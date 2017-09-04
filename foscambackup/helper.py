""" Contains helper functions """
from foscambackup.constant import Constant

def check_dat_file(filename):
    """ check for dat file """
    return not ".dat" in filename


def check_not_curup_dir(filename):
    """ check for current dir or parent dir"""
    return not ".." in filename and not "." in filename


def check_file_type(desc):
    """ check if file desc is dir """
    return desc['type'] != 'dir'


def retrieve_split(split, val):
    """ Split compare to val """
    return split[0] == val

def select_folder(folders=[]):
    """ Set remote folder command """
    base = "CWD " + "/" + Constant.f_folder
    for folder in folders:
        base = base + "/" + folder
    return base

def set_remote_folder_fullpath(connection, fullpath):
    """ Set remote folder """
    connection.sendcmd(fullpath)
