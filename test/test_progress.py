""" Test all Progress functions """
import json
import unittest
import unittest.mock as umock
from io import StringIO

import helper as test_helper
import foscambackup.helper as helper
from foscambackup.constant import Constant
from foscambackup.progress import Progress
from mocks import mock_file_helper


APPEND = mock_file_helper.APPEND
READ_STATE = mock_file_helper.READ_STATE
READ_S = mock_file_helper.READ_S
WRITE = mock_file_helper.WRITE
# mock file read
#@unittest.SkipTest
class TestProgress(unittest.TestCase):
    
    def setUp(self):
        self.progress = Progress("")
        #test_helper.log_to_stdout('Worker','info')

    def tearDown(self):
        APPEND.buffer = ""
        WRITE.buffer = ""

    @umock.patch('builtins.open', READ_STATE)
    def test_load_and_init(self):
        """ Test the load function"""
        read_file = READ_STATE.read()
        self.progress.load_and_init(read_file)
        progress_folder = json.loads(read_file.getvalue())
        self.assertDictEqual(self.progress.done_progress[progress_folder['path']], json.loads(read_file.getvalue()))

    def test_read_previous_state_file(self):
        """ Tested by test_load_and_init """
        pass

    @umock.patch('builtins.open', READ_S)
    def test_load_and_init_complete_folders(self):
        read_file = READ_S.read()
        path = 'record/20160501'
        self.progress.load_and_init_complete_folders(read_file)
        self.assertListEqual(self.progress.complete_folders, [path])
        self.assertDictEqual(self.progress.done_progress[path], {"done":1, "path":"record/20160501"})
        
    def test_read_state_file(self):
        """ Tested by test_load_and_init_complete_folders """
        pass

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
        self.progress.complete_folders.append(path)
        self.assertEqual(self.progress.check_done_folder("record", "20160501"), True)
        self.assertEqual(self.progress.check_done_folder("record", "20160502"), False)

    def test_is_max_files_reached(self):
        self.progress.max_files = 10
        self.progress.done_files = 10
        self.assertEqual(self.progress.is_max_files_reached(), True)
        # reinit
        self.progress.max_files = -1
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
        with umock.patch('foscambackup.file_helper.open_appendonly_file', APPEND):
            self.assertListEqual(self.progress.check_folder_done(), [folder])

    def test_write_to_newline(self):
        folder = "record/20160501"
        args = {"path": folder}

        with umock.patch('builtins.open', APPEND) as appender:
            self.progress.write_done_folder_to_newline(appender, args)

        self.assertEqual(APPEND.buffer, folder+"\n")

    def test_write_done_folder(self):
        """ write folder to state.log """
        foldername = "record/20160501"
        folder = {foldername: {"done":1, "path":foldername}}
        self.progress.done_progress[folder[foldername]['path']] = folder[foldername]
        with umock.patch('foscambackup.file_helper.open_appendonly_file', APPEND):
            self.progress.write_done_folder(folder[foldername], foldername)
        self.assertEqual(self.progress.done_progress, folder)
        self.assertEqual(self.progress.complete_folders, [folder[foldername]['path']])

    def test_save(self):
        """ Test saving of state file """
        with self.assertRaises(ValueError):
            self.progress.save()
        folder = "record/20160501"
        folders = {}
        folders[folder] = self.progress.init_empty(folder)
        folders[folder]['20160501_220030.avi'] = 1
        folders[folder]['20160501_230030.avi'] = 1
        folders[folder]['20160501_150030.avi'] = 0
        self.progress.done_progress = folders
        self.progress.cur_folder = folder
        print("WTFF")
        print(self.progress.cur_folder)
        with umock.patch('builtins.open', APPEND):
            self.assertEqual(self.progress.save(), True)

    def test_write_progress_folder(self):
        folder = "record/20160501"
        folders = {}
        folders[folder] = self.progress.init_empty(folder)
        folders[folder]['20160501_220030.avi'] = 1
        folders[folder]['20160501_230030.avi'] = 1
        folders[folder]['20160501_150030.avi'] = 0
        args = {"enc": json.dumps(folders[folder])}

        with umock.patch('builtins.open', WRITE) as writer:
            self.progress.write_progress_folder(writer, args)

        self.assertEqual(WRITE.buffer, args['enc'])

    def test_read_processed_folder(self):
        """ read progress """
        folder = "record/20160501"
        folders = {}
        folders[folder] = self.progress.init_empty(folder)
        folders[folder]['20160501_220030.avi'] = 1
        folders[folder]['20160501_230030.avi'] = 1
        folders[folder]['20160501_150030.avi'] = 0
        self.progress.done_progress = folders
        self.assertDictEqual(self.progress.read_last_processed_folder(folder), folders[folder])
        self.progress.complete_folders.append(folder)
        self.assertEqual(self.progress.read_last_processed_folder(folder), None)
        self.progress.complete_folders = []
        self.progress.done_progress = {}
        self.assertEqual(self.progress.read_last_processed_folder(folder), None)

    def test_save_progress_for_unfinished(self):
        """ save progress """
        folder = "record/20160501"
        folders = {}
        folders[folder] = self.progress.init_empty(folder)
        folders[folder]['20160501_220030.avi'] = 1
        folders[folder]['20160501_230030.avi'] = 1
        folders[folder]['20160501_150030.avi'] = 0
        args = {"enc": json.dumps(folders[folder])}

        def mocked_open_write_file(path, writer, args):
            writer(WRITE, args)

        WRITE.open_write_file = umock.Mock(side_effect=mocked_open_write_file)

        with umock.patch('foscambackup.file_helper.open_write_file', WRITE.open_write_file):
            result = self.progress.save_progress_for_unfinished(folder)
            self.assertEqual(result, False)

        self.progress.done_progress = folders
        with umock.patch('foscambackup.file_helper.open_write_file', WRITE.open_write_file):
            result = self.progress.save_progress_for_unfinished(folder)
            self.assertEqual(result, True)
            self.assertEqual(WRITE.buffer, args['enc'])
