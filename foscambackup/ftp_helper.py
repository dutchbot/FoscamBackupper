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

def retrieve_model_serial(connection):
    """ Get the serial number """
    dir_list = mlsd(connection, Constant.base_folder)
    for directory, _ in dir_list:
        if not "." in directory:
            return directory

def mlsd(con, path):
    """ Cleans the dot and dotdot folders """
    file_list = con.mlsd(path)
    cleaned = [i for i in file_list if helper.check_not_curup(i[0])]
    if cleaned is None:
        raise ValueError("Empty result")
    return cleaned

def retr(con, abs_path, callback):
    """ Download binary file """
    con.retrbinary(abs_path, callback)
