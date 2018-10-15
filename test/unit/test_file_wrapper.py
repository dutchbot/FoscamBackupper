
import unittest
import unittest.mock as umock
from unittest.mock import call

import progressbar

from foscambackup.file_wrapper import FileWrapper
from test.mocks import mock_file_helper

WRITE = mock_file_helper.WRITE
WRITE.return_value = WRITE

class TestFileWrapper(unittest.TestCase):

    def setUp(self):
        test_file = "12345.avi"
        self.byte_size = 266613824
        with umock.patch("builtins.open", WRITE):
            self.wrapper = FileWrapper(test_file, self.byte_size)

    def tearDown(self):
        WRITE.reset_mock()

    def test_file_wrap_init(self):
        """ Verify class vars are initialized """
        self.assertIsInstance(self.wrapper.cur_file, umock.MagicMock)
        self.assertEqual(self.wrapper.total_size, self.byte_size)
        self.assertEqual(self.wrapper.downloaded_bytes, 0)
        self.assertIsInstance(self.wrapper.progressbar, progressbar.ProgressBar)
    
    def test_write_to_file(self):
        """ Assert write and update_progress are called correctly """
        def update(byte_len):
            pass
        mock_update = umock.MagicMock(side_effect=update)
        writing = '123456'
        with umock.patch("foscambackup.file_wrapper.FileWrapper.update_progress", mock_update):
            self.wrapper.write_to_file(writing)
            self.assertListEqual(mock_update.call_args_list, [call(len(writing))])
            self.assertListEqual(WRITE.call_args_list, [call('12345.avi', 'w+b')])
            self.assertEqual(WRITE.buffer, writing)

    def test_update_progress(self):
        """ Assert that the proper values are computed """
        byte_size = 8192
        remainder = self.wrapper.total_size % byte_size
        number_of_times = (self.wrapper.total_size - remainder) / byte_size
        number_of_times += 1 if remainder > 0 else 0
        for i in range(0, round(number_of_times)):
            if i == number_of_times -1:
                self.wrapper.update_progress(remainder)
            else:
                self.wrapper.update_progress(byte_size)
        self.assertEqual(self.wrapper.downloaded_bytes, self.wrapper.total_size)
        self.assertEqual(self.wrapper.progressbar.data()['percentage'], 100.00)

    def test_close_file(self):
        """ Test if close function is called """
        WRITE.close = umock.MagicMock()
        self.wrapper.close_file()
        self.assertEqual(self.wrapper.cur_file.close.call_args_list,[call()])
