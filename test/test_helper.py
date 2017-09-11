
import foscambackup.helper as helper
import unittest
import unittest.mock as umock
import time

#@unittest.SkipTest
class TestHelper(unittest.TestCase):

    def test_sl(self):
        self.assertEqual(helper.sl(), "/")

    def test_get_current_date(self):
        self.assertEqual(helper.get_current_date(), time.strftime("%Y%m%d"))

    def test_check_not_dat_file(self):
        self.assertEqual(helper.check_not_dat_file("test.txt"), True)
        self.assertEqual(helper.check_not_dat_file("test.dat"), False)

    def test_check_file_type_dir(self):
        desc = {'type': 'dir'}
        self.assertEqual(helper.check_file_type_dir(desc), True)
        desc = {'type': 'file'}
        self.assertEqual(helper.check_file_type_dir(desc), False)

    def test_retrieve_split(self):
        split = "test/oh".split("/")
        self.assertEqual(helper.retrieve_split(split, "test"), True)
        split = "oh/test".split("/")
        self.assertEqual(helper.retrieve_split(split, "test"), False)

    def test_check_not_curup(self):
        self.assertEqual(helper.check_not_curup("oh.test"), True)
        self.assertEqual(helper.check_not_curup(".test"), True)
        self.assertEqual(helper.check_not_curup("."), False)
        self.assertEqual(helper.check_not_curup(".."), False)

    def test_clean_folder_path(self):
        folder_parent = "record/20160501"
        folder_parent_subdir = folder_parent + "/20160501_120000"
        self.assertEqual(helper.clean_folder_path(
            folder_parent_subdir), folder_parent)
        self.assertEqual(helper.clean_folder_path(
            folder_parent), folder_parent)

    def test_cleanup_directories(self):
        shutil = umock.MagicMock()
        shutil.rmtree = umock.MagicMock()
        with umock.patch("shutil.rmtree", shutil):
            helper.cleanup_directories("testfolder")
        self.assertEqual(shutil.called, True)

    def test_on_error(self):
        def rmtree(*args, **kwargs):
            """ mocked """
            return args

        shutil = umock.MagicMock()
        shutil.rmtree = umock.MagicMock(side_effect=rmtree)
        shutil.on_error = umock.MagicMock()
        with umock.patch("shutil.rmtree", shutil.rmtree), \
                umock.patch("foscambackup.helper.on_error", shutil.on_error):
            helper.cleanup_directories("testfolder")
        calls = [umock.call.rmtree(
            'testfolder', ignore_errors=False, onerror=shutil.on_error)]
        self.assertListEqual(shutil.method_calls, calls)

    def test_clean_newline_char(self):
        val = "test\n"
        self.assertEqual(helper.clean_newline_char(val), "test")
        self.assertEqual(helper.clean_newline_char("test"), "test")

    def test_verify_path(self):
        path = "/IPCamera/FXXXXX_CEEEEEEEEEEE/snap/20170910/20170910-143000/testfile.avi"
        self.assertEqual(helper.verify_path(path), True)
        with self.assertRaises(ValueError):
            path = "/IPCamera/FXXXXX_CEEEEEEEEEEE/snap/20170910/20170910.av/testfile.avi"
            helper.verify_path(path)

    def test_get_abs_path(self):
        mode = {"folder": "record"}
        conf = umock.MagicMock()
        conf.model = "FXXXCC_EEEE" # TODO add helper method to validate model_serial
        self.assertEqual(helper.get_abs_path(conf, mode),
                         "/IPCamera/" + conf.model + "/" + mode['folder'])
        mode = {"folder": "snap"}
        self.assertEqual(helper.get_abs_path(conf, mode),
                         "/IPCamera/" + conf.model + "/" + mode['folder'])

    def test_construct_path(self):
        self.assertEqual(helper.construct_path("test",['mytest','ofc']), "test/mytest/ofc")
        self.assertEqual(helper.construct_path("test",['mytest','ofc'], True), "test/mytest/ofc/")

    def test_check_valid_folderkey(self):
        folder = "record/20160501"
        self.assertEqual(helper.check_valid_folderkey(folder), True)
        folder = "20160501"
        with self.assertRaises(ValueError):
            helper.check_valid_folderkey(folder)
        folder = ""
        with self.assertRaises(ValueError):
            helper.check_valid_folderkey(folder)
