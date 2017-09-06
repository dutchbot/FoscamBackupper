""" Track progress of downloading etc """
import json
import sys
import os.path
import logging

from foscambackup.constant import Constant
import foscambackup.helper as helper

class Progress:
    """ Track progress """
    logger = logging.getLogger('Worker')
    max_files = -1
    done_files = 1
    done_folders = []
    done_progress = {}
    cur_mode = None # used for saving progress
    cur_folder = ""  # used for saving progress
    absolute_dir = ""

    def __init__(self):
        self.absolute_dir = os.getcwd()

        self.write_previous_state_file()
        self.write_state_file()

    def write_previous_state_file(self):
        """ Write previous progress to file """
        previous = self.absolute_dir + "/" + Constant.previous_state
        if os.path.isfile(previous):
            try:
                cur_file = open(previous, "r")
                with open(previous) as foldername:
                    progress_folder = json.load(foldername)
                    # don't slice here /n already removed
                    self.initialize_done_progress(foldername, progress_folder)
            finally:
                foldername.close()
                cur_file.close()

    def write_state_file(self):
        """ Write to state file """
        fname = self.absolute_dir + "/" + Constant.state_file
        if os.path.isfile(fname):
            try:
                cur_file = open(fname, "r")
                with open(fname) as filename:
                    content = filename.readlines()
                    for line in content:
                        cleaned = helper.clean_newline_char(line)
                        self.initialize_done_progress(cleaned, {"done": 1, "path": cleaned})
                        self.done_folders.append(cleaned)
            finally:
                filename.close()
                cur_file.close()

    # getters/setters
    def set_max_files(self, max_files):
        """ setter """
        self.max_files = max_files

    def set_current_mode(self, cur_mode):
        """ setter """
        self.cur_mode = cur_mode

    def set_cur_folder(self, cur_folder):
        """ setter """
        self.cur_folder = cur_folder

    def get_cur_folder(self):
        """ getter """
        return self.cur_folder

    # end

    def check_for_previous_progress(self, prefix, folder, filename):
        """ Check previous progress key """
        try:
            if self.done_progress[prefix + "/" + folder][filename] == 1:
                return True
            return False
        except KeyError:
            return False

    def check_done_folder(self, mode, foldername):
        """ Check if folder was already done """
        self.logger.debug("Mode " + mode + " " + foldername)
        # check all the files for 1 value
        for folder in self.done_folders:
            if folder == (mode + "/" + foldername):
                return True
        return False

    def is_max_files_reached(self):
        """ Check max files """
        if self.max_files != -1:
            return self.max_files <= self.done_files
        return False

    def add_file_init(self, combined, filename):
        """ Add file to init key """
        try:
            if combined != '':
                self.done_progress[combined][filename] = 0
        except KeyError:
            self.logger.warning("Key error init " + combined)
            self.initialize_done_progress(combined)
            self.done_progress[combined][filename] = 0

    def add_file_done(self, folder, filename):
        """ Add file to done list """
        self.logger.info("Adding file to DONE " + filename)
        try:
            self.done_files += 1
            self.done_progress[folder][filename] = 1
        except KeyError:
            try:
                self.initialize_done_progress(folder)
                self.done_progress[folder][filename] = 1
            except KeyError as ex:
                self.logger.warning("Key error file_done: " + ex.__str__())
                self.logger.debug(self.done_progress)

    def initialize_done_progress(self, folder, old=None):
        """  Initialize key for a folder in our dict structure """
        if folder != '':
            if old != None:
                self.done_progress[folder] = old
            else:
                self.done_progress[folder] = {"done": 0, "path": folder}

    def check_folders_done(self):
        """ Check which folders are already complete """
        complete_folders = []
        for folder_name, folder in self.done_progress.items():
            if folder["done"] != 1:
                self.logger.debug("folder not done yet")
                number_of_files = len(folder.keys()) - 2
                actual_done = 0
                for key, value in folder.items():
                    if key != "done" and key != "path" and value == 1:
                        actual_done += 1
                self.logger.debug(folder)
                self.logger.debug(
                    "Files: " + str(number_of_files) + " Actual: " + str(actual_done))
                if number_of_files == actual_done:
                    cur_file = open(self.absolute_dir + "/" + Constant.state_file, "a")
                    enc = folder["path"] + "\n"
                    cur_file.write(enc)
                    complete_folders.append(folder["path"])
                    if folder_name != '': # dont know why this could happen
                        self.done_progress[folder_name]["done"] = 1
                    cur_file.close()
            else:
                complete_folders.append(folder["path"])
        return complete_folders

    def save_progress_exit(self):
        """ Save progress """
        if self.get_cur_folder() != '':
            self.logger.debug("Saving progress..")
            self.save_progress_for_unfinished(
                self.cur_mode + "/" + self.get_cur_folder())
        sys.exit()

    # save the progress of the last folder
    def save_progress_for_unfinished(self, folder):
        """ Save the progress for unfinished task """
        try:
            self.logger.debug(self.done_folders)
            for directory in self.done_folders:
                if directory == folder:
                    return
            last_file = self.done_progress[folder]
            cur_file = open(self.absolute_dir + Constant.previous_state, "w")
            enc = json.dumps(last_file)
            cur_file.write(enc)
        except KeyError:
            self.logger.warning("Key: " + folder)
            self.logger.warning("Key error in save_progress_for_unfinished")
            self.logger.warning(self.done_progress)
