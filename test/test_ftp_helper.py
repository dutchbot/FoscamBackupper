
import foscambackup.ftp_helper as ftp_helper
import unittest.mock as umock
import copy
from mocks import mock_worker
import unittest

conn = copy.deepcopy(mock_worker.conn) # Fix for reusing static conn
call = umock.call

class TestFtpHelper(unittest.TestCase):

    def test_close_connection(self):
        def close(*args, **kwargs):
            return True

        conn.close = umock.MagicMock(side_effect=close)
        ftp_helper.close_connection(conn)
        self.assertEqual(conn.close.called, True)

    def test_open_connection(self):
        def generic(*args, **kwargs):
            return "l"

        conn.set_pasv = umock.MagicMock(side_effect=generic)
        conn.connect = umock.MagicMock(side_effect=generic)
        conn.login = umock.MagicMock(side_effect=generic)

        conf = umock.MagicMock(host="127.0.0.1", port=21,
                               username="test", password="abc@123")

        with umock.patch('foscambackup.ftp_helper.FTP.set_pasv', conn.set_pasv), \
                umock.patch('foscambackup.ftp_helper.FTP.connect', conn.connect), \
                umock.patch('foscambackup.ftp_helper.FTP.login', conn.login):
            ftp_helper.open_connection(conf)

        self.assertEqual(conn.set_pasv.call_args_list, [call(False)])
        self.assertEqual(conn.connect.call_args_list, [call(conf.host, conf.port)])
        self.assertEqual(conn.login.call_args_list, [call(conf.username, conf.password)])

    def test_set_remote_folder_fullpath(self):
        fullpath = "/IPCamera/FXXXC_XXE"
        conn.cmd = umock.MagicMock()

        ftp_helper.set_remote_folder_fullpath(conn, fullpath)

        self.assertEqual(conn.sendcmd.call_args_list, [call(fullpath)])

    def test_retrieve_model_serial(self):
        pass

    def test_select_folder(self):
        compare = "CWD /IPCamera"
        compare2 = "CWD /IPCamera/record/test"
        self.assertEqual(ftp_helper.select_folder(), compare)
        self.assertEqual(ftp_helper.select_folder(['record','test']), compare2)

    def test_mlsd(self):
        def mlsd(*args, **kwargs):
            yield (".", {'type':'folder'})
            yield (".", {'type':'folder'})
            if(args[0] != ""):
                yield ("record", {'type':'folder'})
                yield ("snap", {'type':'folder'})

        conn.mlsd.side_effect = mlsd

        result = ftp_helper.mlsd(conn, "/IPCamera")
        self.assertListEqual(result, [("record", {'type':'folder'}), ("snap", {'type':'folder'})])
        result = ftp_helper.mlsd(conn, "")
        self.assertListEqual(result, [])

    def test_retr(self):
        def caller(bin_file):
            return True

        conn.callback = umock.MagicMock(side_effect=caller)

        ftp_helper.retr(conn, "/IPCamera/record", conn.callback)
        self.assertEqual(conn.callback.called, True)

    def test_create_retr(self):
        query = "/IPCamera/abc234.avi"
        self.assertEqual(ftp_helper.create_retr(query), "RETR "+query)
        with self.assertRaises(ValueError):
            ftp_helper.create_retr("/IPCamera/record")
