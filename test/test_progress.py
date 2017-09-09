
import builtins
import json
import unittest
import unittest.mock as mock
from io import StringIO

import foscambackup.helper as helper
from foscambackup.constant import Constant
from foscambackup.progress import Progress

# mock file read

def mocked_append(*args, **kwargs):
    APPEND.buffer += args[0]

def mocked_write(*args, **kwargs):
    print("why not?")
    print("args : " + str(args))
    WRITE.buffer += args[0]

READ_STATE = mock.MagicMock(name="open", spec=str)
READ_STATE.read = mock.Mock(return_value=StringIO("{\"20160501_220030.avi\":1, \"done\":1, \"path\":\"record/20160501\"}"), spec=str)

READ_S = mock.MagicMock(name="open", spec=str)
READ_S.read = mock.Mock(return_value=StringIO("record/20160501"), spec=str)

APPEND = mock.MagicMock(name="open")
APPEND.write = mock.MagicMock()
APPEND.write.side_effect = mocked_append
APPEND.buffer = str()

WRITE = mock.MagicMock(name="open", spec=bytes)
WRITE.write = mock.MagicMock()
WRITE.write.side_effect = mocked_write
WRITE.buffer = str()


class TestProgress(unittest.TestCase):
    # we need 24 TESTS
    
    def setUp(self):
        self.progress = Progress(True)

    def tearDown(self):
        APPEND.buffer = ""
        WRITE.buffer = ""

    @mock.patch('builtins.open', READ_STATE)
    def test_load_and_init(self):
        """ Test the load function"""
        read_file = READ_STATE.read()
        self.progress.load_and_init(read_file)
        progress_folder = json.loads(read_file.getvalue())
        self.assertDictEqual(self.progress.done_progress[progress_folder['path']], json.loads(read_file.getvalue()))

    def test_read_previous_state_file(self):
        """ Tested by test_load_and_init """
        pass

    @mock.patch('builtins.open', READ_S)
    def test_load_and_init_done_folders(self):
        read_file = READ_S.read()
        path = 'record/20160501'
        self.progress.load_and_init_done_folders(read_file)
        self.assertListEqual(self.progress.done_folders, [path])
        self.assertDictEqual(self.progress.done_progress[path], {"done":1, "path":"record/20160501"})
        
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
        folder = "record/20160501"
        folders = {}
        folders[folder] = self.progress.init_empty(folder)
        folders[folder]['20160501_220030.avi'] = 1
        folders[folder]['20160501_230030.avi'] = 1
        self.progress.done_progress = folders
        with unittest.mock.patch('foscambackup.file_helper.open_appendonly_file', APPEND):
            self.assertListEqual(self.progress.check_folders_done(), [folder])

    def test_write_done_folder_to_newline(self):
        folder = "record/20160501"
        args = {"path": folder}

        with unittest.mock.patch('builtins.open', APPEND) as appender:
            self.progress.write_done_folder_to_newline(appender, args)

        self.assertEqual(APPEND.buffer, folder+"\n")

    def test_write_done_folder(self):
        foldername = "record/20160501"
        folder = {foldername: {"done":1, "path":foldername}}
        self.progress.done_progress[folder[foldername]['path']] = folder[foldername]
        with unittest.mock.patch('foscambackup.file_helper.open_appendonly_file', APPEND):
            self.progress.write_done_folder(folder[foldername], foldername)
        self.assertEqual(self.progress.done_progress, folder)
        self.assertEqual(self.progress.complete_folders, [folder[foldername]['path']])

    def test_save(self):
        with self.assertRaises(ValueError):
            self.progress.save()
        folder = "record/20160501"
        folders = {}
        folders[folder] = self.progress.init_empty(folder)
        folders[folder]['20160501_220030.avi'] = 1
        folders[folder]['20160501_230030.avi'] = 1
        folders[folder]['20160501_150030.avi'] = 0
        self.progress.done_progress = folders
        self.progress.set_cur_folder(folder)
        with unittest.mock.patch('builtins.open', APPEND):
            self.assertEqual(self.progress.save(), True)

    def test_write_progress_folder(self):
        folder = "record/20160501"
        folders = {}
        folders[folder] = self.progress.init_empty(folder)
        folders[folder]['20160501_220030.avi'] = 1
        folders[folder]['20160501_230030.avi'] = 1
        folders[folder]['20160501_150030.avi'] = 0
        args = {"enc": json.dumps(folders[folder])}

        with unittest.mock.patch('builtins.open', WRITE) as writer:
            self.progress.write_progress_folder(writer, args)

        self.assertEqual(WRITE.buffer, args['enc'])

    def test_read_last_file(self):
        folder = "record/20160501"
        folders = {}
        folders[folder] = self.progress.init_empty(folder)
        folders[folder]['20160501_220030.avi'] = 1
        folders[folder]['20160501_230030.avi'] = 1
        folders[folder]['20160501_150030.avi'] = 0
        self.progress.done_progress = folders
        self.assertDictEqual(self.progress.read_last_file(folder), folders[folder])
        self.progress.done_folders.append(folder)
        self.assertEqual(self.progress.read_last_file(folder), None)
        self.progress.done_folders = []
        self.progress.done_progress = {}
        self.assertEqual(self.progress.read_last_file(folder), None)

    def test_save_progress_for_unfinished(self):
        folder = "record/20160501"
        folders = {}
        folders[folder] = self.progress.init_empty(folder)
        folders[folder]['20160501_220030.avi'] = 1
        folders[folder]['20160501_230030.avi'] = 1
        folders[folder]['20160501_150030.avi'] = 0
        args = {"enc": json.dumps(folders[folder])}

        def mocked_open_write_file(path, writer, args):
            writer(WRITE, args)

        WRITE.open_write_file = mock.Mock(side_effect=mocked_open_write_file)

        with unittest.mock.patch('foscambackup.file_helper.open_write_file', WRITE.open_write_file):
            result = self.progress.save_progress_for_unfinished(folder)
        self.assertEqual(result, False)

        self.progress.done_progress = folders
        with unittest.mock.patch('foscambackup.file_helper.open_write_file', WRITE.open_write_file):
            result = self.progress.save_progress_for_unfinished(folder)
            self.assertEqual(result, True)
            self.assertEqual(WRITE.buffer, args['enc'])
