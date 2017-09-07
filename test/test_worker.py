import os
import unittest
import zipfile

from foscambackup.worker import Worker
from foscambackup.progress import Progress
from mock_server import MockFTPServer
import helper

class TestWorker(unittest.TestCase):
    args = None
    conf = None
    worker = None

    def setUp(self):
        args =  helper.get_args_obj()
        args["output_path"] = TestWorker.output_path
        helper.mock_dir(self.conf)
        self.args = args
        self.progress = Progress()
        self.worker = Worker(self.progress, self.args)

    def tearDown(self):
        helper.clear_log()

    @staticmethod
    def setUpClass():
        helper.log_to_stdout('Worker')
        TestWorker.conf =  helper.read_conf()

    @staticmethod
    def tearDownClass():
        MockFTPServer.cleanup_remote_directory()
        helper.cleanup_directories(TestWorker.output_path)

    def test_worker_local_delete(self):
        """ Test local deletion of folder """
        # Important
        self.args["dry_run"] = False
        self.args["delete_local_f"] = True

        self.worker = Worker(self.progress, self.args)

        mode_folder = "record"
        new_path, _ = helper.generate_downloaded_path(mode_folder, self.args)

        folder = mode_folder+new_path[-9:]
        self.worker.init_zip_folder(folder)
        self.worker.delete_local_folder(new_path, folder)

        self.assertFalse(os.path.isdir(new_path))

    def test_worker_zipfile(self):
        """ Test zip local file functionality """
        self.args["dry_run"] = False
        self.args["zip_files"] = True

        mode_folder = "record"
        new_path, created_files = helper.generate_downloaded_path(mode_folder, self.args)

        splitted = new_path.split('/')
        folder = helper.construct_path(mode_folder, [splitted[len(splitted)-1]])
        self.worker.init_zip_folder(folder)
        self.worker.zip_local_files_folder(folder)
        zip_file_path = new_path+".zip"
        self.assertEqual(os.path.isfile(zip_file_path), True)
        zip_file = zipfile.ZipFile(zip_file_path)
        list_files = zip_file.namelist()
        self.assertListEqual(created_files, list_files)