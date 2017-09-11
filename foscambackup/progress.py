""" Track progress of downloading etc """
import json
import logging

from foscambackup.constant import Constant
import foscambackup.helper as helper
import foscambackup.file_helper as file_helper

class Progress:
    """ Track progress """
    logger = logging.getLogger('Worker')

    def __init__(self, test=False):
        self.max_files = -1
        self.done_files = 0
        self.done_folders = []
        self.done_progress = {}
        self.cur_folder = None
        self.absolute_dir = helper.get_cwd()
        self.complete_folders = []

        if not test:
            self.read_previous_state_file()
            self.read_state_file()

    def load_and_init(self, read_file):
        """ Read the dict from file and parse with JSON module """
        progress_folder = json.load(read_file)
        self.initialize_done_progress(progress_folder['path'], progress_folder)

    def read_previous_state_file(self):
        """ Read previous progress from file """
        try:
            previous = self.absolute_dir + helper.sl() + Constant.previous_state
            file_helper.open_readonly_file(previous, self.load_and_init)
        except FileNotFoundError:
            self.logger.info("No previous unfinished result found.")

    def load_and_init_done_folders(self, read_file):
        """ Restore from previous file """
        content = read_file.readlines()
        for line in content:
            cleaned = helper.clean_newline_char(line)
            done = self.init_empty(cleaned)
            done['done'] = 1
            self.initialize_done_progress(cleaned, done)
            self.done_folders.append(cleaned)

    # opens file line cleans it, writes initialize, appends to done_folders
    def read_state_file(self):
        """ Read from state file """
        try:
            fname = helper.construct_path(self.absolute_dir, [Constant.state_file])
            file_helper.open_readonly_file(fname, self.load_and_init_done_folders)
        except FileNotFoundError:
            self.logger.info("No state file found.")

    def check_for_previous_progress(self, prefix, folder, filename):
        """ Check previous progress key """
        try:
            if self.done_progress[helper.construct_path(prefix, [folder])][filename] == 1:
                return True
            return False
        except KeyError:
            return False

    def check_done_folder(self, mode, foldername):
        """ Check if folder was already done """
        self.logger.debug("Mode " + mode + " " + foldername)
        # check all the files for 1 value
        for folder in self.done_folders:
            if folder == helper.construct_path(mode, [foldername]):
                return True
        return False

    def is_max_files_reached(self):
        """ Check max files """
        if self.max_files != -1:
            return self.max_files == self.done_files
        return False

    def add_file_init(self, combined, filename):
        """ Add file to init key """
        try:
            if combined not in self.done_progress:
                self.initialize_done_progress(combined)
            self.done_progress[combined][filename] = 0
        except KeyError:
            self.logger.debug("Combined: " + combined + " Filename: " + filename)
            self.logger.warning("Key error init " + combined)
            self.initialize_done_progress(combined)
            self.done_progress[combined][filename] = 0

    def add_file_done(self, folderpath, filename):
        """ Add file to done list """
        self.logger.info("Adding file to DONE " + filename)
        try:
            self.done_progress[folderpath][filename] = 1
            self.done_files += 1
        except KeyError:
            try:
                self.initialize_done_progress(folderpath)
                self.done_progress[folderpath][filename] = 1
                self.done_files += 1
            except KeyError as ex:
                self.logger.warning("Key error file_done: " + ex.__str__())
                self.logger.debug(self.done_progress)

    def init_empty(self, folder):
        """ Init empty folder """
        return {"done": 0, "path": folder}

    def initialize_done_progress(self, folderpath, old=None):
        """  Initialize key for a folder in our dict structure """
        helper.check_valid_folderkey(folderpath)
        if old != None:
            self.done_progress[folderpath] = old
        else:
            self.done_progress[folderpath] = self.init_empty(folderpath)

    def compare_files_done(self, folder):
        """ Folder must be a list """
        # we get a dict with 2 keys that say nothing about the folder
        number_of_files = len(folder.keys()) - 2
        actual_done = 0
        for key, value in folder.items():
            if key != "done" and key != "path" and value == 1:
                actual_done += 1
        self.logger.debug(folder)
        self.logger.debug("Files: " + str(number_of_files) + " Actual: " + str(actual_done))
        return number_of_files == actual_done

    def check_folders_done(self):
        """ Check which folders are already complete """
        for folder_name, folder in self.done_progress.items():
            if folder["done"] != 1:
                self.logger.debug("folder not done yet")
                if self.compare_files_done(folder):
                    self.write_done_folder(folder, folder_name)
        return self.complete_folders

    def write_done_folder_to_newline(self, append_file, args):
        """ Write a line to file """
        append_file.write(args["path"] + "\n")

    def write_done_folder(self, folder, folder_name):
        """ Write done folder to state file """
        path = helper.construct_path(self.absolute_dir, [Constant.state_file])
        args = {'path': folder["path"]}
        file_helper.open_appendonly_file(path, self.write_done_folder_to_newline, args)
        if folder_name != '': # dont know why this could happen
            self.done_progress[folder_name]["done"] = 1
            self.complete_folders.append(folder["path"])

    def save(self):
        """ Save progress """
        if self.cur_folder != None:
            self.logger.debug("Saving progress..")
            mode_folder = self.cur_folder
            return self.save_progress_for_unfinished(mode_folder)
        raise ValueError("Missing current folder!")

    def write_progress_folder(self, write_file, args):
        """ Write json to file """
        write_file.write(args['enc'])

    def read_last_processed_folder(self, folder):
        """ Read the last processed folder json """
        try:
            self.logger.debug(self.done_folders)
            for directory in self.done_folders:
                if directory == folder:
                    self.logger.info("Not saving folder, because already done.")
                    return None
            last_file = self.done_progress[folder]
            return last_file
        except KeyError:
            self.logger.error("Key: " + folder)
            self.logger.error("Key error in save_progress_for_unfinished")
            self.logger.error(self.done_progress)
            return None

    # save the progress of the last folder
    def save_progress_for_unfinished(self, folder):
        """ Save the progress for unfinished task """
        last_file = self.read_last_processed_folder(folder)
        if last_file:
            enc = json.dumps(last_file)
            path = helper.construct_path(self.absolute_dir, [Constant.previous_state])
            args = {'enc':enc}
            import os
            if os.path.isfile(path):
                os.remove(path)
            file_helper.open_write_file(path, self.write_progress_folder, args)
            return True
        return False
