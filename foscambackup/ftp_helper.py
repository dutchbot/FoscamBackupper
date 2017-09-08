from ftplib import FTP
from ftplib import error_perm

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
