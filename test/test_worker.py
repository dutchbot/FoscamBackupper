import os
import unittest
import unittest.mock as umock
from unittest.mock import call

import helper
from foscambackup.conf import Conf
from foscambackup.constant import Constant
from foscambackup.progress import Progress
from foscambackup.worker import Worker
from mocks import mock_worker
from mocks import mock_ftp

mode_record = {"wanted_files": Constant.wanted_files_record,
               "folder": Constant.record_folder, "int_mode": 0, 'separator': '_'}
mode_snap = {"wanted_files": Constant.wanted_files_snap,
             "folder": Constant.snap_folder, "int_mode": 1, 'separator': '-'}


class TestWorker(unittest.TestCase):

    def setUp(self):
        mock_worker.reset_mock()
        self.args = helper.get_args_obj()
        self.args['conf'] = Conf()
        self.progress = Progress()
        self.worker = Worker(mock_worker.conn, self.progress, self.args)
        #helper.log_to_stdout('Worker', 'info')

    def tearDown(self):
        mock_worker.reset_mock()

    def init_worker(self, args):
        """ Supply different args """
        self.worker = Worker(mock_worker.conn, self.progress, args)

    #@unittest.SkipTest
    def test_check_currently_recording(self):
        """ Test the behavior of setting the current_recording value to true/false """
        self.worker.check_currently_recording()
        self.assertEqual(self.args['conf'].currently_recording, True)
        mock_worker.conn.retrbinary = umock.Mock(
            side_effect=mock_worker.retrbinary_false, spec=str)
        self.worker = Worker(mock_worker.conn, self.progress, self.args)
        self.worker.check_currently_recording()
        self.assertEqual(self.args['conf'].currently_recording, False)

    #@unittest.SkipTest
    def test_read_sdrec_content(self):
        """ Test the behavior of setting the current_recording value to true/false """
        file_handle = bytes(helper.get_current_date_time_rounded(), 'ascii')
        self.worker.read_sdrec_content(file_handle)
        self.assertEqual(self.args['conf'].currently_recording, True)
        file_handle = bytes(
            helper.get_current_date_offset_day() + "_100000", 'ascii')
        self.worker.read_sdrec_content(file_handle)
        self.assertEqual(self.args['conf'].currently_recording, False)

    #@unittest.SkipTest
    def test_get_files(self):
        """  Test that the expected functions get called, and proper mode objects are used """
        result = []

        def get_footage(*args, **kwargs):
            result.append(args[0])

        def check_done_folders(*args, **kwargs):
            return True

        mocked_footage = umock.MagicMock(side_effect=get_footage)
        check_done = umock.MagicMock(side_effect=check_done_folders)

        # mock_worker.conn.reset_mock()

        with umock.patch('foscambackup.worker.Worker.get_footage', mocked_footage), \
                umock.patch('foscambackup.worker.Worker.check_done_folders', check_done):
            self.worker.get_files()

        calls = [call.mlsd(
            '/IPCamera'), call.retrbinary('RETR /IPCamera/.SdRec', self.worker.read_sdrec_content)]

        self.assertDictEqual(result[0], mode_record)
        self.assertDictEqual(result[1], mode_snap)
        self.assertEqual(check_done.called, True, "Called check_done_folders")
        self.assertListEqual(mock_worker.conn.method_calls,
                             calls, "Called check_currently_recording")

    def test_get_footage(self):
        # TODO:
        # want to test if folder recording is skipped
        # want to verify that the cur folder is set on progress object
        # done: assert number of files downloaded are correct.
        self.args['conf'].model = "FXXXXX_CEEEEEEEEEEE"  # verified with regex

        mock_worker.conn.mlsd.side_effect = mock_ftp.mlsd

        def makedirs(path):
            return ""

        def download_file(loc_info):
            import foscambackup.helper
            foscambackup.helper.verify_path(
                loc_info['abs_path'], loc_info['mode'])
            #print("Download called")
            return True
        download = umock.MagicMock()
        download.download_file = umock.MagicMock(side_effect=download_file)

        osmakedirs = umock.MagicMock()
        osmakedirs.makedirs = umock.MagicMock(side_effect=download_file)

        with umock.patch("foscambackup.worker.Worker.download_file", download.download_file), \
                umock.patch("os.makedirs", osmakedirs):
            # RECORDING
            file_handle = bytes(
                helper.get_current_date_time_rounded(), 'ascii')
            self.worker.read_sdrec_content(file_handle)
            self.worker.get_footage(mode_snap)
            self.assertEqual(self.worker.progress.done_files, 16)

            self.args['conf'].currently_recording = False
            self.worker.get_footage(mode_snap)
            self.assertEqual(self.worker.progress.done_files, 20)

    #@unittest.SkipTest
    def test_init_zip_folder(self):
        # verify initialized dict for given folder key
        self.worker.init_zip_folder("record/20160601")
        verify = {"record/20160601": {"zipped": 0,
                                      "remote_deleted": 0, "local_deleted": 0}}
        self.assertDictEqual(self.worker.folder_actions, verify)

    #@unittest.SkipTest
    def test_zip_local_files_folder(self):
        """ Verify correct paths are constructed while creating zipfile """
        import time
        self.args['output_path'] = "D:/output"
        self.init_worker(self.args)
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

        def S_ISDIR(mode):
            return 1

        def read(length):
            """BS"""
            return b'\x00\x01\x02\x03'

        def close():
            return True

        def copyfileobj(src, dest, length):
            return True

        class MockedStructure(bytes):
            def __enter__(self):
                return read

            def __exit__(self):
                pass
        ospath_listdir = umock.MagicMock(side_effect=listdir)
        ospath_exists = umock.MagicMock(side_effect=exist)
        os_stat = umock.MagicMock(side_effect=osstat, spec=os.stat)
        os_stat.st_mode = 1
        os_stat.st_mtime = time.time()
        os_stat.st_size = 5
        os_stat.S_ISDIR = umock.MagicMock(side_effect=S_ISDIR)
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
        shutil = umock.MagicMock()

        shutil.copyfileobj = umock.MagicMock(side_effect=copyfileobj)

        with umock.patch("os.listdir", ospath_listdir), \
                umock.patch("os.path.exists", ospath_exists), \
                umock.patch("os.path.isfile", isfile_mock), \
                umock.patch("os.stat", os_stat), \
                umock.patch("builtins.open", open_mocked), \
                umock.patch("io.open", open_mocked), \
                umock.patch("shutil.copyfileobj", shutil):
            self.worker.init_zip_folder(folder)
            self.worker.zip_local_files_folder(folder)

        verify_listdir = [call('D:/output/record/20170911')]
        self.assertListEqual(ospath_listdir.call_args_list, verify_listdir)
        verify_exists = [call('D:/output/record'),
                         call('D:/output/record/20170911')]
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

    #@unittest.SkipTest
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
        with umock.patch("foscambackup.helper.cleanup_directories", m_helper):
            self.worker.delete_local_folder(fullpath, folder)

        verify = {folder: {"zipped": 0, "remote_deleted": 0, "local_deleted": 1}}
        self.assertListEqual(m_helper.call_args_list, [
                             call('/output/record/20170101')])
        self.assertDictEqual(self.worker.folder_actions, verify)

    #@unittest.SkipTest
    def test_set_remote_deleted(self):
        """ Verify remote deleted value is set to 1 """
        folder = "record/20170101"
        self.worker.init_zip_folder(folder)  # important
        self.worker.set_remote_deleted(folder)

        verify = {folder: {"zipped": 0, "remote_deleted": 1, "local_deleted": 0}}
        self.assertDictEqual(self.worker.folder_actions, verify)

    #@unittest.SkipTest
    def test_get_remote_deleted(self):
        folder = "record/20170101"
        self.worker.init_zip_folder(folder)  # important

        self.assertEqual(self.worker.get_remote_deleted(folder), 0)
        self.worker.set_remote_deleted(folder)
        self.assertEqual(self.worker.get_remote_deleted(folder), 1)

    #@unittest.SkipTest
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

    #@unittest.SkipTest
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

    #@unittest.SkipTest
    def test_check_done_folders(self):
        def check_folders_done():
            return ['record/20170101', 'snap/20170101']

        def generic(folder):
            pass
        init_zip = umock.Mock(side_effect=generic)
        zip_and_delete = umock.Mock(side_effect=generic)
        check_folders = umock.Mock(side_effect=check_folders_done)
        with umock.patch("foscambackup.progress.Progress.check_folders_done", check_folders), \
                umock.patch("foscambackup.worker.Worker.init_zip_folder", init_zip), \
                umock.patch("foscambackup.worker.Worker.zip_and_delete", zip_and_delete):
            self.worker.check_done_folders()

        verify = [call('snap/20170101'), call('record/20170101')]
        self.assertListEqual(check_folders.call_args_list, [call()])
        self.assertListEqual(init_zip.call_args_list, verify)
        self.assertListEqual(zip_and_delete.call_args_list, verify)

    #@unittest.SkipTest
    def test_zip_and_delete(self):
        # TODO
        pass

    #@unittest.SkipTest
    def test_check_folder_state_delete(self):
        # TODO
        pass

    #@unittest.SkipTest
    def test_crawl_folder(self):
        # TODO
        pass

    #@unittest.SkipTest
    def test_crawl_files(self):
        # TODO
        pass

    #@unittest.SkipTest
    def test_retrieve_and_write_file(self):
        # TODO
        pass

    #@unittest.SkipTest
    def test_download_file(self):
        # TODO
        pass
