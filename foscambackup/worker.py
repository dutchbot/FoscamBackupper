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
        self.log_debug(isinstance(args.__class__, type(None)))
        self.zipped_folders = {}
        self.zip_files = args["zip_files"]
        if args["output_path"][-1:] == "":
            self.log_debug("Using current dir")
            self.output_path = ""
        else:
            self.output_path = args['output_path']
        if self.output_path != "" and not os.path.exists(self.output_path):
            os.mkdir(self.output_path)
        self.delete_rm = args["delete_rm"]
        self.log_debug(args['max_files'])
        self.progress.set_max_files(args["max_files"])
        self.verbose = args["verbose"]
        self.dry_run = args["dry_run"]
        self.delete_local_f = args["delete_local_f"]

    def check_currently_recording(self, connection):
        """ Read the Sdrec file, which contains the current recording date """
        base = helper.select_folder()
        connection.sendcmd(base)
        dir_list = connection.mlsd("/")
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

        return connection

    def get_files(self, connection):
        """ Get the files for both recorded an snapshot footage """
        self.get_recorded_footage(connection)
        self.get_snapshot_footage(connection)
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

    def delete_local_folder(self, path):
        """ Delete the folder with the downloaded contents, should only be used when zipping is activated. """
        self.log_debug("Deleting local folder..")
        helper.cleanup_directories(self.output_path + path)
        self.zipped_folders[path]["local_deleted"] = 1

    def delete_remote_folder(self, connection, fullpath, folder):
        """ Used to delete the remote folder, also deletes recursively """
        self.log_info("remote delete")
        try:
            if self.zipped_folders[folder]['remote_deleted'] == 0 and self.delete_rm:
                if not self.dry_run:
                    try:
                        self.log_info("Deleting remote folder..")
                        helper.set_remote_folder_fullpath(connection, fullpath)
                        connection.rmd(folder)
                        self.zipped_folders[folder]['remote_deleted'] = 1
                    except error_perm as perm:
                        if "No such file or directory" in perm.__str__():
                            self.logger.error(
                                "Folder does not exist remotely, perhaps previously deleted?")
                        elif "550" in perm.__str__():
                            self.log_info("Recursive strategy to clean folder")
                            helper.set_remote_folder_fullpath(
                                connection, helper.construct_path(fullpath, [folder]))
                            dir_list = connection.mlsd()
                            for dirt, _ in dir_list:
                                helper.set_remote_folder_fullpath(
                                    connection, helper.construct_path(fullpath, [folder, dirt]))
                                file_list = connection.mlsd()
                                for file, desc in file_list:
                                    if desc['type'] != "dir":
                                        if file != "." and file != "..":
                                            connection.delete(file)
                                if dirt != "." and dirt != "..":
                                    helper.set_remote_folder_fullpath(
                                        connection, helper.construct_path(fullpath, [folder]))
                                    self.log_debug("Removing subdir: " + dirt)
                                    connection.rmd(dirt)
                            self.log_debug("Deleting top folder")
                            helper.set_remote_folder_fullpath(
                                connection, fullpath)
                            connection.rmd(folder)
                            self.zipped_folders[folder]['remote_deleted'] = 1
                else:
                    self.log_info("Not deleting remote folder")
                    self.zipped_folders[folder]['remote_deleted'] = 1
        except KeyError:
            self.log_error(
                "Folder key was not initialized in zipped folders list!")
            self.init_zip_folder(folder)
            self.delete_remote_folder(connection, fullpath, folder)

    def get_footage(self, connection, mode):
        """ Get the footage based on the given mode, do some checks. """
        tmp = connection.mlsd(helper.get_abs_path(self.conf, mode))
        # Snapshot folders are also ordered by time periods
        for pdir, desc in tmp:
            if helper.check_file_type_dir(desc):
                if self.conf.currently_recording:
                    if helper.get_current_date() == pdir:
                        self.log_info(
                            "Skipping current recording folder: " + pdir)
                        continue
                self.log_debug(pdir)
                if self.progress.check_done_folder(mode["folder"], pdir) is False:
                    self.progress.set_cur_folder(pdir)
                    val = connection.mlsd(
                        path=helper.get_abs_path(self.conf, mode))
                    self.crawl_files(val, connection, mode, pdir)
                else:
                    self.log_info("skipping folder")
                self.check_done_folders(connection)

    def check_done_folders(self, connection):
        """ Check which folders are marked as done and process them for deletion and/or zipping """
        self.log_debug("called zip and delete")
        done_folders = sorted(self.progress.check_folders_done(), reverse=True)
        self.log_debug(done_folders)
        self.log_debug("Zip_files " + str(self.zip_files))
        self.log_debug(self.zipped_folders)
        for folder in done_folders:
            self.zip_and_delete(connection, folder)

    def zip_and_delete(self, connection, folder):
        """ Function that does multiple checks for zipping and deleting """
        folder = helper.clean_folder_path(folder)
        if self.zipped_folders[folder]['zipped'] == 0 and self.zip_files:
            thread = threading.Thread(target=self.zip_local_files_folder,
                                      args=(folder, ))
            thread.start()
            thread.join()

        if self.delete_local_f and self.zipped_folders[folder]["local_deleted"] == 0:
            if not self.dry_run:
                self.delete_local_folder(folder)
            else:
                self.zipped_folders[folder]["local_deleted"] = 1
                self.log_info("Deleted local: " + folder)

        if self.zipped_folders[folder]['remote_deleted'] == 0 and self.delete_rm:
            if not self.dry_run:
                fullpath = helper.select_folder(
                    [self.conf.model, folder])
                self.delete_remote_folder(
                    connection, fullpath, folder)
            else:
                self.zipped_folders[folder]['remote_deleted'] = 1
                self.log_debug("Deleted: " + folder)

    def crawl_files(self, file_list, connection, mode, parent_dir=""):
        """ Find the files to download in their respective directories """
        for filename, desc in file_list:
            # do not add the time period folders
            if not helper.check_file_type_dir(desc) and helper.check_dat_file(filename) and helper.check_not_curup_dir(filename):
                if self.progress.check_for_previous_progress(mode["folder"], parent_dir, filename):
                    self.log_debug("skipping: " + filename)
                    continue
                if self.progress.is_max_files_reached() is True:
                    self.progress.save_progress_exit()
                self.progress.add_file_init(helper.construct_path(
                    mode["folder"], [parent_dir]), filename)
            if desc['type'] == 'dir':
                if filename != parent_dir:
                    path = helper.construct_path(helper.get_abs_path(
                        self.conf, mode), [parent_dir, filename])
                    parent_dir = helper.construct_path(parent_dir, [filename])
                else:
                    path = helper.construct_path(
                        helper.get_abs_path(self.conf, mode), [parent_dir])
                tmp = connection.mlsd(path)
                self.crawl_files(tmp, connection, mode, parent_dir)
            else:
                # location information
                loc_info = {'mode': mode, 'parent_dir': parent_dir,
                            'filename': filename, 'desc': desc}
                self.retrieve_and_write_file(
                    connection, loc_info)

    def retrieve_and_write_file(self, connection, loc_info):
        """ Perform checks and initialization before downloading file """
        wanted_files = loc_info['mode']['wanted_files']
        folder = loc_info['mode']['folder']
        filename = loc_info['filename']
        folderpath = helper.clean_folder_path(
            helper.construct_path(folder, [loc_info['parent_dir']]))
        self.init_zip_folder(folderpath)
        if loc_info['desc']['type'] == 'file':
            check = filename.split(".")
            if len(check) > 1:
                check = filename.split(".")[1]
                if check == wanted_files[0] or check == wanted_files[1]:
                    if not os.path.exists(helper.construct_path(self.output_path, [folderpath])):
                        os.makedirs(helper.construct_path(
                            self.output_path, [folderpath]))
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
            file_path = helper.construct_path(helper.get_abs_path(
                self.conf, loc_info['mode']), [loc_info['parent_dir'], loc_info['filename']])
            connection.retrbinary(helper.create_retr_command(
                file_path), wrapper.write_to_file)
            self.log_info("Downloading... " + loc_info['filename'])
        except error_perm as exc:
            path_loc_file = helper.construct_path(helper.get_abs_path(
                self.conf, loc_info['mode']), [loc_info['parent_dir']])
            self.log_error("Current remote dir: " +
                           str(list(connection.mlsd())))
            self.log_error("Tried path: " + path_loc_file)
            self.log_error("Tried path: " +
                           str(list(connection.mlsd(path_loc_file))))
            self.log_error(file_path)
            self.log_error("Retrieve and write file: " +
                           loc_info['filename'] + " " + exc.__str__())
        finally:
            if wrapper != None:
                wrapper.close_file()
