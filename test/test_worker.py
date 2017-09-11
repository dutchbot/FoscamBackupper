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

mode_record = {"wanted_files": Constant.wanted_files_record,
"folder": Constant.record_folder, "int_mode": 0}
mode_snap = {"wanted_files": Constant.wanted_files_snap,
"folder": Constant.snap_folder, "int_mode": 1}

class TestWorker(unittest.TestCase):

    def setUp(self):
        mock_worker.conn.reset_mock()
        self.args = helper.get_args_obj()
        self.args['conf'] = Conf()
        self.progress = Progress()
        self.worker = Worker(mock_worker.conn, self.progress, self.args)
        #helper.log_to_stdout('Worker')

    def tearDown(self):
        mock_worker.conn.reset_mock()

    ##@unittest.SkipTest
    # def setUp(self):
    #     args =  helper.get_args_obj()
    #     args["output_path"] = TestWorker.output_path
    #     helper.mock_dir(self.conf)
    #     self.args = args
    #     self.progress = Progress()
    #     self.worker = Worker(Connection(), self.progress, self.args)

    ##@unittest.SkipTest
    # def tearDown(self):
    #     helper.clear_log()

    #unittest.SkipTest
    # @staticmethod
    # def setUpClass():
    #     helper.log_to_stdout('Worker')
    #     TestWorker.conf =  helper.read_conf()

    ##@unittest.SkipTest
    # @staticmethod
    # def tearDownClass():
    #     MockFTPServer.cleanup_remote_directory()
    #     helper.cleanup_directories(TestWorker.output_path)

    ##@unittest.SkipTest
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

    ##@unittest.SkipTest
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

    #@unittest.SkipTest
    def test_check_currently_recording(self):
        """ Test the behavior of setting the current_recording value to true/false """
        self.worker.check_currently_recording()
        self.assertEqual(self.args['conf'].currently_recording, True)
        mock_worker.conn.retrbinary = umock.Mock(side_effect=mock_worker.retrbinary_false, spec=str)
        self.worker = Worker(mock_worker.conn, self.progress, self.args)
        self.worker.check_currently_recording()
        self.assertEqual(self.args['conf'].currently_recording, False)

    #@unittest.SkipTest
    def test_read_sdrec_content(self):
        """ Test the behavior of setting the current_recording value to true/false """
        file_handle = bytes(helper.get_current_date_time_rounded(),'ascii')
        self.worker.read_sdrec_content(file_handle)
        self.assertEqual(self.args['conf'].currently_recording, True)
        file_handle = bytes(helper.get_current_date_offset_day()+"_100000",'ascii')
        self.worker.read_sdrec_content(file_handle)
        self.assertEqual(self.args['conf'].currently_recording, False)

    #@unittest.SkipTest
    def test_update_conf(self):
        #TODO
        pass

    #@unittest.SkipTest
    def test_get_files(self):
        """  Test that the expected functions get called, and proper mode objects are used """
        result = []
        def get_footage(*args, **kwargs):
            result.append(args[0])

        def check_done_folders(*args, **kwargs):
            return True

        mocked_footage = umock.MagicMock(side_effect = get_footage)
        check_done = umock.MagicMock(side_effect = check_done_folders)

        mock_worker.conn.reset_mock()

        with umock.patch('foscambackup.worker.Worker.get_footage', mocked_footage), \
            umock.patch('foscambackup.worker.Worker.check_done_folders', check_done):
                self.worker.get_files()

        calls = [call.mlsd('/'), call.retrbinary('RETR .SdRec', self.worker.read_sdrec_content)]

        self.assertDictEqual(result[0], mode_record)
        self.assertDictEqual(result[1], mode_snap)
        self.assertEqual(check_done.called, True, "Called check_done_folders")
        self.assertListEqual(mock_worker.conn.method_calls, calls, "Called check_currently_recording")

    def test_get_footage(self):
        # TODO:
        # want to test if folder recording is skipped
        # want to verify that the cur folder is set on progress object
        # done: assert number of files downloaded are correct.
        self.args['conf'].model = "FXXX_CEEE"
        def mlsd(*args, **kwargs):
            if args[0] == "/":
                yield (".", {'type':'dir'})
                yield (Constant.sd_rec, {'type':'dir'})
            else:
                yield (".", {'type':'dir'})
                yield ("..", {'type':'dir'})
                if args[0] == "/IPCamera/FXXX_CEEE/snap":
                    yield ("20170101", {'type':'dir'})
                    yield ("20170102", {'type':'dir'})
                    yield ("20170103", {'type':'dir'})
                    yield ("20170104", {'type':'dir'})
                    yield (helper.get_current_date(), {'type':'dir'})
                if args[0].count(helper.sl()) == 4:
                    dirname = args[0].split(helper.sl())[4]
                    yield (dirname+"_120000", {'type':'dir'})
                    yield (dirname+"_140000", {'type':'dir'})
                    yield (dirname+"_160000", {'type':'dir'})
                    yield (dirname+"_170000", {'type':'dir'})
                if  args[0].count(helper.sl()) == 5:
                    dirname = args[0].split(helper.sl())[5]
                    yield (dirname+".jpg", {'type':'file'})
        mock_worker.conn.mlsd.side_effect = mlsd
        def download_file(loc_info):
            return True
        download = umock.MagicMock()
        download.download_file = umock.MagicMock(side_effect=download_file)
        with umock.patch("foscambackup.worker.Worker.download_file", download.download_file):
            # RECORDING
            file_handle = bytes(helper.get_current_date_time_rounded(),'ascii')
            self.worker.read_sdrec_content(file_handle)
            self.worker.get_footage(mode_snap)
            self.assertEqual(self.worker.progress.done_files, 16)
        
        with umock.patch("foscambackup.worker.Worker.download_file", download.download_file):
            self.args['conf'].currently_recording = False
            self.worker.get_footage(mode_snap)
            self.assertEqual(self.worker.progress.done_files, 20)

    #@unittest.SkipTest
    def test_init_zip_folder(self):
        # verify initialized dict for given folder key
        self.worker.init_zip_folder("record/20160601")
        verify = {"record/20160601":{"zipped": 0,"remote_deleted": 0, "local_deleted": 0}}
        self.assertDictEqual(self.worker.folder_actions, verify)

    #@unittest.SkipTest
    def test_zip_local_files_folder(self):
        #TODO
        pass

    #@unittest.SkipTest
    def test_delete_local_folder(self):
        # #@unittest.SkipTestver
        # ify cleanup directories is called
        # verify folder_action local_deleted is set to True
        def delete_local(fullpath):
            return True
        m_helper = umock.MagicMock('helper')
        m_helper.cleanup_directories = umock.MagicMock(side_effect=delete_local)
        fullpath = "/output/record/20170101"
        folder = "record/20170101"
        self.worker.init_zip_folder(folder) #important
        with umock.patch("foscambackup.helper.cleanup_directories", m_helper):
            self.worker.delete_local_folder(fullpath, folder)

        verify = {folder:{"zipped": 0,"remote_deleted": 0, "local_deleted": 1}}
        self.assertListEqual(m_helper.call_args_list, [call('/output/record/20170101')])
        self.assertDictEqual(self.worker.folder_actions, verify)

    #@unittest.SkipTest
    def test_set_remote_deleted(self):
        """ Verify remote deleted value is set to 1 """
        folder = "record/20170101"
        self.worker.init_zip_folder(folder) #important
        self.worker.set_remote_deleted(folder)

        verify = {folder:{"zipped": 0,"remote_deleted": 1, "local_deleted": 0}}
        self.assertDictEqual(self.worker.folder_actions, verify)

    #@unittest.SkipTest
    def test_get_remote_deleted(self):
        folder = "record/20170101"
        self.worker.init_zip_folder(folder) #important
        
        self.assertEqual(self.worker.get_remote_deleted(folder), 0)
        self.worker.set_remote_deleted(folder)
        self.assertEqual(self.worker.get_remote_deleted(folder), 1)

    #@unittest.SkipTest
    def test_recursive_delete(self):
        #TODO
        pass

    #@unittest.SkipTest
    def test_delete_remote_folder(self):
        #TODO
        pass

    #@unittest.SkipTest
    def test_check_done_folders(self):
        #TODO
        pass

    #@unittest.SkipTest
    def test_zip_and_delete(self):
        #TODO
        pass

    #@unittest.SkipTest
    def test_check_folder_state_delete(self):
        #TODO
        pass

    #@unittest.SkipTest
    def test_crawl_folder(self):
        #TODO
        pass

    #@unittest.SkipTest
    def test_crawl_files(self):
        #TODO
        pass

    #@unittest.SkipTest
    def test_retrieve_and_write_file(self):
        #TODO
        pass

    #@unittest.SkipTest
    def test_download_file(self):
        #TODO
        pass
