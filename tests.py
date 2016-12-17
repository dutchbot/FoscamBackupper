import unittest
import os
import time
from main import Wrapper,Worker,CommandParser

class TestConnection(unittest.TestCase):

    def test_connection(self):
        print("conn")
        command = CommandParser()
        command.read_test_data()
        args = self.get_args_obj()
        worker = Worker(args)
        con = worker.open_connection()
        worker.close_connection(con)
        self.assertNotEqual(con.getwelcome(),None)

    def test_delete_file(self):
        print("delete")
        created_dir = "test_dir"
        command = CommandParser()
        command.read_test_data()
        args = self.get_args_obj()
        worker = Worker(args)
        con = worker.open_connection()

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
        worker = Worker(args)
        wanted_files = ['avi','avi_idx']
        desc = {'type':'file'}
        filename = "testme.txt"
        parent_dir="20160101"
        folder = "snap"
        connection = worker.open_connection()
        worker.retrieve_and_write_file(connection,parent_dir,filename,desc,wanted_files,folder)
        if not os.path.exists(output):
            assert(False)
        else:
            assert(True)

    def get_args_obj(self):
        args = {}
        args["zip_files"] = False
        args["output_path"] = ""
        args["delete_rm"] = False
        args["verbose"] = True
        args["dry_run"] = True
        args["delete_local_f"] = False
        return args

if __name__ == '__main__':
    unittest.main()