import os
import unittest
from test import test_server
from threading import Thread

from foscambackup.conf import Conf
from foscambackup.progress import Progress
from foscambackup.worker import Worker


class TestConnection(unittest.TestCase):
    thread = None
    testserver = None

    @staticmethod
    def setUpClass():
        conf = read_conf()
        address = (conf.host, conf.port)
        TestConnection.testserver = test_server.TestServer()
        TestConnection.thread = Thread(target = TestConnection.testserver.start_ftp_server, args = (address, ))
        TestConnection.thread.start()

    @staticmethod
    def tearDownClass():
        TestConnection.testserver.close()
        TestConnection.thread.join()

    def test_connection(self):
        print("conn")
        created_dir = "test_dir"
        args = self.get_args_obj()
        progress = Progress()
        worker = Worker(progress,args)
        conf = read_conf()
        con = worker.open_connection(conf)
        worker = Worker(progress,args)
        con = worker.open_connection(conf)
        self.assertNotEqual(con.getwelcome(),None)

    def test_delete_file(self):
        print("delete")
        created_dir = "test_dir"
        args = self.get_args_obj()
        progress = Progress()
        worker = Worker(progress,args)
        conf = read_conf()
        con = worker.open_connection(conf)
        worker = Worker(progress,args)
        con = worker.open_connection(conf)

        count_dir = 0
        dirs = con.mlsd(facts=['type'])

        con.mkd(created_dir)

        for dirkey,data in dirs:
            count_dir +=1
            if(dirkey == created_dir):
                con.rmd(created_dir)

        after_dirs = con.mlsd(facts=['type'])
        
        self.assertGreater(count_dir,len(list(after_dirs)))
        
        worker.close_connection(con)

    def test_run_output_path(self):
        output = "D:/output-test/"
        args = self.get_args_obj()
        args["output_path"] = output
        progress = Progress()
        worker = Worker(progress,args)
        wanted_files = ['avi','avi_idx']
        desc = {'type':'file'}
        filename = "testme.txt"
        parent_dir="20160101"
        folder = "snap"
        conf = read_conf()
        connection = worker.open_connection(conf)
        worker.retrieve_and_write_file(connection,parent_dir,filename,desc,wanted_files,folder)
        if not os.path.exists(output):
            assert(False)
        else:
            assert(True)

    def test_worker(self):
        output = "D:/output-test/"
        args = self.get_args_obj()
        args["output_path"] = output
        progress = Progress()
        worker = Worker(progress,args)
        conf = read_conf()
        connection = worker.open_connection(conf)
        worker.get_recorded_footage(connection)
        if not os.path.exists(output):
            assert(False)
        else:
            assert(True)


    def get_args_obj(self):
        """ """
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
    with open(file_conf) as f:
        content = f.readlines()
        for keyvalue in content:
            split = keyvalue.split(":",1)
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
