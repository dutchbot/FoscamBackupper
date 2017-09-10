from foscambackup.constant import Constant
import unittest.mock as mock
from ftplib import FTP
from unittest.mock import call
import helper

def mlsd(*args, **kwargs):
    yield (".", {'type':'folder'})
    yield (Constant.sd_rec, {'type':'file'})

def retrbinary_false(*args, **kwargs):
    file_handle = bytes(helper.get_current_date_offset_day()+"_100000",'ascii')
    args[1](file_handle)

def retrbinary(*args, **kwargs):
    file_handle = bytes(helper.get_current_date_time_rounded(),'ascii')
    args[1](file_handle)

conn = mock.MagicMock(name="ftp_connection", spec=FTP)
conn.mlsd = mock.Mock(side_effect=mlsd, spec=str)
conn.retrbinary = mock.Mock(side_effect=retrbinary, spec=str)
