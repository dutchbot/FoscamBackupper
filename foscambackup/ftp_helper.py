""" Contains functions for ftp interaction """
from ftplib import FTP
from foscambackup.constant import Constant
import foscambackup.helper as helper

def close_connection(connection):
    """ Close the FTP connection """
    connection.close()

def open_connection(conf):
    """ Open FTP connection to server with conf information """
    connection = FTP()
    connection.set_pasv(False)
    connection.connect(conf.host, conf.port)
    connection.login(conf.username, conf.password)

    return connection

def set_remote_folder_fullpath(connection, fullpath):
    """ Set remote folder """
    connection.sendcmd(fullpath)

def retrieve_model_serial(connection):
    """ Get the serial number """
    dir_list = mlsd(connection, Constant.base_folder)
    for directory, _ in dir_list:
        if not "." in directory:
            return directory

def select_folder(folders=[]):
    """ Set remote folder command """
    base = "CWD " + helper.sl() + Constant.base_folder
    for folder in folders:
        base = base + helper.sl() + folder
    return base

def mlsd(con, path):
    """ Cleans the dot and dotdot folders """
    file_list = con.mlsd(path)
    if file_list:
        cleaned = [i for i in file_list if helper.check_not_curup(i[0])]
    if cleaned is None:
        raise ValueError("Empty result")
    return cleaned

def retr(con, abs_path, callback):
    """ Download binary file """
    con.retrbinary(abs_path, callback)

def create_retr(path):
    """ Create the RETR command at path """
    if "." in path: # Really basic check for file ext
        return "RETR " + path
    raise ValueError("Malformed path, missing file ext?")

def size(con, path):
    """ Return the file size at abs path """
    con.sendcmd("TYPE i")
    f_size = con.size(path)
    con.sendcmd("TYPE A")
    return f_size
