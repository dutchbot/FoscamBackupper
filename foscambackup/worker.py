""" WORKER """
import logging
import os
import shutil
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
        self.logger.debug(msg)

    def log_info(self, msg):
        self.logger.info(msg)

    def __init__(self, progress, args):
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
                connection.retrbinary(
                    "RETR " + directory, self.read_sdrec_content)
                break

    def read_sdrec_content(self, file_handle):
        if helper.get_current_date() == file_handle.decode('ascii').split("_")[0]:
            self.log_info(
                "Skipping current date, because currently recording.")
            self.conf.currently_recording = True

    def update_conf(self, conf):
        self.conf = conf

    def open_connection(self, conf):
        self.conf = conf

        connection = FTP()
        connection.set_pasv(False)
        connection.connect(conf.host, conf.port)
        connection.login(conf.username, conf.password)

        self.check_currently_recording(connection)

        return connection

    def close_connection(self, connection):
        connection.close()

    def get_files(self, connection):
        self.get_recorded_footage(connection)
        self.get_snapshot_footage(connection)
        self.log_info("finished downloading files")

    def get_recorded_footage(self, connection):
        mode = {"wanted_files": Constant.wanted_files_record,
                "folder": Constant.record_folder, "int_mode": 0}
        self.progress.current_mode = Constant.record_folder
        self.get_footage(connection, mode)

    def get_snapshot_footage(self, connection):
        mode = {"wanted_files": Constant.wanted_files_snap,
                "folder": Constant.snap_folder, "int_mode": 1}
        self.progress.current_mode = Constant.snap_folder
        self.get_footage(connection, mode)

    def init_zip_folder(self,key):
        self.zipped_folders[key] = { "zipped": 0, "remote_deleted": 0, "local_deleted": 0 }

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
                    folder_path = helper.construct_path(self.output_path, [folder])
                    with ZipFile(path_file, 'w', compression=ZIP_LZMA) as myzip:
                        # scandir would provide more info
                        for filex in os.listdir(path = helper.construct_path(self.output_path, [folder])):
                            self.log_debug(filex)
                            myzip.write(helper.construct_path(folder_path,[filex]), arcname=filex)
                    myzip.close()
                    self.zipped_folders[folder]['zipped'] = 1


    def delete_local_folder(self, path):
        self.log_debug("Deleting local folder..")
        helper.cleanup_directories(self.output_path + path)
        self.zipped_folders[path]["local_deleted"] = 1

    def delete_remote_folder(self, connection, fullpath, folder):
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
                            self.log_info("Recursive strategy")
                            """ Recursive strategy to clean folder """
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
                            helper.set_remote_folder_fullpath(connection, fullpath)
                            connection.rmd(folder)
                            self.zipped_folders[folder]['remote_deleted'] = 1
                else:
                    self.log_info("Not deleting remote folder")
                    self.zipped_folders[folder]['remote_deleted'] = 1
        except KeyError:
            self.init_zip_folder(folder)
            self.delete_remote_folder(connection, fullpath, folder)

    def get_abs_path(self, mode):
        return helper.construct_path("/"+Constant.base_folder,[self.conf.model,mode["folder"]])

    def get_footage(self, connection, mode):
        tmp = connection.mlsd(self.get_abs_path(mode))
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
                    val = connection.mlsd(path=self.get_abs_path(mode))
                    self.crawl_files(val, connection, mode, pdir)
                else:
                    self.log_info("skipping folder")
                self.check_done_folders_zip_and_delete(
                    connection)

    def clean_folder_path(self,folder):
        """ Remove the rounded date_time to find the correct key """
        if "_" in folder: #failsafe
            return folder[:-16] 
        return folder

    def check_done_folders_zip_and_delete(self, connection):
        self.log_debug("called zip and delete")
        done_folders = sorted(self.progress.check_folders_done(), reverse=True)
        self.log_debug(done_folders)
        self.log_debug("Zip_files " + str(self.zip_files))
        self.log_debug(self.zipped_folders)
        for folder in done_folders:
            self.zip_and_delete(connection, folder)

    def zip_and_delete(self, connection, folder):
        folder = self.clean_folder_path(folder)
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
                    path = helper.construct_path(self.get_abs_path(mode),[parent_dir,filename])
                    parent_dir = helper.construct_path(parent_dir,[filename])
                else:
                    path = helper.construct_path(self.get_abs_path(mode),[parent_dir])
                tmp = connection.mlsd(path)
                self.crawl_files(tmp, connection, mode, parent_dir)
            else:
                self.retrieve_and_write_file(
                    connection, parent_dir, filename, desc, mode)

    def retrieve_and_write_file(self, connection, parent_dir, filename, desc, mode):
        wanted_files = mode['wanted_files']
        folder = mode['folder']
        folderpath = self.clean_folder_path(helper.construct_path(folder,[parent_dir]))
        self.init_zip_folder(folderpath)
        if desc['type'] == 'file':
            check = filename.split(".")
            if len(check) > 1:
                check = filename.split(".")[1]
                if check == wanted_files[0] or check == wanted_files[1]:
                    wrapper = FileWrapper()
                    if not os.path.exists(helper.construct_path(self.output_path, [folderpath])):
                        os.makedirs(helper.construct_path(
                            self.output_path, [folderpath]))
                    local_file_path = helper.construct_path(self.output_path, [folderpath, filename])
                    cur_file = open(local_file_path, "w+b")
                    self.log_debug(local_file_path)
                    wrapper.set_cur_file(cur_file)
                    try:
                        file_path = helper.construct_path(self.get_abs_path(mode),[parent_dir,filename])
                        connection.retrbinary(
                            "RETR " + file_path, wrapper.write_to_file)
                        self.log_info("Downloading... " + filename)
                    except error_perm as exc:
                        self.log_debug(file_path)
                        self.log_debug("Retrieve and write file: " +filename + exc.__str__())
                    wrapper.close_file()
                    self.progress.add_file_done(folderpath, filename)
