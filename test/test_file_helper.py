import unittest
import unittest.mock as umock
import foscambackup.file_helper as file_helper
from mocks import mock_file_helper
from io import StringIO

class TestFileHelper(unittest.TestCase):

    def setUp(self):
        def generic(path):
            return True

        def caller(*args, **kwargs):
            return True

        def close(*args, **kwargs):
            return True

        self.ospath = umock.MagicMock()
        self.ospath.isfile = umock.MagicMock(side_effect=generic)

        self.callback = umock.MagicMock(side_effect=caller)

        self.file_handle = umock.MagicMock(name="file")
        self.file_handle.close = umock.MagicMock(side_effect=close, spec=StringIO)
        self.file_state = umock.MagicMock(name="read", return_value=self.file_handle)


    def test_open_readonly_file(self):
        with umock.patch("builtins.open", self.file_state):
            with umock.patch("os.path.isfile", self.ospath.isfile):
                file_helper.open_readonly_file("/record", self.callback)

        self.assertEqual(self.ospath.isfile.called, True)
        self.assertEqual(self.callback.called, True)
        self.assertEqual(self.file_handle.close.called, True)

    def test_open_appendonly_file(self):
        call = umock.call

        self.file_state.__name__ = "append"
        args = {}

        with umock.patch("builtins.open", self.file_state):
            file_helper.open_appendonly_file("/record.txt", self.callback, args)
        
        call_args = [call(self.file_handle,{})]
        self.assertListEqual(self.callback.call_args_list, call_args)
        self.assertEqual(self.file_handle.close.call_args_list, call())

    def test_open_write_file(self):
        call = umock.call

        self.file_state.__name__ = "write"
        args = {}

        with self.assertRaises(FileExistsError):
            with umock.patch("builtins.open", self.file_state), \
                umock.patch("os.path.isfile", self.ospath.isfile):
                    file_helper.open_write_file("/record.txt", self.callback, args)
        
        def not_exist(path):
            return False

        self.ospath.isfile.side_effect = not_exist

        with umock.patch("builtins.open", self.file_state), \
            umock.patch("os.path.isfile", self.ospath.isfile):
                file_helper.open_write_file("/record.txt", self.callback, args)
        
        call_args = [call(self.file_handle,{})]
        self.assertListEqual(self.callback.call_args_list, call_args)
        self.assertEqual(self.file_handle.close.call_args_list, call())
