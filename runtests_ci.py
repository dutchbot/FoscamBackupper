""" Use for CI test """
import os
import sys
import unittest

from integration.test_worker import TestWorker as TestIntegrationWorker
TestIntegrationWorker.output_path = "output-test-integration"
from test.test_helper import TestHelper
from test.test_ftp_helper import TestFtpHelper
from test.test_file_helper import TestFileHelper
from test.test_file_wrapper import TestFileWrapper
from test.test_progress import TestProgress
from test.test_worker import TestWorker
TestWorker.output_path = "output-test-worker"

unittest.main(verbosity=2)
