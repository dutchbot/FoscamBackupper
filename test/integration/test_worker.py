import os
import sys
import time
import logging
import shutil
import unittest

from ftplib import error_perm
from threading import Thread

from test.mocks import mock_server
from foscambackup.config import Config
from foscambackup.constant import Constant
from foscambackup.progress import Progress
from foscambackup.worker import Worker
import foscambackup.util.ftp_helper as ftp_helper
from test.util import helper

DELETE_TESTS = True

#TODO add test like we call from main.py..

class TestWorker(unittest.TestCase):
    """ Basically an integration / system test """
    thread = None
    testserver = None
    args = None
    conf = None
    worker = None
    connection = None
    output_path = ""
    mode = {"wanted_files": Constant.wanted_files_record,
        "folder": Constant.record_folder, "int_mode": 0, "separator":"_"}
    mode_snap = {"wanted_files": Constant.wanted_files_snap,
        "folder": Constant.snap_folder, "int_mode": 1, "separator":"-"}

    def setUp(self):
        args = helper.get_args_obj()
        args["output_path"] = TestWorker.output_path
        helper.mock_dir(self.conf)
        helper.mock_dir_offset_subdir(self.conf)
        helper.mock_dir_offset_parentdir(self.conf)
        self.args = args
        self.args['conf'] = self.conf

    def tearDown(self):
        ftp_helper.close_connection(self.connection)
        helper.clear_log()

    @staticmethod
    def setUpClass():
        #helper.log_to_stdout('Worker')
        TestWorker.conf =  helper.read_conf()
        TestWorker.testserver = mock_server.MockFTPServer()
        TestWorker.thread = Thread(
            target=TestWorker.testserver.start_ftp_server, args=(TestWorker.conf, ))
        TestWorker.thread.start()
        while not TestWorker.testserver.is_running():
            time.sleep(0.2)

    @staticmethod
    def tearDownClass():
        TestWorker.testserver.close()
        TestWorker.testserver.cleanup_remote_directory()
        helper.cleanup_directories(TestWorker.output_path)
        TestWorker.thread.join()

    
    def test_connection(self):
        """ Test for welcome message """
        self.init_worker()
        self.assertNotEqual(self.connection.getwelcome(), None)

    
    def test_delete_file(self):
        """ Verify that we can delete a file remotely """
        self.init_worker()
        created_dir = "test_dir"
        count_dir = 0
        dirs = self.connection.mlsd(facts=['type'])
        self.connection.mkd(created_dir)

        for dirkey, _ in dirs:
            count_dir += 1
            if dirkey == created_dir:
                self.connection.rmd(created_dir)

        after_dirs = self.connection.mlsd(facts=['type'])
        self.assertGreater(count_dir, len(list(after_dirs)))

    
    def test_retrieve_dir_contents(self):
        """ Get a list of files """
        #todo replace with functions used in worker
        self.init_worker()
        if len(self.get_list_of_files("record")) > 0 and len(self.get_list_of_files("snap")) > 0:
            assert True
        else:
            assert False

    
    def test_download_output_path(self):
        """ Verify that we can retrieve and write a file to a specific directory """
        time.sleep(2)
        self.init_worker()
        desc = {'type': 'file'}
        mode = self.mode
        m_folder = mode['folder']
        sub_dir = self.get_list_of_dirs(m_folder, True)
        parent_dir = self.get_list_of_dirs(m_folder)
        filename = self.get_list_of_files(m_folder)[0][0]

        # First set the correct working dir
        pdir = parent_dir+helper.slash()+sub_dir
        abs_path = helper.get_abs_path(self.conf, m_folder)
        abs_path = helper.construct_path(abs_path, [pdir, filename])
        loc_info = {'mode': mode, 'parent_dir': parent_dir + helper.slash() + sub_dir, 'abs_path': abs_path,
            'filename': filename, 'desc': desc}
        self.worker.retrieve_and_write_file(loc_info, Progress(pdir))
        verify_path = helper.construct_path(self.args['output_path'], [m_folder, parent_dir, filename])
        if os.path.exists(verify_path):
            assert True
        else:
            assert False

    
    def test_worker_recorded_footage_download(self):
        """ Test that we can download recorded footage """
        self.init_worker()
        folder = 'record'
        parent_dir = self.get_list_of_dirs(folder)
        filenames = self.get_list_of_files(folder)
        mode = self.mode
        self.worker.get_footage(mode)
        verify_path = helper.construct_path(self.args['output_path'], [folder, parent_dir])
        helper.verify_file_count(verify_path, filenames)

    
    def test_worker_recorded_footage_download_delete_local(self):
        """ Test that we can delete local folder """
        self.args["dry_run"] = False
        self.args['delete_local_f'] = True
        self.init_worker()
        folder = 'record'
        parent_dir = self.get_list_of_dirs(folder)
        filenames = self.get_list_of_files(folder)
        mode = self.mode
        self.worker.get_footage(mode)
        self.worker.check_folder_done(Progress("mock/me"))
        verify_path = helper.construct_path(self.args['output_path'], [folder, parent_dir])
        helper.verify_files_deleted(verify_path, filenames)

    
    def test_worker_snap_footage_download(self):
        """ Test that we can download snapshot footage """
        self.init_worker()
        folder = 'snap'
        parent_dir = self.get_list_of_dirs(folder)
        filenames = self.get_list_of_files(folder)
        mode = self.mode_snap
        self.worker.get_footage(mode)
        verify_path = helper.construct_path(self.args['output_path'], [folder, parent_dir])
        helper.verify_file_count(verify_path, filenames)

    
    def test_worker_snapandrecorded_footage_download(self):
        """ Test our main entry point for downloading both types of footage """
        self.init_worker()
        folder_snap = 'snap'
        folder_record = 'record'
        parent_dir_snap = self.get_list_of_dirs(folder_snap)
        filenames_snap = self.get_list_of_files(folder_snap)
        parent_dir_record = self.get_list_of_dirs(folder_record)
        filenames_record = self.get_list_of_files(folder_record)
        self.worker.get_files()
        verify_path_snap = helper.construct_path(self.args['output_path'], [folder_snap, parent_dir_snap])
        verify_path_record = helper.construct_path(self.args['output_path'], [folder_record, parent_dir_record])
        helper.verify_file_count(verify_path_snap, filenames_snap)
        helper.verify_file_count(verify_path_record, filenames_record)

    
    def test_worker_remote_delete(self):
        """ Test remote deletion of folder """
        if DELETE_TESTS:
            # Important
            mode = self.mode
            self.args['mode'] = mode
            self.args["dry_run"] = False
            self.args["delete_rm"] = True
            self.connection = ftp_helper.open_connection(self.conf)
            self.worker = Worker(self.connection, self.args)
            self.worker.get_footage(mode)

            for progress in self.worker.progress_objects:
                self.worker.check_folder_done(progress)
                abspath_parent = "/IPCamera/FXXXXXX_CXXXXXXXXXXX/" + progress.cur_folder
                result = self.check_parent_dir_deleted(abspath_parent)
                self.assertTrue(result)
        else:
            pass

    
    def test_worker_snapandrecorded_footage_download_delete_zip(self):
        """ Test our main entry point for downloading both types of footage """
        if DELETE_TESTS:
            self.args["dry_run"] = False
            self.args["delete_rm"] = True
            self.args['zip_files'] = True
            self.init_worker()
            folder_snap = 'snap'
            folder_record = 'record'
            parent_dir_snap = self.get_list_of_dirs(folder_snap)
            filenames_snap = self.get_list_of_files(folder_snap)
            parent_dir_record = self.get_list_of_dirs(folder_record)
            filenames_record = self.get_list_of_files(folder_record)
            self.worker.get_files()
            verify_path_snap = helper.construct_path(self.args['output_path'], [folder_snap, parent_dir_snap])
            verify_path_record = helper.construct_path(self.args['output_path'], [folder_record, parent_dir_record])
            helper.verify_file_count(verify_path_snap, filenames_snap)
            helper.verify_file_count(verify_path_record, filenames_record)
        else:
            pass

    
    def test_get_file_size(self):
        self.init_worker()
        abs_path = "/IPCamera/"+self.conf.model + "/snap/" + helper.get_current_date() + \
        "/" + helper.get_current_date_time_rounded(time.localtime(), "-") + \
        "/" + helper.get_current_date_time("-") + ".jpg"
        self.assertEqual(ftp_helper.size(self.connection, abs_path), 2048)

    """ Test helpers """

    def init_worker(self):
        self.connection = ftp_helper.open_connection(self.conf)
        self.worker = Worker(self.connection, self.args)

    def check_parent_dir_deleted(self, folder):
        return self.get_list_of_dirs(folder) is None

    def get_list_of_dirs(self, mode, subdir=False):
        path = helper.get_abs_path(self.conf, mode)
        list_dir = self.connection.mlsd(path)
        try:
            for dirname, _ in list_dir:
                if subdir:
                    subpath = path + helper.slash() + dirname
                    list_subdirs = self.connection.mlsd(subpath)
                    for subdirname, _ in list_subdirs:
                        return subdirname
                return dirname
            return None
        except error_perm as perm:
            if "501" in perm.__str__():
                return None

    def get_list_of_files(self, mode):
        path = helper.get_abs_path(self.conf, mode)
        list_dir = helper.mlsd(self.connection, path)
        for dirname, _ in list_dir:
            subpath = path + helper.slash() + dirname
            list_subdirs = self.connection.mlsd(subpath)
            for subdir, _ in list_subdirs:
                list_files = helper.mlsd(self.connection, subpath + helper.slash() + subdir)
                return list(list_files)
