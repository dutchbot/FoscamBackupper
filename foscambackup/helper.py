""" Contains helper functions """
import os
import time
import shutil
from foscambackup.constant import Constant

def sl():
    """ return slash in use """
    return "/"

def retrieve_model_serial(connection):
    """ Get the serial number """
    dir_list = mlsd(connection, Constant.base_folder)
    for directory, _ in dir_list:
        if not "." in directory:
            return directory

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

def select_folder(folders=[]):
    """ Set remote folder command """
    base = "CWD " + sl() + Constant.base_folder
    for folder in folders:
        base = base + sl() + folder
    return base

def clean_folder_path(folder):
    """ Remove the subdir to find the correct key in dict/list """
    splitted = folder.split(sl())
    # if "-" in folder: #failsafe
    #     return folder[:-16]
    if len(splitted) == 3:
        return construct_path(splitted[0],[splitted[1]])
    return folder

def create_retr_command(path):
    """ Create the RETR command at path """
    if "." in path: # Really basic check for file ext
        return "RETR " + path
    raise ValueError("Malformed path, missing file ext?")

def set_remote_folder_fullpath(connection, fullpath):
    """ Set remote folder """
    connection.sendcmd(fullpath)

def cleanup_directories(folder):
    """ Used to cleanup a tree of folders and files """
    shutil.rmtree(folder, ignore_errors=False, onerror=on_error)

def on_error(func, path, exc_info):
    """ Callback function for OS errors when deleting a folder tree """
    print("Calling error")
    print(func)
    print(path)
    print(exc_info)

def mlsd(con, path):
    """ Cleans the dot and dotdot folders """
    file_list = con.mlsd(path)
    print(file_list)
    cleaned = [print(i) for i in file_list if check_not_curup(i[0])]
    return cleaned

def get_cwd():
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
        print(type(folders))
        raise ValueError
    count = 0
    for folder in folders:
        if len(folders) != count:
            start += sl()
        start += folder
        count += 1
        if len(folders) == count and endslash:
            start += sl()
    return start
