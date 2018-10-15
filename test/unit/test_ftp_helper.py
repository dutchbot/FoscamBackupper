
import copy
import unittest
import unittest.mock as umock
from test.mocks import mock_worker
import foscambackup.util.ftp_helper as ftp_helper


CONN = copy.deepcopy(mock_worker.conn) # Fix for reusing static conn
call = umock.call

#@unittest.SkipTest
class TestFtpHelper(unittest.TestCase):

    def test_close_connection(self):
        def close(*args, **kwargs):
            return True

        CONN.close = umock.MagicMock(side_effect=close)
        ftp_helper.close_connection(CONN)
        self.assertEqual(CONN.close.called, True)

    def test_open_connection(self):
        def generic(*args, **kwargs):
            return "l"

        CONN.set_pasv = umock.MagicMock(side_effect=generic)
        CONN.connect = umock.MagicMock(side_effect=generic)
        CONN.login = umock.MagicMock(side_effect=generic)

        conf = umock.MagicMock(host="127.0.0.1", port=21,
                               username="test", password="abc@123")

        with umock.patch('foscambackup.util.ftp_helper.FTP.set_pasv', CONN.set_pasv), \
                umock.patch('foscambackup.util.ftp_helper.FTP.connect', CONN.connect), \
                umock.patch('foscambackup.util.ftp_helper.FTP.login', CONN.login):
            ftp_helper.open_connection(conf)

        self.assertEqual(CONN.set_pasv.call_args_list, [call(False)])
        self.assertEqual(CONN.connect.call_args_list, [call(conf.host, conf.port)])
        self.assertEqual(CONN.login.call_args_list, [call(conf.username, conf.password)])

    def test_set_remote_folder_fullpath(self):
        fullpath = "/IPCamera/FXXXC_XXE"
        CONN.cmd = umock.MagicMock()

        ftp_helper.set_remote_folder_fullpath(CONN, fullpath)

        self.assertEqual(CONN.sendcmd.call_args_list, [call(fullpath)])

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

        CONN.mlsd.side_effect = mlsd

        result = ftp_helper.mlsd(CONN, "/IPCamera")
        self.assertListEqual(result, [("record", {'type':'folder'}), ("snap", {'type':'folder'})])
        result = ftp_helper.mlsd(CONN, "")
        self.assertListEqual(result, [])

    def test_retr(self):
        def caller(bin_file):
            return True

        CONN.callback = umock.MagicMock(side_effect=caller)

        ftp_helper.retr(CONN, "/IPCamera/record", CONN.callback)
        self.assertEqual(CONN.callback.called, True)

    def test_create_retr(self):
        query = "/IPCamera/abc234.avi"
        self.assertEqual(ftp_helper.create_retrcmd(query), "RETR " + query)
        with self.assertRaises(ValueError):
            ftp_helper.create_retrcmd("/IPCamera/record")

    def test_size(self):
        """ Verify we go to Binary, retrieve size and go back to ASCII """
        def generic(value):
            pass
        CONN.sendcmd = umock.MagicMock(side_effect=generic)
        CONN.size = umock.MagicMock(side_effect=generic)
        ftp_helper.size(CONN, 'IPCamera/record/test')

        self.assertListEqual(CONN.sendcmd.call_args_list, [call('TYPE i'), call('TYPE A')])
        self.assertListEqual(CONN.size.call_args_list, [call('IPCamera/record/test')])
