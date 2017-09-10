""" Contains helper functions """
import os
import time
import shutil
from foscambackup.constant import Constant

def sl():
    """ return slash in use """
    return "/"

def get_current_date():
    """ This is the format for the date folder where the subfolders and files will be located. """
    return time.strftime("%Y%m%d")

def check_not_dat_file(filename):
    """ check for dat file """
    return not ".dat" in filename

def check_file_type_dir(desc):
    """ check if file desc is dir """
    return desc['type'] == 'dir'

def retrieve_split(split, val):
    """ Split compare to val """
    return split[0] == val

def check_not_curup(foldername):
    """ Check if the folder is current or one directory up.
        Note: Not necessary in test mode but real ftp server needs it to prevent recursion
    """
    return not '..' in foldername and foldername != '.'

def clean_folder_path(folder):
    """ Remove the subdir to find the correct key in dict/list """
    splitted = folder.split(sl())
    # if "-" in folder: #failsafe
    #     return folder[:-16]
    if len(splitted) == 3:
        return construct_path(splitted[0], [splitted[1]])
    return folder

def cleanup_directories(folder):
    """ Used to cleanup a tree of folders and files """
    shutil.rmtree(folder, ignore_errors=False, onerror=on_error)

def on_error(func, path, exc_info):
    """ Callback function for OS errors when deleting a folder tree """
    print("Calling error")
    print(func)
    print(path)
    print(exc_info)

def get_cwd():
    """ Get the current working directory """
    return os.getcwd()

def clean_newline_char(line):
    """ Remove /n from line """
    if "\n" in line:
        return line[:-1]
    return line

def get_abs_path(conf, mode):
    """ Construct the absolute remote path, looks like IPCamera/FXXXXXX_CXXXXXXXXXXX/[mode] """
    return construct_path(sl() + Constant.base_folder, [conf.model, mode["folder"]])

def construct_path(start, folders=[], endslash=False):
    """ Helps to get rid of all the slashes scattered throughout the program
        And thus helps migitate possible typo's.
    """
    if not isinstance(folders, type([])):
        raise TypeError("Expected list of folders!")
    count = 0
    for folder in folders:
        if len(folders) != count:
            start += sl()
        start += folder
        count += 1
        if len(folders) == count and endslash:
            start += sl()
    return start
