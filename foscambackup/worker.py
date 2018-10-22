""" WORKER """
import os
import sys
import logging
import threading

import ftplib
from zipfile import ZipFile
from zipfile import ZIP_LZMA

from foscambackup.download_file_tracker import DownloadFileTracker
from foscambackup.constant import Constant
from foscambackup.progress import Progress
import foscambackup.util.helper as helper
import foscambackup.util.ftp_helper as ftp_helper
import foscambackup.util.file_helper as file_helper

class Worker:
    """ Lists, Downloads, Deletes and Zips files """
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

    def __init__(self, connection, args):
        """ Set and initialize all the variables for later use.
            Note: Hard to test this way, needs rewrite.
        """
        self.connection = connection
        self.progress_objects = []
        self.args = args
        self.conf = args['conf']
        self.folder_actions = {}

        Progress.max_files = args["max_files"]
        if args["output_path"][-1:] == "":
            self.log_debug("Using current dir")
            self.output_path = ""
        else:
            self.output_path = args['output_path']
        if self.output_path != "" and not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

    def check_currently_recording(self):
        """ Read the Sdrec file, which contains the current recording date """
        dir_list = ftp_helper.mlsd(self.connection, helper.slash() + Constant.base_folder)
        for directory, _ in dir_list:
            if directory == Constant.sd_rec:
                absolute_remote_path = helper.slash() + Constant.base_folder + helper.slash() + directory
                retr_command = ftp_helper.create_retrcmd(absolute_remote_path)
                ftp_helper.retr(self.connection, retr_command, self.read_sdrec_content)
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
                "folder": Constant.record_folder, "int_mode": 0, 'separator':'_'}
        mode_snap = {"wanted_files": Constant.wanted_files_snap,
                "folder": Constant.snap_folder, "int_mode": 1, 'separator':'-'}
        if self.args['mode'] != None:
            if self.args['mode'] == Constant.record_folder:
                self.get_footage(mode_record)
            else:
                self.get_footage(mode_snap)
        else:
            self.get_footage(mode_record)
            self.get_footage(mode_snap)
        self.log_info("finished downloading files")

    def load_and_init_from_previous(self, read_file):
        """ Restore from previous file """
        already_processed = []
        content = read_file.readlines()
        for line in content:
            cleaned = helper.clean_newline_char(line)
            progress = Progress(cleaned)
            progress.read_previous_progress_file()
            already_processed.append(progress)
        return already_processed
            
    def read_state_file(self, absolute_dir):
        """ Read from state file """
        try:
            fname = helper.construct_path(absolute_dir, [Constant.state_file])
            return file_helper.open_readonly_file(fname, self.load_and_init_from_previous)
        except FileNotFoundError:
            self.logger.info("No state file found.")

    def get_footage(self, mode):
        """ Get the footage based on the given mode, do some checks. """
        top_folders = ftp_helper.mlsd(
            self.connection, helper.get_abs_path(self.conf, mode))
        # Snapshot folders are also ordered by time periods

        already_processed = self.read_state_file(os.getcwd())

        for pdir, desc in top_folders:
            path_local = mode["folder"] + helper.slash() + pdir
            
            progress = Progress(path_local)
            
            skip = False
            if already_processed != None:
                # add check for unique cur_folder entries? or better clean state.log on reading.
                for prev_progress in already_processed:
                    if prev_progress.done_progress["done"] == 1 and prev_progress.cur_folder == progress.cur_folder:
                        skip = True
                    # take the previous progress to optimize download of files
                    elif prev_progress.cur_folder == progress.cur_folder and prev_progress.done_progress["done"] == 0:
                        progress = prev_progress

            if helper.check_file_type_dir(desc):
                if self.conf.currently_recording:
                    if helper.get_current_date() == pdir or skip:
                        self.log_info(
                            "Skipping current recording folder: " + pdir)
                        continue
                self.log_debug(pdir)
                self.progress_objects.append(progress)
                if progress.check_done_folder() is False:
                    self.init_zip_folder(progress.cur_folder)
                    path = helper.construct_path(
                        helper.get_abs_path(self.conf, mode), [pdir])
                    val = ftp_helper.mlsd(self.connection, path)
                    self.crawl_folder(val, mode, progress, pdir)
                    self.check_folder_done(progress)
                else:
                    self.log_info("skipping folder because already done")

    def crawl_folder(self, file_list, mode, progress, parent, subdir=None):
        """ Find the files to download in their respective directories """
        self.log_debug("Found subdirs: "+ str(file_list))
        for foldername, desc in file_list:
            # do not add the time period folders
            if progress.is_max_files_reached():
                progress.save()
                sys.exit()

            if helper.is_subdir(subdir, foldername):
                continue
    
            abs_path = helper.get_abs_path(self.conf, mode)

            if subdir:
                if desc['type'] == 'file':
                    subdir['path'] = helper.construct_path(abs_path, [parent, subdir['current']])
                else:
                    subdir['path'] = helper.construct_path(abs_path, [parent, foldername])
            else:
                subdir = {"path":'', "subdirs":[foldername]}
                subdir['path'] = helper.construct_path(abs_path, [parent, foldername])

            if helper.check_file_type_dir(desc) and subdir['path'] != "" and helper.check_not_curup(foldername):
                path = subdir['path']
                self.log_info("Querying path: " + path)
                file_list_subdir = ftp_helper.mlsd(self.connection, path)
                if subdir:
                    subdir['subdirs'].append(foldername)
                    subdir['current'] = foldername
                self.crawl_folder(file_list_subdir, mode, progress, parent, subdir)
            else:
                abs_path = helper.construct_path(subdir['path'], [foldername])
                loc_info = {'mode': mode, 'parent_dir': parent, 'abs_path': abs_path,
                            'filename': foldername, 'desc': desc}
                self.crawl_files(loc_info, progress)

    def init_zip_folder(self, key):
        """ Initialize the key for folder with dict object """
        helper.check_valid_folderkey(key)
        self.folder_actions[key] = {"zipped": 0,
                                    "remote_deleted": 0, "local_deleted": 0}

    def zip_local_files_folder(self, folder):
        """ Arg folder is e.g record/01052017 """
        split = folder.split(helper.slash())
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
                        for filex in os.listdir(helper.construct_path(self.output_path, [folder])):
                            self.log_debug("Adding to zip: " + filex)
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
        except ftplib.error_perm:
            self.log_error("No such file or directory! Tried: " + fullpath)
        except ftplib.error_temp:
            self.log_info("Timeout when deleting..")

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
                    except ftplib.error_perm as perm:
                        if "550" in perm.__str__():
                            self.recursive_delete(fullpath, folder)
                    except ftplib.error_temp as timeout:
                        # cause: zipping and local deletion keep the connection idle too long.
                        self.log_debug(timeout.__str__())
                        self.log_info("Timeout so reopening connection right now ..")
                        ftp_helper.close_connection(self.connection)
                        self.connection = ftp_helper.open_connection(self.args['conf'])
                        self.log_info("Reinitate deletion of remote folder.")
                        self.delete_remote_folder(fullpath, folder)
                else:
                    self.log_info("Not deleting remote folder")
                    self.set_remote_deleted(folder)
        except KeyError:
            self.log_error(
                "Folder key was not initialized in zipped folders list!")
            self.delete_remote_folder(fullpath, folder)

    def check_folder_done(self, progress):
        """ Check which folders are marked as done and process them for deletion and/or zipping """
        self.log_debug("Check if folder is done")
        if progress.check_done_folder():
            self.zip_and_delete(progress.cur_folder)
            progress.write_done_folder(progress.cur_folder)

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

        if self.conf.model:
            fullpath = helper.construct_path(self.conf.model, [folder])
            fullpath = helper.construct_path(
                helper.slash() + Constant.base_folder, [fullpath])
            delete_state = {'action_key': 'remote_deleted',
                            'arg_key': 'delete_rm', 'folder': folder, 'fullpath': fullpath}
            self.check_folder_state_delete(delete_state, self.delete_remote_folder)
        else:
            raise ValueError("No model serial value found!")

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

    def crawl_files(self, loc_info, progress):
        """ Check if not already downloaded and valid filename, then download the file to our local path """
        if progress.check_for_previous_progress(loc_info):
            self.log_debug("skipping: " + loc_info['filename'])
            return
        self.log_debug("Called craw files with: " + str(loc_info))
        if helper.check_not_dat_file(loc_info['filename']):
            progress.add_file_init(loc_info['filename'])
            self.retrieve_and_write_file(loc_info, progress)

    def retrieve_and_write_file(self, loc_info, progress):
        """ Perform checks and initialization before downloading file """
        wanted_files = loc_info['mode']['wanted_files']
        m_folder = loc_info['mode']['folder']
        filename = loc_info['filename']
        folderpath = helper.clean_folder_path(
            helper.construct_path(m_folder, [loc_info['parent_dir']]))
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
                    # FIXME only file_wrapper knows for certain if the file is complete.
                    progress.add_file_done(folderpath, filename)

    def download_file(self, loc_info):
        """ Download the file with the wrapper object """
        local_file_path = helper.construct_path(
            self.output_path, [loc_info['folderpath'], loc_info['filename']])
        self.log_debug(local_file_path)
        wrapper = None
        try:
            helper.verify_path(loc_info['abs_path'], loc_info['mode'])
            byte_size = ftp_helper.size(self.connection, loc_info['abs_path'])
            wrapper = DownloadFileTracker(local_file_path, byte_size)
            call = wrapper.write_to_file
            self.log_info("Downloading... " + loc_info['filename'])
            ftp_helper.retr(self.connection, ftp_helper.create_retrcmd(
                loc_info['abs_path']), call)
        except ftplib.error_perm as exc:
            self.log_error("Tried path: " + loc_info['abs_path'])
            self.log_error("Tried path: " +
                           str(list(ftp_helper.mlsd(self.connection, loc_info['abs_path']))))
            self.log_error(loc_info['abs_path'])
            self.log_error("Retrieve and write file: " +
                           loc_info['filename'] + " " + exc.__str__())
        except ValueError as exc:
            self.log_error(loc_info['abs_path'] + " : " + exc.__str__())
        except EOFError:
            self.connection = ftp_helper.open_connection(self.args['conf'])
            wrapper.delete_file()
            self.download_file(loc_info)
        finally:
            if wrapper != None:
                wrapper.close_file()
