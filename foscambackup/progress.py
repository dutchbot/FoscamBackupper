""" Track progress of downloading etc """
import os
import json
import logging

from foscambackup.constant import Constant
import foscambackup.util.helper as helper
import foscambackup.util.file_helper as file_helper

class Progress:
    """ Track progress """
    logger = logging.getLogger('Worker')
    max_files = -1

    def __init__(self, cur_folder, test=False):
        if not isinstance(cur_folder, str):
            raise ValueError("Cur_folder must be a string!")
        self.done_files = 0
        self.done_progress = self.init_empty(cur_folder)
        self.cur_folder = cur_folder
        self.absolute_dir = helper.get_cwd()

        if not test:
            self.read_previous_progress_file()

    def load_and_init(self, read_file):
        """ Read the dict from file and parse with JSON module """
        progress_folder = json.load(read_file)
        self.initialize_done_progress(progress_folder)

    def construct_state_file_path(self):
        abs_prefix = self.absolute_dir + helper.slash() + Constant.previous_state
        names = self.cur_folder.split("/")
        return abs_prefix + names[0] + "_" + names[1] + Constant.previous_state_ext

    def read_previous_progress_file(self):
        """ Read previous progress from file """
        try:
            previous = self.construct_state_file_path()
            file_helper.open_readonly_file(previous, self.load_and_init)
        except FileNotFoundError:
            self.logger.info("No previous unfinished result found for: " + self.cur_folder)

    def check_for_previous_progress(self, loc_info):
        """ Check previous progress key """
        filename = loc_info['filename']
        try:
            if self.done_progress["files"][filename] == 1:
                return True
            return False
        except KeyError:
            return False

    def check_done_folder(self):
        """ Check if folder is done by counting the files downloaded """
        count_files = 0
        count_downloaded = 0
        for _, downloaded in self.done_progress["files"].items():
            if downloaded:
                count_downloaded +=1
            count_files += 1
        return count_downloaded == count_files and count_files != 0

    def is_max_files_reached(self):
        """ Check max files """
        if self.max_files != -1:
            return self.max_files == self.done_files
        return False

    def add_file_init(self, filename):
        """ Add file to init key """
        if self.done_progress is None:
            self.initialize_done_progress()
        self.done_progress["files"][filename] = 0

    def add_file_done(self, folderpath, filename):
        """ Add file to done list """
        self.logger.debug("Adding file to DONE " + filename)
        self.done_progress["files"][filename] = 1
        self.done_files += 1

    def init_empty(self, folder=""):
        """ Init empty folder """
        if folder == "":
            folder = self.cur_folder
        return {"done": 0, "path": folder, "files":{}}

    def initialize_done_progress(self, old=None):
        """  Initialize key for a folder in our dict structure """
        if old != None:
            if isinstance(old, dict):
                self.done_progress = old
            else:
                raise ValueError("Expected a dictionary type which describes the progress!")
        else:
            self.done_progress = self.init_empty()

    def write_done_folder_to_newline(self, append_file, args):
        """ Write a line to file """
        append_file.write(args["path"] + "\n")

    def write_done_folder(self, folder_name):
        """ Write done folder to state file """
        path = helper.construct_path(self.absolute_dir, [Constant.state_file])
        args = {'path': folder_name}
        file_helper.open_appendonly_file(path, self.write_done_folder_to_newline, args)
        self.done_progress["done"] = 1

    def save(self):
        """ Save progress """
        if self.cur_folder != None and self.cur_folder !="":
            self.logger.debug("Saving progress..")
            return self.save_progress_for_unfinished()
        raise ValueError("Missing current folder!")

    def write_progress_folder(self, write_file, args):
        """ Write json to file """
        write_file.write(args['enc'])

    def save_progress_for_unfinished(self):
        """ Save the progress for unfinished task """
        enc = json.dumps(self.done_progress)
        path = self.construct_state_file_path()
        args = {'enc':enc}
        if os.path.isfile(path):
            os.remove(path)
        file_helper.open_write_file(path, self.write_progress_folder, args)
        return True
