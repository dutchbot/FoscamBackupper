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

    @staticmethod
    def cleanup_remote_directory():
        """ Delete all mocked files """
        helper.cleanup_directories("IPCamera")

    def close(self):
        """ Close all connections so python does not leak """
        self.server.close_all()
