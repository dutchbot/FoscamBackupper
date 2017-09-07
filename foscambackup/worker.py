""" WORKER """
import os
import logging
import threading

from ftplib import FTP
from ftplib import error_perm
from zipfile import ZipFile
from zipfile import ZIP_LZMA

# own classes
from foscambackup.file_wrapper import FileWrapper
from foscambackup.constant import Constant
import foscambackup.helper as helper


class Worker:
    """ Retrieves files for us """
    # object variables
    logger = logging.getLogger('Worker')
    progress = None
    conf = None
    args = None
    connection = None #

    def log_debug(self, msg):
        """ Log debug msg """
        self.logger.debug(msg)

    def log_info(self, msg):
        """ Log info msg """
        self.logger.info(msg)

    def log_error(self, msg):
        """ Log error msg """
        self.logger.error(msg)

    def __init__(self, progress, args):
        """ Set and initialize all the variables for later use.
            Note: Hard to test this way, needs rewrite.
        """
        self.progress = progress
        self.args = args
        self.zipped_folders = {}
        if args["output_path"][-1:] == "":
            self.log_debug("Using current dir")
            self.output_path = ""
        else:
            self.output_path = args['output_path']
        if self.output_path != "" and not os.path.exists(self.output_path):
            os.makedirs(self.output_path)
        self.progress.set_max_files(args["max_files"])

    def check_currently_recording(self, connection):
        """ Read the Sdrec file, which contains the current recording date """
        dir_list = helper.mlsd(connection, "/")
        for directory, _ in dir_list:
            if directory == ".SdRec":
                connection.retrbinary(helper.create_retr_command(
                    directory), self.read_sdrec_content)
                break

    def read_sdrec_content(self, file_handle):
        """ Read the sdrec file, which indicates the last recording state """
        if helper.get_current_date() == file_handle.decode('ascii').split("_")[0]:
            self.log_info(
                "Skipping current date, because currently recording.")
            self.conf.currently_recording = True

    def update_conf(self, conf):
        """ Update the conf variable """
        self.conf = conf

    def open_connection(self, conf):
        """ Open FTP connection to server with conf information """
        self.conf = conf

        connection = FTP()
        connection.set_pasv(False)
        connection.connect(conf.host, conf.port)
        connection.login(conf.username, conf.password)

        self.check_currently_recording(connection)
        self.connection = connection

        return connection

    def get_files(self, connection):
        """ Get the files for both recorded an snapshot footage """
        self.connection = connection
        self.get_recorded_footage(connection)
        self.get_snapshot_footage(connection)
        self.check_done_folders(connection)
        self.log_info("finished downloading files")

    def get_recorded_footage(self, connection):
        """ Get the recorded (avi) footage """
        mode = {"wanted_files": Constant.wanted_files_record,
                "folder": Constant.record_folder, "int_mode": 0}
        self.progress.current_mode = Constant.record_folder
        self.get_footage(connection, mode)

    def get_snapshot_footage(self, connection):
        """ Get the snapshot (jpeg) footage """
        mode = {"wanted_files": Constant.wanted_files_snap,
                "folder": Constant.snap_folder, "int_mode": 1}
        self.progress.current_mode = Constant.snap_folder
        self.get_footage(connection, mode)

    def init_zip_folder(self, key):
        """ Initialize the key for folder with dict object """
        self.zipped_folders[key] = {"zipped": 0,
                                    "remote_deleted": 0, "local_deleted": 0}

    def zip_local_files_folder(self, folder):
        """ Arg folder is e.g record/01052017 """
        split = folder.split("/")
        output = split[0]
        if os.path.exists(helper.construct_path(self.output_path, [output])):
            if os.path.exists(helper.construct_path(self.output_path, [folder])):
                path_file = helper.construct_path(
                    self.output_path, [folder]) + '.zip'
                if not os.path.isfile(path_file):
                    self.log_info("Creating zip file at: " +
                                  path_file)
                    folder_path = helper.construct_path(
                        self.output_path, [folder])
                    with ZipFile(path_file, 'w', compression=ZIP_LZMA) as myzip:
                        # scandir would provide more info
                        for filex in os.listdir(path=helper.construct_path(self.output_path, [folder])):
                            self.log_debug(filex)
                            myzip.write(helper.construct_path(
                                folder_path, [filex]), arcname=filex)
                    myzip.close()
                    self.zipped_folders[folder]['zipped'] = 1

    def delete_local_folder(self, fullpath, folder):
        """ Delete the folder with the downloaded contents, should only be used when zipping is activated. """
        self.log_debug("Deleting local folder.. " + fullpath)
        helper.cleanup_directories(fullpath)
        self.zipped_folders[folder]["local_deleted"] = 1

    def delete_remote_folder(self, fullpath, folder):
        """ Used to delete the remote folder, also deletes recursively """
        connection = self.connection
        try:
            if self.zipped_folders[folder]['remote_deleted'] == 0 and self.args['delete_rm']:
                if not self.args['dry_run']:
                    try:
                        self.log_info("Deleting remote folder..")
                        self.log_info(fullpath)
                        connection.rmd(fullpath)
                        self.zipped_folders[folder]['remote_deleted'] = 1
                    except error_perm as perm:
                        # if "No such file or directory" in perm.__str__():
                        #     self.log_error("Fullpath: " + fullpath + ", Folder: " + folder)
                        #     self.log_error("Current remote dir: " + str(list(connection.mlsd())))
                        #     self.log_error("Folder does not exist remotely!" + perm.__str__())
                        if "550" in perm.__str__():
                            self.log_info("Recursive strategy to clean folder")
                            dir_list = helper.mlsd(connection, fullpath)
                            for dirt, _ in dir_list:
                                sub_path = helper.construct_path(fullpath, [dirt])
                                file_list = helper.mlsd(connection, sub_path)
                                for filename, desc in file_list:
                                    if desc['type'] != "dir":
                                        if filename != "." and filename != "..":
                                            file_path = helper.construct_path(sub_path, [filename])
                                            connection.delete(file_path)
                                if dirt != "." and dirt != "..":
                                    self.log_debug("Removing subdir: " + dirt)
                                    connection.rmd(sub_path)
                            self.log_debug("Deleting top folder")
                            connection.rmd(fullpath)
                            self.zipped_folders[folder]['remote_deleted'] = 1
                else:
                    self.log_info("Not deleting remote folder")
                    self.zipped_folders[folder]['remote_deleted'] = 1
        except KeyError:
            self.log_error(
                "Folder key was not initialized in zipped folders list!")
            self.init_zip_folder(folder)
            self.delete_remote_folder(fullpath, folder)

    def get_footage(self, connection, mode):
        """ Get the footage based on the given mode, do some checks. """
        top_folders = helper.mlsd(connection, helper.get_abs_path(self.conf, mode))
        # Snapshot folders are also ordered by time periods
        for pdir, desc in top_folders:
            if helper.check_file_type_dir(desc):
                if self.conf.currently_recording:
                    if helper.get_current_date() == pdir:
                        self.log_info(
                            "Skipping current recording folder: " + pdir)
                        continue
                self.log_debug(pdir)
                if self.progress.check_done_folder(mode["folder"], pdir) is False:
                    self.progress.set_cur_folder(pdir)
                    self.progress.set_cur_mode(mode)
                    path = helper.construct_path(helper.get_abs_path(self.conf, mode), [pdir])
                    val = helper.mlsd(connection, path)
                    self.crawl_folder(val, connection, mode, pdir)
                else:
                    self.log_info("skipping folder")

    def check_done_folders(self, connection):
        """ Check which folders are marked as done and process them for deletion and/or zipping """
        self.log_debug("called zip and delete")
        done_folders = sorted(self.progress.check_folders_done(), reverse=True)
        self.log_debug(done_folders)
        self.log_debug(self.zipped_folders)
        count = 0
        for folder in done_folders:
            count+=1
            self.log_debug(count)
            self.init_zip_folder(folder)
            self.zip_and_delete(connection, folder)

    def zip_and_delete(self, connection, folder):
        """ Function that does multiple checks for zipping and deleting """
        folder = helper.clean_folder_path(folder)
        if self.zipped_folders[folder]['zipped'] == 0 and self.args['zip_files']:
            thread = threading.Thread(target=self.zip_local_files_folder,
                                      args=(folder, ))
            thread.start()
            thread.join()

        fullpath = helper.construct_path(self.output_path, [folder])
        self.check_folder_state_delete("local_deleted","delete_local_f",folder, fullpath, self.delete_local_folder)
        fullpath = helper.construct_path(self.conf.model, [folder])
        fullpath = helper.construct_path("/"+Constant.base_folder,[fullpath])
        self.check_folder_state_delete("remote_deleted","delete_rm",folder, fullpath, self.delete_remote_folder)

    def check_folder_state_delete(self, zip_key, arg_key, folder, fullpath, callback):
        if self.zipped_folders[folder][zip_key] == 0 and self.args[arg_key]:
            if not self.args['dry_run']:
                callback(fullpath, folder)
            else:
                self.zipped_folders[folder][zip_key] = 1
                self.log_debug("Deleted "+zip_key+": " + folder)

    def crawl_folder(self, file_list, connection, mode, parent, path = ""):
        """ Find the files to download in their respective directories """
        for foldername, desc in file_list:
            # do not add the time period folders
            if self.progress.check_for_previous_progress(mode["folder"], parent, foldername):
                self.log_debug("skipping: " + foldername)
                continue
            if self.progress.is_max_files_reached() is True:
                self.progress.save_progress_exit()
            if path == "":
                path = helper.construct_path(helper.get_abs_path(self.conf, mode), [parent,foldername])
            # difference between simulated ftp server and real one is listing of '.' and '..'
            if desc['type'] == 'dir' and path != "" and helper.check_not_curup(foldername): # second time this should be false
                self.log_debug("Querying path: " + path)
                file_list_subdir = helper.mlsd(connection, path)
                self.crawl_folder(file_list_subdir,connection,mode,parent, path)
            else:
                abs_path = helper.construct_path(path,[foldername])
                loc_info = {'mode': mode, 'parent_dir': parent, 'abs_path': abs_path,
                    'filename': foldername, 'desc': desc}
                self.crawl_files(connection, loc_info)

    def crawl_files(self, connection, loc_info):
        """ Process the actual files """
        if helper.check_not_dat_file(loc_info['filename']):
            self.progress.add_file_init(helper.construct_path(
            loc_info['mode']["folder"], [loc_info['parent_dir']]), loc_info['filename'])
            self.retrieve_and_write_file(connection, loc_info)

    def retrieve_and_write_file(self, connection, loc_info):
        """ Perform checks and initialization before downloading file """
        wanted_files = loc_info['mode']['wanted_files']
        m_folder = loc_info['mode']['folder']
        filename = loc_info['filename']
        folderpath = helper.clean_folder_path(
            helper.construct_path(m_folder, [loc_info['parent_dir']]))
        self.init_zip_folder(folderpath)
        if loc_info['desc']['type'] == 'file':
            check = filename.split(".")
            if len(check) > 1:
                check = filename.split(".")[1]
                if check == wanted_files[0] or check == wanted_files[1]:
                    path = helper.construct_path(self.output_path, [folderpath])
                    if not os.path.exists(path):
                        self.log_info("create structure" +path)
                        os.makedirs(path)
                    loc_info['folderpath'] = folderpath
                    self.download_file(connection, loc_info)
                    self.progress.add_file_done(folderpath, filename)

    def download_file(self, connection, loc_info):
        """ Download the file with the wrapper object """
        local_file_path = helper.construct_path(
            self.output_path, [loc_info['folderpath'], loc_info['filename']])
        self.log_debug(local_file_path)
        wrapper = None
        try:
            wrapper = FileWrapper(local_file_path)
            connection.retrbinary(helper.create_retr_command(loc_info['abs_path']), wrapper.write_to_file)
            self.log_info("Downloading... " + loc_info['filename'])
        except error_perm as exc:
            # #self.log_error("Current remote dir: " +
            #                str(list(connection.mlsd("."))))
            self.log_error("Tried path: " + loc_info['abs_path'])
            self.log_error("Tried path: " +
                           str(list(helper.mlsd(connection, loc_info['abs_path']))))
            self.log_error(loc_info['abs_path'])
            self.log_error("Retrieve and write file: " +
                           loc_info['filename'] + " " + exc.__str__())
        finally:
            if wrapper != None:
                wrapper.close_file()
