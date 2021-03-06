import os
import time
import ftplib
import unittest
from io import StringIO
import unittest.mock as umock
from unittest.mock import call

import test.util.helper as helper
from foscambackup.config import Config
from foscambackup.constant import Constant
from foscambackup.progress import Progress
from foscambackup.worker import Worker
from test.mocks import mock_worker
from test.mocks import mock_ftp
from test.mocks import mock_file_helper

MODE_RECORD = {"wanted_files": Constant.wanted_files_record,
               "folder": Constant.record_folder, "int_mode": 0, 'separator': '_'}
MODE_SNAP = {"wanted_files": Constant.wanted_files_snap,
             "folder": Constant.snap_folder, "int_mode": 1, 'separator': '-'}
READ_S = mock_file_helper.READ_S

# TODO test multiple folders zipping and deleting locally and remotely.
# Use queue for done_folders?
# TODO test timeout with big files

class TestWorker(unittest.TestCase):

    FAKE_MODEL = "FXXXXX_CEEEEEEEEEEE"

    def setUp(self):
        mock_worker.reset_mock()
        self.args = helper.get_args_obj()
        self.args['conf'] = Config()
        self.worker = Worker(mock_worker.conn, self.args)
        #helper.log_to_stdout('Worker', 'info')

    def tearDown(self):
        mock_worker.reset_mock()

    def init_worker(self, args):
        """ Supply different args """
        self.worker = Worker(mock_worker.conn, args)

    def test_log_error(self):
        # Arrange
        logger = umock.MagicMock()
        logger.error = umock.MagicMock()
        expected = "fake error"

        # Act
        with umock.patch("foscambackup.worker.Worker.logger", logger):
            self.worker.log_error(expected)

        # Assert
        self.assertEqual([call(expected)], logger.error.call_args_list)
    
    def test_update_conf(self):
        # Arrange
        initial_config = Config()
        initial_config.host = "not_existing"

        # Act
        self.worker.update_conf(Config())

        # Assert
        self.assertNotEqual(initial_config, self.worker.conf)

    def test_check_currently_recording(self):
        """ Test the behavior of setting the current_recording value to true/false """
        self.worker.check_currently_recording()
        self.assertEqual(self.args['conf'].currently_recording, True)
        mock_worker.conn.retrbinary = umock.Mock(
            side_effect=mock_worker.retrbinary_false, spec=str)
        self.worker = Worker(mock_worker.conn, self.args)
        self.worker.check_currently_recording()
        self.assertEqual(self.args['conf'].currently_recording, False)

    def test_read_sdrec_content(self):
        """ Test the behavior of setting the current_recording value to true/false """
        file_handle = bytes(helper.get_current_date_time_rounded(time.localtime()), 'ascii')
        self.worker.read_sdrec_content(file_handle)
        self.assertEqual(self.args['conf'].currently_recording, True)
        file_handle = bytes(
            helper.get_current_date_offset_day() + "_100000", 'ascii')
        self.worker.read_sdrec_content(file_handle)
        self.assertEqual(self.args['conf'].currently_recording, False)

    def test_get_files(self):
        """  Test that the expected functions get called, and proper mode objects are used """
        result = []

        def get_footage(*args, **kwargs):
            result.append(args[0])

        def check_done_folders(*args, **kwargs):
            return True

        mocked_footage = umock.MagicMock(side_effect=get_footage)
        check_done = umock.MagicMock(side_effect=check_done_folders)

        with umock.patch('foscambackup.worker.Worker.get_footage', mocked_footage), \
                umock.patch('foscambackup.worker.Worker.check_folder_done', check_done):
            self.worker.get_files()

        calls = [call.mlsd(
            '/IPCamera'), call.retrbinary('RETR /IPCamera/.SdRec', self.worker.read_sdrec_content)]

        self.assertDictEqual(result[0], MODE_RECORD)
        self.assertDictEqual(result[1], MODE_SNAP)
        self.assertListEqual(mock_worker.conn.method_calls,
                             calls, "Called check_currently_recording")

    def test_get_files_mode_arguments(self):
        """  Test that the proper code paths are used """
        result = []

        def get_footage(*args, **kwargs):
            result.append(args[0])

        def check_done_folders(*args, **kwargs):
            return True

        mocked_footage = umock.MagicMock(side_effect=get_footage)
        check_done = umock.MagicMock(side_effect=check_done_folders)

        with umock.patch('foscambackup.worker.Worker.get_footage', mocked_footage), \
                umock.patch('foscambackup.worker.Worker.check_folder_done', check_done):
            self.worker.args['mode'] = 'record'
            self.worker.get_files()
            self.assertDictEqual(result[0], MODE_RECORD)
            self.worker.args['mode'] = 'snap'
            self.worker.get_files()
            self.assertDictEqual(result[1], MODE_SNAP)

    def test_get_footage(self):
        self.args['conf'].model = "FXXXXX_CEEEEEEEEEEE"

        mock_worker.conn.mlsd.side_effect = mock_ftp.mlsd

        def makedirs(path):
            return ""

        def download_file(loc_info):
            import foscambackup.util.helper
            foscambackup.util.helper.verify_path(
                loc_info['abs_path'], loc_info['mode'])
            return True
        download = umock.MagicMock()
        download.download_file = umock.MagicMock(side_effect=download_file)

        osmakedirs = umock.MagicMock()
        osmakedirs.makedirs = umock.MagicMock(side_effect=makedirs)
        osmakedirs.isfile = umock.MagicMock(side_effect=makedirs)
        progress = Progress("record/20160501")
        progress.done_progress = {"done": 0, "path":"record/20160501"}
        mock_open = umock.MagicMock(name="open",return_value=[progress], spec=str)

        with umock.patch("foscambackup.worker.Worker.download_file", download.download_file), \
                umock.patch("os.makedirs", osmakedirs), \
                umock.patch("os.path.isfile", osmakedirs), \
                umock.patch("foscambackup.util.file_helper.open_readonly_file", mock_open), \
                umock.patch("foscambackup.util.file_helper.open_appendonly_file", mock_file_helper.APPEND):
            # RECORDING
            file_handle = bytes(
                helper.get_current_date_time_rounded(time.localtime()), 'ascii')
            self.worker.read_sdrec_content(file_handle)
            self.worker.get_footage(MODE_SNAP)
            self.assertEqual(self.worker.progress_objects[0].done_files, 4)
            self.assertEqual(self.worker.progress_objects[1].done_files, 4)
            self.assertEqual(self.worker.progress_objects[2].done_files, 4)
            self.assertEqual(self.worker.progress_objects[3].done_files, 4)

            self.args['conf'].currently_recording = False
            self.worker.get_footage(MODE_SNAP)
            self.assertEqual(self.worker.progress_objects[0].done_files, 4)
            self.assertEqual(self.worker.progress_objects[1].done_files, 4)
            self.assertEqual(self.worker.progress_objects[2].done_files, 4)
            self.assertEqual(self.worker.progress_objects[3].done_files, 4)
            self.assertEqual(self.worker.progress_objects[4].done_files, 4)

    def test_get_footage_skip_folder(self):
        self.args['conf'].model = "FXXXXX_CEEEEEEEEEEE"

        mock_worker.conn.mlsd.side_effect = mock_ftp.mlsd

        def makedirs(path):
            return ""

        def download_file(loc_info):
            import foscambackup.util.helper
            foscambackup.util.helper.verify_path(
                loc_info['abs_path'], loc_info['mode'])
            return True

        download = umock.MagicMock()
        download.download_file = umock.MagicMock(side_effect=download_file)

        osmakedirs = umock.MagicMock()
        osmakedirs.makedirs = umock.MagicMock(side_effect=makedirs)
        osmakedirs.isfile = umock.MagicMock(side_effect=makedirs)

        log_info = umock.MagicMock()

        progress1 = Progress("snap/20170101")
        progress1.done_progress = {"done": 1,"path":"snap/20170101", "files": { "12345,jpg":1 }}
        progress2 = Progress("snap/20170102")
        progress2.done_progress = {"done": 0,"path":"snap/20170102", "files":{ "12345,jpg":1 }}
        mock_open = umock.MagicMock(name="open",return_value=[progress1, progress2], spec=str)
        with umock.patch("foscambackup.worker.Worker.download_file", download.download_file), \
            umock.patch("foscambackup.worker.Worker.log_info", log_info), \
            umock.patch("os.makedirs", osmakedirs), \
            umock.patch("os.path.isfile", osmakedirs), \
            umock.patch("foscambackup.util.file_helper.open_readonly_file", mock_open), \
            umock.patch("foscambackup.util.file_helper.open_appendonly_file", mock_file_helper.APPEND):
                local_time = time.localtime()
                file_handle = bytes(helper.get_current_date_time_rounded(local_time), 'ascii')
                self.worker.read_sdrec_content(file_handle)
                self.worker.get_footage(MODE_SNAP)
                self.assertIn(call("Skipping current date, because currently recording."), log_info.call_args_list)
                self.assertIn(call("Skipping current recording folder: 20170101"), log_info.call_args_list)
                self.assertIn(call("skipping folder because already done"), log_info.call_args_list)

    def test_init_zip_folder(self):
        """ verify initialized dict for given folder key """
        self.worker.init_zip_folder("record/20160601")
        verify = {"record/20160601": {"zipped": 0,
                                      "remote_deleted": 0, "local_deleted": 0}}
        self.assertDictEqual(self.worker.folder_actions, verify)

    def test_zip_local_files_folder(self):
        """ Verify correct paths are constructed while creating zipfile """
        folder = "record/20170911"

        def write(*args, **kwargs):
            return len(args)  # offset count?

        def exist(*args, **kwargs):
            return True

        def isfile(*args, **kwargs):
            return False

        def listdir(*args, **kwargs):
            yield "12345.avi"
            yield "34562.avi"

        def osstat(*args, **kwargs):
            return os_stat

        def s_isdir(mode):
            return 1

        def read(length):
            """BS"""
            return b'\x00\x01\x02\x03'

        def close():
            return True

        def copyfileobj(src, dest, length):
            return True

        def makedirs(path):
            return ""

        class MockedStructure(bytes):
            def __enter__(self):
                return read

            def __exit__(self, exc_type, exc_value, tb):
                pass
        ospath_listdir = umock.MagicMock(side_effect=listdir)
        ospath_exists = umock.MagicMock(side_effect=exist)
        os_stat = umock.MagicMock(side_effect=osstat, spec=os.stat)
        os_stat.st_mode = 1
        os_stat.st_mtime = time.time()
        os_stat.st_size = 5
        os_stat.S_ISDIR = umock.MagicMock(side_effect=s_isdir)
        read_obj = umock.MagicMock()
        read_obj.read = read
        zipwriter = umock.MagicMock(spec=MockedStructure)
        zipwriter.write = write
        zipwriter.close = close
        zipwriter.flush = close
        isfile_mock = umock.MagicMock(
            name="os.path.isfile", side_effect=isfile)
        open_mocked = umock.MagicMock(name="open", return_value=zipwriter)
        open_mocked.write = umock.MagicMock(name="write", side_effect=write)
        open_mocked.header_offset = 10
        open_mocked.buffer = str()

        osmakedirs = umock.MagicMock()
        osmakedirs.makedirs = umock.MagicMock(side_effect=makedirs)
        osmakedirs.mkdir = umock.MagicMock()

        shutil = umock.MagicMock()
        shutil.copyfileobj = umock.MagicMock(side_effect=copyfileobj)

        with umock.patch("os.listdir", ospath_listdir), \
                umock.patch("os.path.exists", ospath_exists), \
                umock.patch("os.path.isfile", isfile_mock), \
                umock.patch("os.stat", os_stat), \
                umock.patch("builtins.open", open_mocked), \
                umock.patch("io.open", open_mocked), \
                umock.patch("os.mkdir", osmakedirs.mkdir), \
                umock.patch("os.makedirs", osmakedirs.makedirs), \
                umock.patch("shutil.copyfileobj", shutil):
                    self.args['output_path'] = "D:/output"
                    self.init_worker(self.args)
                    self.worker.init_zip_folder(folder)
                    self.worker.zip_local_files_folder(folder)

        verify_listdir = [call('D:/output/record/20170911')]
        self.assertListEqual(ospath_listdir.call_args_list, verify_listdir)
        verify_exists = [call('D:/output'), call('D:/output/record'), call('D:/output/record/20170911')]
        self.assertListEqual(ospath_exists.call_args_list, verify_exists)
        caller = [call('D:/output/record/20170911/12345.avi'),
                  call('D:/output/record/20170911/34562.avi')]
        self.assertListEqual(os_stat.call_args_list, caller)
        verify_isfile = [call('D:/output/record/20170911.zip')]
        self.assertListEqual(isfile_mock.call_args_list, verify_isfile)
        verify_open_mock = [call('D:/output/record/20170911.zip', 'w+b'),
                            call('D:/output/record/20170911/12345.avi', 'rb'),
                            call('D:/output/record/20170911/34562.avi', 'rb')]
        self.assertListEqual(open_mocked.call_args_list, verify_open_mock)

    def test_delete_local_folder(self):
        # verify cleanup directories is called
        # verify folder_action local_deleted is set to True
        def delete_local(fullpath):
            return True
        m_helper = umock.MagicMock('helper')
        m_helper.cleanup_directories = umock.MagicMock(
            side_effect=delete_local)
        fullpath = "/output/record/20170101"
        folder = "record/20170101"
        self.worker.init_zip_folder(folder)  # important
        with umock.patch("foscambackup.util.helper.cleanup_directories", m_helper):
            self.worker.delete_local_folder(fullpath, folder)

        verify = {folder: {"zipped": 0, "remote_deleted": 0, "local_deleted": 1}}
        self.assertListEqual(m_helper.call_args_list, [call('/output/record/20170101')])
        self.assertDictEqual(self.worker.folder_actions, verify)
   
    def test_set_remote_deleted(self):
        """ Verify remote deleted value is set to 1 """
        folder = "record/20170101"
        self.worker.init_zip_folder(folder)  # important
        self.worker.set_remote_deleted(folder)

        verify = {folder: {"zipped": 0, "remote_deleted": 1, "local_deleted": 0}}
        self.assertDictEqual(self.worker.folder_actions, verify)

    def test_get_remote_deleted(self):
        folder = "record/20170101"
        self.worker.init_zip_folder(folder)  # important

        self.assertEqual(self.worker.get_remote_deleted(folder), 0)
        self.worker.set_remote_deleted(folder)
        self.assertEqual(self.worker.get_remote_deleted(folder), 1)

    def test_recursive_delete(self):
        fullpath = "/IPCamera/FXXXXX_CEEEEEEEEEEE/snap/20170101"
        folder = "snap/20170101"

        mock_worker.conn.mlsd.side_effect = mock_ftp.mlsd
        mock_worker.conn.delete.side_effect = mock_ftp.delete
        mock_worker.conn.rmd.side_effect = mock_ftp.rmd

        self.worker.init_zip_folder(folder)
        self.worker.recursive_delete(fullpath, folder)

        top_subdirs = [call(fullpath),
                       call(fullpath + '/20170101-120000'),
                       call(fullpath + '/20170101-140000'),
                       call(fullpath + '/20170101-160000'),
                       call(fullpath + '/20170101-170000')]
        delete_files = [call(fullpath + '/20170101-120000/20170101-120000.jpg'),
                        call(fullpath + '/20170101-140000/20170101-140000.jpg'),
                        call(fullpath + '/20170101-160000/20170101-160000.jpg'),
                        call(fullpath + '/20170101-170000/20170101-170000.jpg')]

        self.assertListEqual(mock_worker.conn.mlsd.call_args_list, top_subdirs)
        self.assertListEqual(
            mock_worker.conn.delete.call_args_list, delete_files)
        deleted_dirs = top_subdirs
        tmp = deleted_dirs[0]
        deleted_dirs.remove(tmp)
        deleted_dirs.append(tmp)
        self.assertListEqual(
            mock_worker.conn.rmd.call_args_list, deleted_dirs)
        self.assertEqual(self.worker.get_remote_deleted(folder), 1)

    def test_recursive_delete_exceptions(self):
        fullpath = "/IPCamera/FXXXXX_CEEEEEEEEEEE/snap/20170101"
        folder = "snap/20170101"

        log_info = umock.MagicMock()
        log_error = umock.MagicMock()

        with umock.patch("foscambackup.worker.Worker.log_error", log_error), \
            umock.patch("foscambackup.util.ftp_helper.mlsd", umock.MagicMock(side_effect=ftplib.error_perm)):
                self.worker.recursive_delete(fullpath, folder)
                self.assertListEqual(log_error.call_args_list, [call("No such file or directory! Tried: " + fullpath)])

        with umock.patch("foscambackup.worker.Worker.log_info", log_info), \
            umock.patch("foscambackup.util.ftp_helper.mlsd", umock.MagicMock(side_effect=ftplib.error_temp)):
                self.worker.recursive_delete(fullpath, folder)
                self.assertListEqual(log_info.call_args_list, [call("Recursive strategy to clean folder"), call("Timeout when deleting..")])

    def test_delete_remote_folder(self):
        fullpath = "/IPCamera/FXXXXX_CEEEEEEEEEEE/snap/20170101"
        folder = "snap/20170101"
        self.worker.args['dry_run'] = 0
        self.worker.args['delete_rm'] = 1

        mock_worker.conn.mlsd.side_effect = mock_ftp.mlsd
        mock_worker.conn.delete.side_effect = mock_ftp.delete
        mock_worker.conn.rmd.side_effect = mock_ftp.rmd_raise

        delete_dirs = [
            call(fullpath),
            call(fullpath + '/20170101-120000'),
            call(fullpath + '/20170101-140000'),
            call(fullpath + '/20170101-160000'),
            call(fullpath + '/20170101-170000'),
            call(fullpath)]

        delete_dir = [call(fullpath)]

        self.worker.init_zip_folder(folder)
        self.worker.delete_remote_folder(fullpath, folder)
        self.assertListEqual(mock_worker.conn.rmd.call_args_list,
                             delete_dirs, msg="Recursive delete path")
        # reset
        self.worker.folder_actions[folder]['remote_deleted'] = 0
        mock_worker.reset_mock()
        mock_worker.conn.mlsd.side_effect = mock_ftp.mlsd
        mock_worker.conn.delete.side_effect = mock_ftp.delete
        mock_worker.conn.rmd.side_effect = mock_ftp.rmd
        self.worker.delete_remote_folder(fullpath, folder)
        self.assertListEqual(mock_worker.conn.rmd.call_args_list,
                             delete_dir, msg="Normal delete path")
        self.assertEqual(self.worker.get_remote_deleted(folder), 1)

    def test_delete_remote_folder_exceptions(self):
        fullpath = "/IPCamera/FXXXXX_CEEEEEEEEEEE/snap/20170101"
        folder = "snap/20170101"
        self.worker.args['dry_run'] = 0
        self.worker.args['delete_rm'] = 1

        mock_worker.conn.rmd = umock.MagicMock(side_effect=ftplib.error_temp("Connection timeout."))
        ftp_helper = umock.MagicMock()
        ftp_helper.open_connection = umock.MagicMock()
        log_error = umock.MagicMock()
        delete_remote_folder = umock.MagicMock()

        original_delete_remote_folder = self.worker.delete_remote_folder
        with umock.patch("foscambackup.util.ftp_helper.open_connection", ftp_helper.open_connection), \
            umock.patch("foscambackup.util.ftp_helper.close_connection", ftp_helper.close_connection), \
            umock.patch("foscambackup.worker.Worker.log_error", log_error), \
            umock.patch("foscambackup.worker.Worker.delete_remote_folder", delete_remote_folder):
                original_delete_remote_folder(fullpath, folder)
                # assert key error
                self.assertListEqual(log_error.call_args_list, [call("Folder key was not initialized in zipped folders list!")])
                self.assertListEqual(delete_remote_folder.call_args_list, [call(fullpath, folder)])

                ftp_helper.reset_mock()
                log_error.reset_mock()
                delete_remote_folder.reset_mock()
                log_info = umock.MagicMock()
                log_debug = umock.MagicMock()

                with umock.patch("foscambackup.worker.Worker.get_remote_deleted", umock.MagicMock(return_value=0)), \
                    umock.patch("foscambackup.worker.Worker.log_debug", log_debug), \
                    umock.patch("foscambackup.worker.Worker.log_info", log_info):
                        original_delete_remote_folder(fullpath, folder)
                        self.assertListEqual([call("Connection timeout.")], log_debug.call_args_list)
                        self.assertListEqual([call(mock_worker.conn)], ftp_helper.close_connection.call_args_list)
                        self.assertListEqual([call(self.worker.args['conf'])], ftp_helper.open_connection.call_args_list)
                        self.assertListEqual([call("Deleting remote folder.."), 
                                                call(fullpath), 
                                                call("Timeout so reopening connection right now .."),
                                                call("Reinitate deletion of remote folder.")], log_info.call_args_list)
                        self.assertListEqual(delete_remote_folder.call_args_list, [call(fullpath, folder)])

    def test_delete_remote_folder_dry_run(self):
        fullpath = "/IPCamera/FXXXXX_CEEEEEEEEEEE/snap/20170101"
        folder = "snap/20170101"
        self.worker.args['dry_run'] = 1
        self.worker.args['delete_rm'] = 1

        log_info = umock.MagicMock()
        set_remote_deleted = umock.MagicMock()

        with umock.patch("foscambackup.worker.Worker.get_remote_deleted", umock.MagicMock(return_value=0)), \
            umock.patch("foscambackup.worker.Worker.set_remote_deleted", set_remote_deleted), \
            umock.patch("foscambackup.worker.Worker.log_info", log_info):
                self.worker.delete_remote_folder(fullpath, folder)
                self.assertListEqual([call("Not deleting remote folder")], log_info.call_args_list)
                self.assertEqual(set_remote_deleted.call_count , 1)

    def test_check_done_folders(self):
        def check_done_folder():
            return True

        def generic(folder):
            pass
        init_zip = umock.Mock(side_effect=generic)
        zip_and_delete = umock.Mock(side_effect=generic)
        check_done = umock.Mock(side_effect=check_done_folder)
        with umock.patch("foscambackup.progress.Progress.check_done_folder", check_done), \
                umock.patch("foscambackup.worker.Worker.init_zip_folder", init_zip), \
                umock.patch("foscambackup.worker.Worker.zip_and_delete", zip_and_delete):
            self.worker.check_folder_done(Progress("snap/20170101"))

        verify = [call('snap/20170101')]
        self.assertListEqual(check_done.call_args_list, [call()])
        self.assertListEqual(zip_and_delete.call_args_list, verify)

    def test_load_and_init_from_previous(self):
        read_file = READ_S.read()
        path = 'record/20160501'
        list_of_files = []

        with umock.patch('foscambackup.progress.Progress.read_previous_progress_file',):
            list_of_files = self.worker.load_and_init_from_previous(read_file)
            self.assertDictEqual(list_of_files[0].done_progress, {"done":0, "path":path, "files":{}})
  
    def test_zip_and_delete(self):
        """ Verify the logic, actual deletion and zipping should be tested already. """
        def clean_folder(folder):
            return folder

        def delete(state, callback):
            pass
        folder = "record/20170101"
        clean = umock.Mock(side_effect=clean_folder)
        delete = umock.Mock(side_effect=delete)
        verify_delete = [call({'action_key': 'local_deleted', 'arg_key': 'delete_local_f', 'folder': 'record/20170101', 'fullpath': '/record/20170101'}, self.worker.delete_local_folder),
                         call({'action_key': 'remote_deleted', 'arg_key': 'delete_rm', 'folder': 'record/20170101', 'fullpath': '/IPCamera/FXXXXX_CEEEEEEEEEEE/record/20170101'}, self.worker.delete_remote_folder)]
        with umock.patch("foscambackup.util.helper.clean_folder_path", clean), \
                umock.patch("foscambackup.worker.Worker.check_folder_state_delete", delete):
            self.worker.init_zip_folder(folder)
            with self.assertRaises(ValueError):
                self.worker.zip_and_delete(folder)
            clean.reset_mock(side_effect=False)
            delete.reset_mock(side_effect=False)
            self.worker.conf.model = self.FAKE_MODEL
            self.worker.zip_and_delete(folder)
            self.assertListEqual(clean.call_args_list, [call(folder)])
            self.assertListEqual(delete.call_args_list, verify_delete)

    def test_check_folder_state_delete(self):
        def delete_method(fullpath, folder):
            self.worker.set_remote_deleted(folder)
            pass
        folder = "record/20170101"
        fullpath = "/IPCamera/FXXXXX_CEEEEEEEEEEE/snap/20170101"
        delete_state = {'action_key': 'remote_deleted',
                        'arg_key': 'delete_rm', 'folder': folder, 'fullpath': fullpath}
        callback = umock.MagicMock(side_effect=delete_method)
        self.args['dry_run'] = True
        self.args['delete_rm'] = True
        self.worker.init_zip_folder(folder)
        self.worker.check_folder_state_delete(delete_state, callback)
        self.assertListEqual(callback.call_args_list, [])
        self.assertTrue(self.worker.get_remote_deleted(folder), 1)

        # non dry run code path
        self.worker.args['dry_run'] = False
        self.worker.folder_actions[folder]['remote_deleted'] = 0
        self.worker.check_folder_state_delete(delete_state, callback)
        self.assertListEqual(callback.call_args_list, [call(
            '/IPCamera/FXXXXX_CEEEEEEEEEEE/snap/20170101', 'record/20170101')])
        self.assertTrue(self.worker.get_remote_deleted(folder), 1)
    
    def test_crawl_folder(self):
        # count recursion and calls to craw_files.
        mock_worker.conn.mlsd.side_effect = mock_ftp.mlsd2
        self.worker.conf.model = "FXXXXX_CEEEEEEEEEEE"
        parent = "20170101"
        parent_path = "/IPCamera/FXXXXX_CEEEEEEEEEEE/snap/20170101"
        file_list = mock_worker.conn.mlsd(
            "/IPCamera/FXXXXX_CEEEEEEEEEEE/snap/20170101")

        def permit(arg0, arg1):
            pass

        crawl = umock.MagicMock(side_effect=permit)

        with umock.patch("foscambackup.worker.Worker.crawl_files", crawl):
            instance = Progress("snap/20170101")
            self.worker.crawl_folder(file_list, MODE_SNAP, instance, parent)
            file_list = ['20170101-120000.jpg', '20170101-140000.jpg',
                         '20170101-160000.jpg', '20170101-170000.jpg']
            verify_list = []
            for filename in file_list:
                subfolder = filename
                _type = "dir"
                if len(filename) > 2:
                    subfolder = filename[:-4]
                    _type = 'file'
                verify_list.append(call({
                    'mode': MODE_SNAP,
                    'parent_dir': '20170101',
                    'abs_path': parent_path + "/" + subfolder + "/" + filename,
                    'filename': filename,
                    'desc': {'type': _type}}, instance))
            self.assertListEqual(crawl.call_args_list, verify_list,
                                 msg="Failed to verify the calls")

    def test_crawl_folder_max_files(self):
        # count recursion and calls to craw_files.
        self.worker.conf.model = "FXXXXX_CEEEEEEEEEEE"
        parent = "20170101"
        subdir = {"subdirs":["201701011500"], "path":"","current":"20170101"}
        file_list = [("201701011500", {'type': 'dir'})]

        progress = umock.MagicMock()
        progress.is_max_files_reached = umock.MagicMock(return_value = True)
        progress.save_progress = umock.MagicMock()
        exit_mock = umock.MagicMock()

        with umock.patch("foscambackup.progress.Progress.is_max_files_reached", progress.is_max_files_reached), \
            umock.patch("foscambackup.progress.Progress.save", progress.save_progress), \
            umock.patch("sys.exit", exit_mock):
                instance = Progress("snap/20170101")
                self.worker.crawl_folder(file_list, MODE_SNAP, instance, parent, subdir)
                self.assertEqual(progress.is_max_files_reached.call_count, 1)
                self.assertEqual(progress.save_progress.call_count, 1)
                self.assertEqual(exit_mock.call_count, 1)

    def test_download_file(self):
        loc_info = {'mode':'snap', 'parent_dir': "20170101", 'abs_path': "output\\b", 'filename': "test.jpg", 'desc':"file", 'folderpath':""}

        log_debug = umock.MagicMock()
        log_error = umock.MagicMock()
        mlsd = umock.MagicMock(return_value=["aad.jpg"])

        with umock.patch("foscambackup.worker.Worker.log_debug", log_debug), \
            umock.patch("foscambackup.worker.Worker.log_error", log_error), \
            umock.patch("foscambackup.util.ftp_helper.mlsd", mlsd):
            
            with umock.patch("foscambackup.util.helper.verify_path", umock.MagicMock(side_effect=ftplib.error_perm("550 denied"))):
                self.worker.download_file(loc_info)
                self.assertListEqual([call("Tried path: " + loc_info['abs_path']), 
                                    call("Tried path: " + str(mlsd.return_value)),
                                    call(loc_info['abs_path']),
                                    call("Retrieve and write file: " +loc_info['filename'] + " " + "550 denied")], log_error.call_args_list)

            log_error.reset_mock()
            log_debug.reset_mock()

            with umock.patch("foscambackup.util.helper.verify_path", umock.MagicMock(side_effect=ValueError("incorrect value"))):
                self.worker.download_file(loc_info)
                self.assertListEqual([call(loc_info['abs_path'] + " : " + "incorrect value")], log_error.call_args_list)
            
            open_connection = umock.MagicMock()
            download_file = umock.MagicMock()
            delete_file = umock.MagicMock()
            log_error.reset_mock()
            log_debug.reset_mock()

            original_download_file = self.worker.download_file

            with umock.patch("foscambackup.util.helper.verify_path", umock.MagicMock()), \
                umock.patch("foscambackup.worker.Worker.log_info", umock.MagicMock()), \
                umock.patch("builtins.open", umock.MagicMock()), \
                umock.patch("foscambackup.util.ftp_helper.size", umock.MagicMock()), \
                umock.patch("foscambackup.util.ftp_helper.open_connection", open_connection), \
                umock.patch("foscambackup.util.ftp_helper.retr", umock.MagicMock(side_effect=EOFError)), \
                umock.patch("foscambackup.util.ftp_helper.create_retrcmd", umock.MagicMock()), \
                umock.patch("foscambackup.download_file_tracker.DownloadFileTracker.write_to_file", umock.MagicMock()), \
                umock.patch("foscambackup.download_file_tracker.DownloadFileTracker.delete_file", delete_file), \
                umock.patch("foscambackup.worker.Worker.download_file", download_file):
                    original_download_file(loc_info)
                    self.assertEqual(open_connection.called, True)
                    self.assertEqual(delete_file.called, True)
                    self.assertEqual(download_file.called, True)
