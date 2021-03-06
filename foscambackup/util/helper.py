""" Contains helper functions """
import os
import time
import shutil
import logging
from foscambackup.constant import Constant

logger = logging.getLogger('Worker')

def slash():
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
    splitted = folder.split(slash())
    if len(splitted) == 3:
        return construct_path(splitted[0], [splitted[1]])
    return folder

def cleanup_directories(folder):
    """ Used to cleanup a tree of folders and files """
    shutil.rmtree(folder, ignore_errors=False, onerror=on_error)

def on_error(func, path, exc_info):
    """ Callback function for OS errors when deleting a folder tree """
    logger.error(func)
    logger.error(path)
    logger.error(exc_info)

def get_cwd():
    """ Get the current working directory """
    return os.getcwd()

def clean_newline_char(line):
    """ Remove /n from line """
    if "\n" in line:
        return line[:-1]
    return line

def verify_path(path, mode):
    """ Verify we constructed a valid remote path """
    import re
    regex = r'\/[a-zA-Z]{8}\/([A-Z0-9]){6,7}_([A-Z0-9]){12}\/[a-z]{4,6}\/[0-9]{8}\/[0-9]{8}-[0-9]{6}'
    sep = mode['separator']
    if sep == '_':
        regex = regex[:-9] + regex[-9:].replace('-', sep, 1)
    pattern = re.compile(regex)
    if pattern.match(path):
        return True
    raise ValueError("Invalid constructed path!")

def get_abs_path(conf, mode):
    """ Construct the absolute remote path, looks like IPCamera/FXXXXXX_CXXXXXXXXXXX/[mode] """
    return construct_path(slash() + Constant.base_folder, [conf.model, mode["folder"]])

def construct_path(start, folders=[], endslash=False):
    """ Helps to get rid of all the slashes scattered throughout the program
        And thus helps migitate possible typo's.
    """
    if not isinstance(folders, type([])):
        raise TypeError("Expected list of folders!")
    count = 0
    for folder in folders:
        if len(folders) != count:
            start += slash()
        start += folder
        count += 1
        if len(folders) == count and endslash:
            start += slash()
    return start

def check_valid_folderkey(folder):
    """ Verify that key is correct """
    if folder is None or folder == '':
        raise ValueError("Foldername empty!")
    if slash() in folder and len(folder.split(slash())[1]) == 8:
        return True
    raise ValueError("Foldername truncated!")

def is_subdir(subdir, foldername):
    """ Verify our current folder is not a subdirectory """
    if subdir:
        return foldername in subdir['subdirs']
    return False
