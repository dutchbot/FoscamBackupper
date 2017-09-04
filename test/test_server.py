#!/usr/bin/env python

import os
from multiprocessing import Process, Queue

from pyftpdlib import servers
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler


class TestServer:

    server = None

    def start_ftp_server(self, address):
        authorizer = DummyAuthorizer()

        # Define a new user having full r/w permissions and a read-only
        # anonymous user
        authorizer.add_user('admin', 'abc@123', '.', perm='elradfmwM')
        authorizer.add_anonymous(os.getcwd())

        # Instantiate FTP handler class
        handler = FTPHandler
        handler.authorizer = authorizer

        self.mock_dir()

        self.server = servers.FTPServer(address, handler)
        self.server.serve_forever()

    def mock_dir(self):
        # create IPCamera folder
        # create record and snap folder
        # create some mocked avi and jpg files
        if not os.path.isdir("IPCamera"):
            os.mkdir("IPCamera")

    def close(self):
        self.server.close_all()