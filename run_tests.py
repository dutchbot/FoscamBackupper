""" Used for convenience in CI """
import os
import sys
import unittest

from integration.test_worker import TestWorker as TestIntegrationWorker
from test.test_file_wrapper import TestFileWrapper
from test.test_file_helper import TestFileHelper
from test.test_ftp_helper import TestFtpHelper
from test.test_progress import TestProgress
from test.test_worker import TestWorker
from test.test_helper import TestHelper

output_path = os.environ["output_path"]

TestIntegrationWorker.output_path = output_path + "/integration"
TestWorker.output_path = output_path + "/worker"

unittest.main(verbosity=2)
