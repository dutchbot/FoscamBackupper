""" Contains helper functions """
import time
from foscambackup.constant import Constant

def check_dat_file(filename):
    """ check for dat file """
    return not ".dat" in filename

def check_not_curup_dir(filename):
    """ check for current dir or parent dir"""
    return not ".." in filename and not "." in filename

def check_file_type_dir(desc):
    """ check if file desc is dir """
    return desc['type'] == 'dir'

def retrieve_split(split, val):
    """ Split compare to val """
    return split[0] == val

def select_folder(folders=[]):
    """ Set remote folder command """
    base = "CWD " + "/" + Constant.base_folder
    for folder in folders:
        base = base + "/" + folder
    return base

def set_remote_folder_fullpath(connection, fullpath):
    """ Set remote folder """
    connection.sendcmd(fullpath)

def get_current_date():
    return time.strftime("%Y%m%d")

def get_current_date_time():
    return time.strftime("%Y%m%d_%H%M%S")

def get_current_date_time_rounded():
    return time.strftime("%Y%m%d_%H0000")

def construct_path(start, folders=[], endslash = False):
    count = 0
    for folder in folders:
        if len(folders) != count:
            start += "/"
        start += folder 
        count +=1
        if len(folders) == count and endslash:
            start += "/"
    return start
