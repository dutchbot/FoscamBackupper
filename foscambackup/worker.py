""" WORKER """
import os
import sys
import logging
import threading

from ftplib import error_perm
from zipfile import ZipFile
from zipfile import ZIP_LZMA

# own classes
from foscambackup.file_wrapper import FileWrapper
from foscambackup.constant import Constant
import foscambackup.helper as helper
import foscambackup.ftp_helper as ftp_helper


class Worker:
    """ Retrieves files for us """
    # static variable
    logger = logging.getLogger('Worker')

    def log_debug(self, msg):
        """ Log debug msg """
        self.logger.debug(msg)

    def log_info(self, msg):
        """ Log info msg """
        self.logger.info(msg)

    def log_error(self, msg):
        """ Log error msg """
        self.logger.error(msg)

    def __init__(self, connection, progress, args):
        """ Set and initialize all the variables for later use.
            Note: Hard to test this way, needs rewrite.
        """
        self.connection = connection
        self.progress = progress
        self.args = args
        self.conf = args['conf']
        self.folder_actions = {}
        self.progress.max_files = args["max_files"]
        if args["output_path"][-1:] == "":
            self.log_debug("Using current dir")
            self.output_path = ""
        else:
            self.output_path = args['output_path']
        if self.output_path != "" and not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

    def check_currently_recording(self):
        """ Read the Sdrec file, which contains the current recording date """
        dir_list = ftp_helper.mlsd(self.connection, helper.sl())
        for directory, _ in dir_list:
            if directory == Constant.sd_rec:
                ftp_helper.retr(self.connection, ftp_helper.create_retr(directory), self.read_sdrec_content)
                break

    def read_sdrec_content(self, file_handle):
        """ Read the sdrec file, which indicates the last recording state """
        if helper.get_current_date() == file_handle.decode('ascii').split("_")[0]:
            self.log_info(
                "Skipping current date, because currently recording.")
            self.conf.currently_recording = True
        else:
            self.conf.currently_recording = False

    def update_conf(self, conf):
        """ Update the conf variable """
        self.conf = conf

    def get_files(self):
        """ Get the files for both recorded an snapshot footage """
        self.check_currently_recording()
        mode_record = {"wanted_files": Constant.wanted_files_record,
                "folder": Constant.record_folder, "int_mode": 0}
        mode_snap = {"wanted_files": Constant.wanted_files_snap,
                "folder": Constant.snap_folder, "int_mode": 1}
        if self.args['mode'] != None:
            if self.args['mode'] == Constant.record_folder:
                self.get_footage(mode_record)
            else:
                self.get_footage(mode_snap)
        else:
            self.get_footage(mode_record)
            self.get_footage(mode_snap)
        self.check_done_folders()
        self.log_info("finished downloading files")

    def get_footage(self, mode):
        """ Get the footage based on the given mode, do some checks. """
        top_folders = ftp_helper.mlsd(
            self.connection, helper.get_abs_path(self.conf, mode))
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
                    self.progress.cur_folder = mode["folder"] + \
                        helper.sl() + pdir
                    path = helper.construct_path(
                        helper.get_abs_path(self.conf, mode), [pdir])
                    val = ftp_helper.mlsd(self.connection, path)
                    self.crawl_folder(val, mode, pdir)
                else:
                    self.log_info("skipping folder because already done")

    def crawl_folder(self, file_list, mode, parent, subdir=None):
        """ Find the files to download in their respective directories """
        self.log_debug("Found subdirs: "+ str(file_list))
        for foldername, desc in file_list:
            # do not add the time period folders
            if self.progress.check_for_previous_progress(mode["folder"], parent, foldername):
                self.log_debug("skipping: " + foldername)
                continue
            if self.progress.is_max_files_reached() is True:
                self.progress.save_progress()
                sys.exit()

            if helper.not_check_subdir(subdir,foldername) == False:
                continue
            if subdir:
                subdir['path'] = helper.construct_path(helper.get_abs_path(self.conf, mode), [parent, foldername])
            else:
                subdir = {"path":'', "subdirs":[foldername]}
                subdir['path'] = helper.construct_path(helper.get_abs_path(
                    self.conf, mode), [parent, foldername])
            if helper.check_file_type_dir(desc) and subdir['path'] != "" and helper.check_not_curup(foldername):
                path = subdir['path']
                self.log_debug("Querying path: " + path)
                file_list_subdir = ftp_helper.mlsd(self.connection, path)
                if subdir:
                    subdir['subdirs'].append(foldername)
                self.crawl_folder(file_list_subdir, mode, parent, subdir)
            else:
                abs_path = helper.construct_path(subdir['path'], [foldername])
                loc_info = {'mode': mode, 'parent_dir': parent, 'abs_path': abs_path,
                            'filename': foldername, 'desc': desc}
                self.crawl_files(loc_info)

    def init_zip_folder(self, key):
        """ Initialize the key for folder with dict object """
        helper.check_valid_folderkey(key)
        self.folder_actions[key] = {"zipped": 0,
                                    "remote_deleted": 0, "local_deleted": 0}

    def zip_local_files_folder(self, folder):
        """ Arg folder is e.g record/01052017 """
        split = folder.split(helper.sl())
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
                        for filex in os.listdir(helper.construct_path(self.output_path, [folder])):
                            self.log_debug(filex)
                            myzip.write(helper.construct_path(
                                folder_path, [filex]), arcname=filex)
                    myzip.close()
                    self.folder_actions[folder]['zipped'] = 1

    def delete_local_folder(self, fullpath, folder):
        """ Delete the folder with the downloaded contents.
            Should only be used when zipping is activated.
        """
        self.log_debug("Deleting local folder.. " + fullpath)
        helper.cleanup_directories(fullpath)
        self.folder_actions[folder]["local_deleted"] = 1

    def set_remote_deleted(self, folder):
        """ Mark folder as deleted """
        self.folder_actions[folder]['remote_deleted'] = 1

    def get_remote_deleted(self, folder):
        """ Return remote deleted value """
        return self.folder_actions[folder]['remote_deleted']

    def recursive_delete(self, fullpath, folder):
        """ Deletes the remote folder recursively """
        try:
            self.log_info("Recursive strategy to clean folder")
            dir_list = ftp_helper.mlsd(self.connection, fullpath)
            for dirt, _ in dir_list:
                sub_path = helper.construct_path(fullpath, [dirt])
                file_list = ftp_helper.mlsd(self.connection, sub_path)
                for filename, desc in file_list:
                    if desc['type'] != "dir":
                        if filename != "." and filename != "..":
                            file_path = helper.construct_path(
                                sub_path, [filename])
                            self.connection.delete(file_path)
                if dirt != "." and dirt != "..":
                    self.log_debug("Removing subdir: " + dirt)
                    self.connection.rmd(sub_path)
            self.log_debug("Deleting top folder")
            self.connection.rmd(fullpath)
            self.set_remote_deleted(folder)
        except error_perm:
            self.log_error("No such file or directory! Tried: " + fullpath)

    def delete_remote_folder(self, fullpath, folder):
        """ Used to delete the remote folder, also deletes recursively """
        try:
            if self.get_remote_deleted(folder) == 0 and self.args['delete_rm']:
                if not self.args['dry_run']:
                    try:
                        self.log_info("Deleting remote folder..")
                        self.log_info(fullpath)
                        self.connection.rmd(fullpath)
                        self.set_remote_deleted(folder)
                    except error_perm as perm:
                        if "550" in perm.__str__():
                            self.recursive_delete(fullpath, folder)
                else:
                    self.log_info("Not deleting remote folder")
                    self.set_remote_deleted(folder)
        except KeyError:
            self.log_error(
                "Folder key was not initialized in zipped folders list!")
            self.init_zip_folder(folder)
            self.delete_remote_folder(fullpath, folder)

    def check_done_folders(self):
        """ Check which folders are marked as done and process them for deletion and/or zipping """
        self.log_debug("Check done folders")
        done_folders = sorted(self.progress.check_folders_done(), reverse=True)
        self.log_debug(done_folders)
        self.log_debug(self.folder_actions)
        count = 0
        for folder in done_folders:
            count += 1
            self.log_debug(count)
            self.init_zip_folder(folder)
            self.zip_and_delete(folder)

    def zip_and_delete(self, folder):
        """ Function that does multiple checks for zipping and deleting """
        folder = helper.clean_folder_path(folder)
        if self.folder_actions[folder]['zipped'] == 0 and self.args['zip_files']:
            thread = threading.Thread(target=self.zip_local_files_folder,
                                      args=(folder, ))
            thread.start()
            thread.join()

        fullpath = helper.construct_path(self.output_path, [folder])
        delete_state = {'action_key': 'local_deleted',
                        'arg_key': 'delete_local_f', 'folder': folder, 'fullpath': fullpath}
        self.check_folder_state_delete(delete_state, self.delete_local_folder)
        fullpath = helper.construct_path(self.conf.model, [folder])
        fullpath = helper.construct_path(
            helper.sl() + Constant.base_folder, [fullpath])
        delete_state = {'action_key': 'remote_deleted',
                        'arg_key': 'delete_rm', 'folder': folder, 'fullpath': fullpath}
        self.check_folder_state_delete(delete_state, self.delete_remote_folder)

    def check_folder_state_delete(self, delete_state, callback):
        """ Remote and local deletion of folder """
        folder = delete_state['folder']
        action_key = delete_state['action_key']
        arg_key = delete_state['arg_key']
        fullpath = delete_state['fullpath']
        if self.folder_actions[folder][action_key] == 0 and self.args[arg_key]:
            if not self.args['dry_run']:
                callback(fullpath, folder)
            else:
                self.folder_actions[folder][action_key] = 1
                self.log_debug("Deleted " + action_key + ": " + folder)

    def crawl_files(self, loc_info):
        self.log_debug("Called craw files with: " + str(loc_info))
        """ Process the actual files """
        if helper.check_not_dat_file(loc_info['filename']):
            self.progress.add_file_init(helper.construct_path(
                loc_info['mode']["folder"], [loc_info['parent_dir']]), loc_info['filename'])
            self.retrieve_and_write_file(loc_info)

    def retrieve_and_write_file(self, loc_info):
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
                    path = helper.construct_path(
                        self.output_path, [folderpath])
                    if not os.path.exists(path):
                        self.log_info("create structure" + path)
                        os.makedirs(path)
                    loc_info['folderpath'] = folderpath
                    self.download_file(loc_info)
                    self.progress.add_file_done(folderpath, filename)

    def download_file(self, loc_info):
        """ Download the file with the wrapper object """
        local_file_path = helper.construct_path(
            self.output_path, [loc_info['folderpath'], loc_info['filename']])
        self.log_debug(local_file_path)
        wrapper = None
        try:
            wrapper = FileWrapper(local_file_path)
            call = wrapper.write_to_file
            ftp_helper.retr(self.connection, ftp_helper.create_retr(
                loc_info['abs_path']), call)
            self.log_info("Downloading... " + loc_info['filename'])
        except error_perm as exc:
            # #self.log_error("Current remote dir: " +
            #                str(list(connection.mlsd("."))))
            self.log_error("Tried path: " + loc_info['abs_path'])
            self.log_error("Tried path: " +
                           str(list(ftp_helper.mlsd(self.connection, loc_info['abs_path']))))
            self.log_error(loc_info['abs_path'])
            self.log_error("Retrieve and write file: " +
                           loc_info['filename'] + " " + exc.__str__())
        finally:
            if wrapper != None:
                wrapper.close_file()
