import os
import time
import shutil
import unittest
from threading import Thread

import mock_server
from foscambackup.conf import Conf
from foscambackup.constant import Constant
from foscambackup.progress import Progress
from foscambackup.worker import Worker


class TestWorker(unittest.TestCase):
    thread = None
    testserver = None
    args = None
    conf = None
    worker = None
    connection = None

    def setUp(self):
        args = get_args_obj()
        args["output_path"] = TestWorker.output_path
        self.args = args
        progress = Progress()
        self.worker = Worker(progress, self.args)
        self.connection = self.worker.open_connection(self.conf)

    def tearDown(self):
        self.worker.close_connection(self.connection)

    @staticmethod
    def setUpClass():
        TestWorker.conf = read_conf()
        TestWorker.testserver = mock_server.MockFTPServer()
        TestWorker.thread = Thread(
            target=TestWorker.testserver.start_ftp_server, args=(TestWorker.conf, ))
        TestWorker.thread.start()
        while not TestWorker.testserver.is_running():
            print("waiting")
            time.sleep(0.2)

    @staticmethod
    def tearDownClass():
        TestWorker.testserver.close()
        TestWorker.testserver.cleanup_directories()
        TestWorker.thread.join()

    def test_connection(self):
        self.assertNotEqual(self.connection.getwelcome(), None)

    def test_delete_file(self):
        """ Verify that we can delete a file remotely """
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
        """ Note: we want to test a function from worker actually, need lambdas """
        if len(self.get_list_of_files("record")) > 0 and len(self.get_list_of_files("snap")) > 0:
            assert True
        else:
            assert False

    def test_download_write_file_record(self):
        """ Verify that we can retrieve and write a file to a specific directory """
        mode = {"wanted_files": Constant.wanted_files_record,
                "folder": Constant.record_folder, "int_mode": 0}
        desc = {'type': 'file'}
        folder = "record"
        sub_dir = self.get_list_of_dirs(folder, True)
        parent_dir = self.get_list_of_dirs(folder)
        filename = self.get_list_of_files(folder)[0][0]

        # First set the correct working dir
        self.worker.traverse_folder(
            self.connection, mode["int_mode"], parent_dir, sub_dir)
        self.worker.retrieve_and_write_file(
            self.connection, parent_dir, filename, desc, mode["wanted_files"], folder)
        verify_path = self.args['output_path'] + \
            folder + "/" + parent_dir + "/" + filename
        print(verify_path)
        if os.path.exists(verify_path):
            assert True
        else:
            assert False

    def test_worker_recorded_footage_download_only(self):
        """ Test that we can download recorded footage """
        folder = 'record'
        parent_dir = self.get_list_of_dirs(folder)
        filenames = self.get_list_of_files(folder)
        self.worker.get_recorded_footage(self.connection)
        verify_path = self.args['output_path'] + folder + "/" + parent_dir + "/"
        if os.path.exists(verify_path):
            count = 0
            for filename in filenames:
                if os.path.exists(verify_path+filename[0]):
                    count +=1
            assert count == len(filenames)
        else:
            print("wuut")
            assert False

    # def test_worker_recorded_footage_download_remote_delete(self):
    #     """ Test that we can download recorded footage """
    #     """ To verify correctly we need a list of files """
    #     self.worker.get_recorded_footage(self.connection)
    #     if not os.path.exists(self.args['output_path']):
    #         assert(False)
    #     else:
    #         assert(True)

    """ Test helpers """

    def get_list_of_dirs(self, mode, subdir=False):
        path = self.conf.model + "/" + mode
        list_dir = self.connection.mlsd(path)
        for dirname, _ in list_dir:
            if subdir:
                subpath = path + "/" + dirname
                list_subdirs = self.connection.mlsd(subpath)
                for subdirname, _ in list_subdirs:
                    return subdirname
            return dirname

    def get_list_of_files(self, mode):
        path = self.conf.model + "/" + mode
        list_dir = self.connection.mlsd(path)
        for dirname, _ in list_dir:
            subpath = path + "/" + dirname
            list_subdirs = self.connection.mlsd(subpath)
            for subdir, _ in list_subdirs:
                list_files = self.connection.mlsd(subpath + "/" + subdir)
                return list(list_files)

    def cleanup_directories(self, folder):
        shutil.rmtree(folder, ignore_errors=False, onerror=self.on_error)

    def on_error(self, func, path, exc_info):
        print(func)
        print(path)
        print(exc_info)

def get_args_obj():
    """ Mocked args object"""
    args = {}
    args["zip_files"] = False
    args["output_path"] = ""
    args["delete_rm"] = False
    args["verbose"] = True
    args["dry_run"] = True
    args["max_files"] = -1
    args["delete_local_f"] = False
    return args

def read_conf():
    file_conf = "test.conf"
    conf = Conf()
    with open(file_conf) as file_contents:
        content = file_contents.readlines()
        for keyvalue in content:
            split = keyvalue.split(":", 1)
            split[1] = split[1].rstrip()
            if split[0] == "host":
                conf.host = split[1]
            elif split[0] == "port":
                conf.port = int(split[1])
            elif split[0] == "username":
                conf.username = split[1]
            elif split[0] == "password":
                conf.password = split[1]
            elif split[0] == "model_serial":
                conf.model = split[1]
    return conf
