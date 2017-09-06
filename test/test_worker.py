import os
import sys
import time
import logging
import shutil
import unittest
import zipfile
from ftplib import error_perm
from threading import Thread

import mock_server
from foscambackup.conf import Conf
from foscambackup.constant import Constant
from foscambackup.progress import Progress
from foscambackup.worker import Worker
import foscambackup.helper as helper

class TestWorker(unittest.TestCase):
    """ Basically an intergration / system test """
    thread = None
    testserver = None
    args = None
    conf = None
    worker = None
    connection = None

    def setUp(self):
        args = get_args_obj()
        args["output_path"] = TestWorker.output_path
        TestWorker.testserver.mock_dir(self.conf)
        self.args = args
        self.progress = Progress()

    def tearDown(self):
        helper.close_connection(self.connection)
        cleanup_directories(TestWorker.output_path)
        self.clear_log()

    @staticmethod
    def setUpClass():
        if get_verbosity() == 2:
            logger = logging.getLogger('Worker')
            logger.setLevel(logging.DEBUG)
            channel = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            channel.setFormatter(formatter)
            logger.addHandler(channel)
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
        TestWorker.testserver.cleanup_remote_directory()
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
        folder = mode['folder']
        sub_dir = self.get_list_of_dirs(folder, True)
        parent_dir = self.get_list_of_dirs(folder)
        filename = self.get_list_of_files(folder)[0][0]

        # First set the correct working dir
        loc_info = {'mode': mode, 'parent_dir': parent_dir+"/"+sub_dir,
            'filename': filename, 'desc': desc}
        self.worker.retrieve_and_write_file(self.connection,loc_info)
        verify_path = helper.construct_path(self.args['output_path'],[folder,parent_dir,filename])
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
        self.verify_file_count(verify_path,filenames)

    def test_worker_remote_delete(self):
        """ Test remote deletion of folder """
        # Important
        self.args["dry_run"] = False
        self.args["delete_rm"] = True
        self.worker = Worker(self.progress, self.args)
        self.connection = self.worker.open_connection(self.conf)
        mode_folder = 'record'
        self.worker.get_recorded_footage(self.connection)
        self.assertRaises(error_perm,self.check_parent_dir_deleted,mode_folder)

    def test_worker_zipfile(self):
        """ Test zip local file functionality """
        self.args["dry_run"] = False
        self.args["zip_files"] = True

        self.worker = Worker(self.progress, self.args)
        self.connection = self.worker.open_connection(self.conf)
        mode_folder = 'record'
        dir_structure = helper.construct_path(self.args['output_path'],[mode_folder])
        TestWorker.testserver.create_dir(dir_structure)
        new_path = TestWorker.testserver.generate_date_folders_local(dir_structure)
        created_files = []
        for i in range(1,3):
            val = TestWorker.testserver.generate_mocked_record_file(new_path + "/")
            if created_files.count(val) == 0:
                created_files.append(val)

        splitted = new_path.split('/')
        folder = helper.construct_path(mode_folder,[splitted[len(splitted)-1]])
        self.worker.init_zip_folder(folder)
        self.worker.zip_local_files_folder(folder)
        zip_file_path = new_path+".zip"
        self.assertEqual(os.path.isfile(zip_file_path),True)
        zip_file = zipfile.ZipFile(zip_file_path)
        list_files = zip_file.namelist()
        self.assertListEqual(created_files,list_files)

    """ Test helpers """

    def init_worker(self):
        self.worker = Worker(self.progress, self.args)
        self.connection = self.worker.open_connection(self.conf)

    def check_parent_dir_deleted(self,folder):
        return self.get_list_of_dirs(folder) == None

    def verify_file_count(self,verify_path,filenames):
        """ Assert the file count """
        if os.path.exists(verify_path):
            count = 0
            for filename in filenames:
                if os.path.isfile(verify_path+"/"+filename[0]):
                    count +=1
            assert count == len(filenames)
        else:
            assert False

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
        return None

    def get_list_of_files(self, mode):
        path = self.conf.model + "/" + mode
        list_dir = self.connection.mlsd(path)
        for dirname, _ in list_dir:
            subpath = path + "/" + dirname
            list_subdirs = self.connection.mlsd(subpath)
            for subdir, _ in list_subdirs:
                list_files = self.connection.mlsd(subpath + "/" + subdir)
                return list(list_files)

    def clear_log(self):
        if os.path.exists(Constant.state_file):
            os.remove(Constant.state_file)

        if os.path.exists(Constant.previous_state):
            os.remove(Constant.previous_state)

def get_verbosity():
    import inspect
    """Return current verbosity"""
    for f in inspect.getouterframes(inspect.currentframe() ):
        args, _,_, local_dict = inspect.getargvalues(f[0])
        if len(args) > 5: 
            first_arg = args[7]
            first_value = local_dict[first_arg]
            return first_value

def cleanup_directories(folder):
    shutil.rmtree(folder, ignore_errors=False, onerror=on_error)

def on_error(func, path, exc_info):
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
