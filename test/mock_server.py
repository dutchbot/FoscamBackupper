#!/usr/bin/env python

import os
import logging
from foscambackup import helper

from pyftpdlib import servers
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler


class MockFTPServer:
    """ Mock the foscam ftp folder structure """
    server = None
    running = False

    def start_ftp_server(self, conf):
        authorizer = DummyAuthorizer()

        # Define a new user having full r/w permissions and a read-only
        # anonymous user
        address = (conf.host, conf.port)
        authorizer.add_user('admin', 'abc@123', '.', perm='elradfmwM')
        authorizer.add_anonymous(os.getcwd())

        # Instantiate FTP handler class
        handler = FTPHandler
        handler.authorizer = authorizer

        self.server = servers.FTPServer(address, handler)
        logger = logging.getLogger('pyftpdlib')
        logger.disabled = True # disable
        self.running = True
        self.server.serve_forever()

    def is_running(self):
        return self.running

    def mock_dir(self, conf):
        # create IPCamera folder
        # create record and snap folder
        # create some mocked avi and jpg files
        dir_structure = "IPCamera/" + conf.model + "/record"
        self.create_dir(dir_structure)
        new_path = self.generate_date_folders_remote(dir_structure)
        self.generate_mocked_record_file(new_path + "/")
        dir_structure = "IPCamera/" + conf.model + "/snap"
        self.create_dir(dir_structure)
        new_path = self.generate_date_folders_remote(dir_structure)
        self.generate_mocked_snap_file(new_path + "/")

    def get_rand_bytes(self, size):
        return os.urandom(size)

    def generate_date_folders_local(self, path):
        """ Create the date folder structure for local """
        new_path = path + "/" + helper.get_current_date()
        self.create_dir(new_path)
        return new_path
    
    def generate_date_folders_remote(self, path):
        """ Create the date folders structure for remote """
        new_path = path + "/" + helper.get_current_date() + "/" + \
            helper.get_current_date_time_rounded()
        self.create_dir(new_path)
        return new_path

    def generate_mocked_record_file(self, path, offset = 0):
        """ create mocked avi file """
        file_content = self.get_rand_bytes((1024) * 200)  # 200KB file
        fname = helper.get_current_date_time_offset(offset) + ".avi"
        fname_path = path + fname
        if not os.path.isfile(fname_path):
            try:
                with open(fname_path, "wb") as filename:
                    filename.write(file_content)
            finally:
                filename.close()
        return fname

    def generate_mocked_snap_file(self, path):
        """ create mocked jpg file """
        file_content = self.get_rand_bytes((1024) * 90)  # 90 KB file
        fname = helper.get_current_date_time() + ".jpg"
        fname = path + fname
        if not os.path.isfile(fname):
            try:
                with open(fname, "wb") as filename:
                    filename.write(file_content)
            finally:
                filename.close()

    def create_dir(self, name):
        if not os.path.isdir(name):
            os.makedirs(name)

    def cleanup_remote_directory(self):
        """ Delete all mocked files """
        helper.cleanup_directories("IPCamera")

    def close(self):
        """ Close all connections so python does not leak """
        self.server.close_all()
