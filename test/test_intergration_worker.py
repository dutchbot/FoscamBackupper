import os
import sys
import time
import logging
import shutil
import unittest

from ftplib import error_perm
from threading import Thread

import mock_server
from foscambackup.conf import Conf
from foscambackup.constant import Constant
from foscambackup.progress import Progress
from foscambackup.worker import Worker
import helper

class TestIntergrationWorker(unittest.TestCase):
    """ Basically an intergration / system test """
    thread = None
    testserver = None
    args = None
    conf = None
    worker = None
    connection = None

    def setUp(self):
        args =  helper.get_args_obj()
        args["output_path"] = TestIntergrationWorker.output_path
        helper.mock_dir(self.conf)
        self.args = args
        self.progress = Progress()

    def tearDown(self):
        helper.close_connection(self.connection)
        helper.clear_log()

    @staticmethod
    def setUpClass():
        helper.log_to_stdout('Worker')
        TestIntergrationWorker.conf =  helper.read_conf()
        TestIntergrationWorker.testserver = mock_server.MockFTPServer()
        TestIntergrationWorker.thread = Thread(
            target=TestIntergrationWorker.testserver.start_ftp_server, args=(TestIntergrationWorker.conf, ))
        TestIntergrationWorker.thread.start()
        while not TestIntergrationWorker.testserver.is_running():
            print("waiting")
            time.sleep(0.2)

    @staticmethod
    def tearDownClass():
        TestIntergrationWorker.testserver.close()
        TestIntergrationWorker.testserver.cleanup_remote_directory()
        helper.cleanup_directories(TestIntergrationWorker.output_path)
        TestIntergrationWorker.thread.join()

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
            if(dirkey == created_dir):
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
        self.init_worker()
        mode = {"wanted_files": Constant.wanted_files_record,
                "folder": Constant.record_folder, "int_mode": 0}
        desc = {'type': 'file'}
        m_folder = mode['folder']
        sub_dir = self.get_list_of_dirs(m_folder, True)
        parent_dir = self.get_list_of_dirs(m_folder)
        filename = self.get_list_of_files(m_folder)[0][0]

        # First set the correct working dir
        pdir = parent_dir+"/"+sub_dir
        abs_path = helper.get_abs_path(self.conf, m_folder)
        abs_path = helper.construct_path(abs_path,[pdir,filename])
        loc_info = {'mode': mode, 'parent_dir': parent_dir+"/"+sub_dir,'abs_path': abs_path,
            'filename': filename, 'desc': desc}
        self.worker.retrieve_and_write_file(self.connection,loc_info)
        verify_path = helper.construct_path(self.args['output_path'],[m_folder,parent_dir,filename])
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
        self.worker.get_recorded_footage(self.connection)
        verify_path = helper.construct_path(self.args['output_path'],[folder,parent_dir])
        helper.verify_file_count(verify_path,filenames)
    
    def test_worker_snap_footage_download(self):
        """ Test that we can download snapshot footage """
        self.init_worker()
        folder = 'snap'
        parent_dir = self.get_list_of_dirs(folder)
        filenames = self.get_list_of_files(folder)
        self.worker.get_snapshot_footage(self.connection)
        verify_path = helper.construct_path(self.args['output_path'],[folder,parent_dir])
        helper.verify_file_count(verify_path,filenames)

    def test_worker_snapandrecorded_footage_download(self):
        """ Test our main entry point for downloading both types of footage """
        self.init_worker()
        folder_snap = 'snap'
        folder_record = 'record'
        parent_dir_snap = self.get_list_of_dirs(folder_snap)
        filenames_snap = self.get_list_of_files(folder_snap)
        parent_dir_record = self.get_list_of_dirs(folder_record)
        filenames_record = self.get_list_of_files(folder_record)
        self.worker.get_files(self.connection)
        verify_path_snap = helper.construct_path(self.args['output_path'],[folder_snap,parent_dir_snap])
        verify_path_record = helper.construct_path(self.args['output_path'],[folder_record,parent_dir_record])
        helper.verify_file_count(verify_path_snap,filenames_snap)
        helper.verify_file_count(verify_path_record,filenames_record)

    def test_worker_remote_delete(self):
        """ Test remote deletion of folder """
        # Important
        self.args["dry_run"] = False
        self.args["delete_rm"] = True
        self.worker = Worker(self.progress, self.args)
        self.connection = self.worker.open_connection(self.conf)
        mode_folder = 'record'
        self.worker.get_recorded_footage(self.connection)
        self.worker.check_done_folders(self.connection)
        self.assertTrue(self.check_parent_dir_deleted(mode_folder))

    def test_worker_snapandrecorded_footage_download_delete_zip(self):
        """ Test our main entry point for downloading both types of footage """
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
        self.worker.get_files(self.connection)
        verify_path_snap = helper.construct_path(self.args['output_path'],[folder_snap,parent_dir_snap])
        verify_path_record = helper.construct_path(self.args['output_path'],[folder_record,parent_dir_record])
        helper.verify_file_count(verify_path_snap,filenames_snap)
        helper.verify_file_count(verify_path_record,filenames_record)

    """ Test helpers """

    def init_worker(self):
        self.worker = Worker(self.progress, self.args)
        self.connection = self.worker.open_connection(self.conf)

    def check_parent_dir_deleted(self,folder):
        return self.get_list_of_dirs(folder) is None

    def get_list_of_dirs(self, mode, subdir=False):
        path = helper.get_abs_path(self.conf, mode)
        list_dir = self.connection.mlsd(path)
        for dirname, _ in list_dir:
            if subdir:
                subpath = path + "/" + dirname
                list_subdirs = self.connection.mlsd(subpath)
                for subdirname, _ in list_subdirs:
                    return subdirname
            return dirname
        return None

    def get_list_of_files(self, mode):
        path = helper.get_abs_path(self.conf, mode)
        list_dir = self.connection.mlsd(path)
        for dirname, _ in list_dir:
            subpath = path + "/" + dirname
            list_subdirs = self.connection.mlsd(subpath)
            for subdir, _ in list_subdirs:
                list_files = self.connection.mlsd(subpath + "/" + subdir)
                return list(list_files)