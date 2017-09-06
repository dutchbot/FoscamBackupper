""" Contains helper functions """
import time
import shutil
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

def clean_folder_path(folder):
    """ Remove the subdir to find the correct key in dict/list """
    if "_" in folder: #failsafe
        return folder[:-16]
    return folder

def create_retr_command(path):
    """ Create the RETR command at path """
    if "." in path: # Really basic check for file ext
        return "RETR " + path
    raise ValueError

def set_remote_folder_fullpath(connection, fullpath):
    """ Set remote folder """
    connection.sendcmd(fullpath)

def get_current_date():
    """ This is the format for the date folder where the subfolders and files will be located. """
    return time.strftime("%Y%m%d")

def get_current_date_time_rounded():
    """ This how the foscam model constructs the subfolders located in a date folder. """
    return time.strftime("%Y%m%d_%H0000")

def get_current_date_time():
    """ This is how the filenames are constructed on the foscam camera."""
    return time.strftime("%Y%m%d_%H%M%S")

def get_current_date_time_offset(offset):
    """ For testing purposes """
    if offset != 0:
        time_str = time.strftime("%Y%m%d_%H%M%S")
        calc_offset = str(int(time_str[:-2]) + offset)
        l_timestr = list(time_str)
        l_timestr[-2] = calc_offset[0]
        l_timestr[-1] = calc_offset[1]
        time_str = ''.join(l_timestr)
        print("TIME" + time_str)
        return time_str
    return time.strftime("%Y%m%d_%H%M%S")

def close_connection(connection):
    """ Close the FTP connection """
    connection.close()

def cleanup_directories(folder):
    """ Used to cleanup a tree of folders and files """
    shutil.rmtree(folder, ignore_errors=False, onerror=on_error)

def on_error(func, path, exc_info):
    """ Callback function for OS errors when deleting a folder tree """
    print("Calling error")
    print(func)
    print(path)
    print(exc_info)

def clean_newline_char(line):
    """ Remove /n from line """
    return line[:-1]

def get_abs_path(conf, mode):
    """ Construct the absolute remote path, looks like IPCamera/FXXXXXX_CXXXXXXXXXXX/[mode] """
    return construct_path("/" + Constant.base_folder, [conf.model, mode["folder"]])

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
            start += "/"
        start += folder
        count += 1
        if len(folders) == count and endslash:
            start += "/"
    return start
