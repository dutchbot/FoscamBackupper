import os
import unittest
import unittest.mock as umock
import zipfile
from unittest.mock import call

import helper
from foscambackup.conf import Conf
from foscambackup.constant import Constant
from foscambackup.progress import Progress
from foscambackup.worker import Worker
from mocks import mock_worker


class TestWorker(unittest.TestCase):
    # Statics
    args = None
    conf = None
    worker = None

    # def setUp(self):
    #     args =  helper.get_args_obj()
    #     args["output_path"] = TestWorker.output_path
    #     helper.mock_dir(self.conf)
    #     self.args = args
    #     self.progress = Progress()
    #     self.worker = Worker(Connection(), self.progress, self.args)

    # def tearDown(self):
    #     helper.clear_log()

    # @staticmethod
    # def setUpClass():
    #     helper.log_to_stdout('Worker')
    #     TestWorker.conf =  helper.read_conf()

    # @staticmethod
    # def tearDownClass():
    #     MockFTPServer.cleanup_remote_directory()
    #     helper.cleanup_directories(TestWorker.output_path)

    # def test_worker_local_delete(self):
    #     """ Test local deletion of folder """
    #     # Important
    #     self.args["dry_run"] = False
    #     self.args["delete_local_f"] = True

    #     self.worker = Worker(Connection(), self.progress, self.args)

    #     mode_folder = "record"
    #     new_path, _ = helper.generate_downloaded_path(mode_folder, self.args)

    #     folder = mode_folder+new_path[-9:]
    #     self.worker.init_zip_folder(folder)
    #     self.worker.delete_local_folder(new_path, folder)

    #     self.assertFalse(os.path.isdir(new_path))

    # def test_worker_zipfile(self):
    #     """ Test zip local file functionality """
    #     self.args["dry_run"] = False
    #     self.args["zip_files"] = True

    #     mode_folder = "record"
    #     new_path, created_files = helper.generate_downloaded_path(mode_folder, self.args)

    #     splitted = new_path.split('/')
    #     folder = helper.construct_path(mode_folder, [splitted[len(splitted)-1]])
    #     self.worker.init_zip_folder(folder)
    #     self.worker.zip_local_files_folder(folder)
    #     zip_file_path = new_path+".zip"
    #     self.assertEqual(os.path.isfile(zip_file_path), True)
    #     zip_file = zipfile.ZipFile(zip_file_path)
    #     list_files = zip_file.namelist()
    #     self.assertListEqual(created_files, list_files)

    def test_log_debug(self):
        pass

    def test_log_info(self):
        pass

    def test_log_error(self):
        pass

    def test_check_currently_recording(self):
        """ Test the behavior of setting the current_recording value to true/false """
        args = helper.get_args_obj()
        args['conf'] = Conf()
        progress = Progress()
        worker = Worker(mock_worker.conn, progress, args)

        worker.check_currently_recording()
        self.assertEqual(worker.args['conf'].currently_recording, True)
        mock_worker.conn.retrbinary = umock.Mock(side_effect=mock_worker.retrbinary_false, spec=str)
        worker = Worker(mock_worker.conn, progress, args)
        worker.check_currently_recording()
        self.assertEqual(worker.args['conf'].currently_recording, False)

    def test_read_sdrec_content(self):
        """ Test the behavior of setting the current_recording value to true/false """
        args = helper.get_args_obj()
        args['conf'] = Conf()
        progress = Progress()
        worker = Worker(None, progress, args)

        file_handle = bytes(helper.get_current_date_time_rounded(),'ascii')
        worker.read_sdrec_content(file_handle)
        self.assertEqual(worker.args['conf'].currently_recording, True)
        file_handle = bytes(helper.get_current_date_offset_day()+"_100000",'ascii')
        worker.read_sdrec_content(file_handle)
        self.assertEqual(worker.args['conf'].currently_recording, False)

    def test_update_conf(self):
        pass

    def test_get_files(self):
        """  Test that the expected functions get called, and proper mode objects are used """
        mode_record = {"wanted_files": Constant.wanted_files_record,
        "folder": Constant.record_folder, "int_mode": 0}
        mode_snap = {"wanted_files": Constant.wanted_files_snap,
        "folder": Constant.snap_folder, "int_mode": 1}
        result = []
        def get_footage(*args, **kwargs):
            result.append(args[0])

        def check_done_folders(*args, **kwargs):
            return True

        mocked_footage = umock.MagicMock(side_effect = get_footage)
        check_done = umock.MagicMock(side_effect = check_done_folders)

        args = helper.get_args_obj()
        args['conf'] = Conf()
        progress = Progress()
        worker = Worker(mock_worker.conn, progress, args)

        mock_worker.conn.reset_mock()

        with umock.patch('foscambackup.worker.Worker.get_footage', mocked_footage), \
            umock.patch('foscambackup.worker.Worker.check_done_folders', check_done):
                worker.get_files()

        calls = [call.mlsd('/'), call.retrbinary('RETR .SdRec', worker.read_sdrec_content)]

        self.assertDictEqual(result[0], mode_record)
        self.assertDictEqual(result[1], mode_snap)
        self.assertEqual(check_done.called, True, "Called check_done_folders")
        self.assertListEqual(mock_worker.conn.method_calls, calls, "Called check_currently_recording")

    def test_get_footage(self):
        # want to test if folder recording is skipped
        # want to verify that the cur folder is set on progress object
        pass

    def test_init_zip_folder(self):
        # verify initialized dict for given folder key
        pass

    def test_zip_local_files_folder(self):
        pass

    def test_delete_local_folder(self):
        pass

    def test_set_remote_deleted(self):
        pass

    def test_get_remote_deleted(self):
        pass

    def test_recursive_delete(self):
        pass

    def test_delete_remote_folder(self):
        pass

    def test_check_done_folders(self):
        pass

    def test_zip_and_delete(self):
        pass

    def test_check_folder_state_delete(self):
        pass

    def test_crawl_folder(self):
        pass

    def test_crawl_files(self):
        pass

    def test_retrieve_and_write_file(self):
        pass

    def test_download_file(self):
        pass
