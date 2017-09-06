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

def set_remote_folder_fullpath(connection, fullpath):
    """ Set remote folder """
    connection.sendcmd(fullpath)

def get_current_date():
    return time.strftime("%Y%m%d")

def get_current_date_time():
    return time.strftime("%Y%m%d_%H%M%S")

def get_current_date_time_offset(offset):
    if offset != 0:
        time_str = time.strftime("%Y%m%d_%H%M%S")
        calc_offset = str(int(time_str[:-2]) + offset)
        l_timestr = list(time_str)
        l_timestr[-2] = calc_offset[0]
        l_timestr[-1] = calc_offset[1]
        time_str = ''.join(l_timestr)
        print("TIME" + time_str)
        return time_str
    else:
        return time.strftime("%Y%m%d_%H%M%S")

def get_current_date_time_rounded():
    return time.strftime("%Y%m%d_%H0000")

def cleanup_directories(folder):
    shutil.rmtree(folder, ignore_errors=False, onerror=on_error)

def on_error(func, path, exc_info):
    print("Calling error")
    print(func)
    print(path)
    print(exc_info)

def construct_path(start, folders=[], endslash = False):
    if type(folders) != type([]):
        print(type(folders))
        raise ValueError
    count = 0
    for folder in folders:
        if len(folders) != count:
            start += "/"
        start += folder 
        count +=1
        if len(folders) == count and endslash:
            start += "/"
    return start
