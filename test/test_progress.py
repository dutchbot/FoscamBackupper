
import builtins
import unittest
import unittest.mock as mock
from io import StringIO
from foscambackup.progress import Progress
import json

# mock file read
read_state = mock.MagicMock(name="open", spec=str)
read_state.read = mock.Mock(return_value = StringIO("{\"20160501_220030.avi\":1, \"done\":1, \"path\":\"record/20160501\"}"), spec=str)

read_s = mock.MagicMock(name="open", spec=str)
read_s.read = mock.Mock(return_value = StringIO("record/20160501"), spec=str)


class TestProgress(unittest.TestCase):
    # we need 24 TESTS
    
    def setUp(self):
        self.progress = Progress()

    @mock.patch('builtins.open', read_state)
    def test_load_and_init(self):
        """ Test the load function"""
        read_file = read_state.read()
        self.progress.load_and_init(read_file)
        progress_folder = json.loads(read_file.getvalue())
        self.assertDictEqual(self.progress.done_progress[progress_folder['path']], json.loads(read_file.getvalue()))

    def test_read_previous_state_file(self):
        """ Tested by test_load_and_init """
        pass

    @mock.patch('builtins.open', read_s)
    def test_load_and_init_done_folders(self):
        read_file = read_s.read()
        path = 'record/20160501'
        self.progress.load_and_init_done_folders(read_file)
        self.assertListEqual(self.progress.done_folders, [path])
        self.assertDictEqual(self.progress.done_progress[path], {"done":1,"path":"record/20160501"})
        
    def test_read_state_file(self):
        """ Tested by test_load_and_init_done_folders """
        pass

    def test_set_max_files(self):
        self.progress.set_max_files(20)
        self.assertEqual(self.progress.max_files, 20)

    def test_set_cur_mode(self):
        self.progress.set_cur_mode("record")
        self.assertEqual(self.progress.cur_mode, "record")

    def test_set_cur_folder(self):
        self.progress.set_cur_folder("20160501")
        self.assertEqual(self.progress.cur_folder, "20160501")

    def test_get_cur_folder(self):
        self.progress.set_cur_folder("20160501")
        self.assertEqual(self.progress.get_cur_folder(), "20160501")

    def test_check_for_previous_progress(self):
        path = 'record/20160501'
        self.progress.initialize_done_progress(path)
        self.progress.done_progress[path]['2345.avi'] = 1
        result = self.progress.check_for_previous_progress("record", "20160501", "2345.avi")
        self.progress.done_progress[path]['233345.avi'] = 0
        result = self.progress.check_for_previous_progress("record", "20160501", "233345.avi")
        self.assertEqual(result, False)

    def test_check_done_folder(self):
        path = 'record/20160501'
        self.progress.done_folders.append(path)
        self.assertEqual(self.progress.check_done_folder("record", "20160501"), True)
        self.assertEqual(self.progress.check_done_folder("record", "20160502"), False)

    def test_is_max_files_reached(self):
        self.progress.set_max_files(10)
        self.progress.done_files = 10
        self.assertEqual(self.progress.is_max_files_reached(), True)
        # reinit
        self.progress.set_max_files(-1)
        self.assertEqual(self.progress.is_max_files_reached(), False)
        self.progress.done_files = 2
        self.assertEqual(self.progress.is_max_files_reached(), False)
        self.progress.max_files = 4
        self.assertEqual(self.progress.is_max_files_reached(), False)

    def test_add_file_init(self):
        path = 'record/20160501'
        filename = "avi2345.avi"
        self.progress.add_file_init(path, filename)
        self.assertEqual(self.progress.done_progress[path][filename], 0)

    def test_add_file_done(self):
        path = 'record/20160501'
        filename = "avi2345.avi"
        self.progress.add_file_done(path, filename)
        self.assertEqual(self.progress.done_files, 1)
        self.assertEqual(self.progress.done_progress, {'record/20160501': {'done': 0, 'path': 'record/20160501', 'avi2345.avi': 1}})
    
    def test_check_valid_folderkey(self):
        folder = "record/20160501"
        self.assertEqual(self.progress.check_valid_folderkey(folder), True)
        folder = "20160501"
        with self.assertRaises(ValueError):
            self.progress.check_valid_folderkey(folder)
        folder = ""
        with self.assertRaises(ValueError):
            self.progress.check_valid_folderkey(folder)

    def test_init_empty(self):
        folder = "record/20160501"
        self.assertEqual(self.progress.init_empty(folder), {"done": 0, "path": folder})

    def test_initialize_done_progress(self):
        folder = "record/20160501"
        empty = { folder: self.progress.init_empty(folder)}
        self.progress.initialize_done_progress(folder)
        self.assertDictEqual(self.progress.done_progress, empty)
        empty[folder]['12345.avi'] = 1
        empty[folder]['done'] = 1
        self.progress.initialize_done_progress(folder, empty[folder])
        self.assertDictEqual(self.progress.done_progress, empty)

    def test_compare_files_done(self):
        folder = "record/20160501"
        folders = {}
        folders[folder] = self.progress.init_empty(folder)
        folders[folder]['20160501_220030.avi'] = 1
        folders[folder]['20160501_230030.avi'] = 1
        self.assertEqual(self.progress.compare_files_done(folders[folder]), True)
        folder = "record/20160501"
        folders = {}
        folders[folder] = self.progress.init_empty(folder)
        folders[folder]['20160501_220030.avi'] = 1
        folders[folder]['20160501_230030.avi'] = 0
        self.assertEqual(self.progress.compare_files_done(folders[folder]), False)

    def test_check_folders_done(self):
        pass

    def test_write_done_folder_to_newline(self):
        pass

    def test_write_done_folder(self):
        pass

    def test_save_progress(self):
        pass

    def test_write_progress_folder(self):
        pass

    def test_read_last_file(self):
        pass

    def test_save_progress_for_unfinished(self):
        pass
