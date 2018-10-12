""" Use for local testing """
import os
import sys
import unittest
sys.path.append(os.path.abspath(".")+"/")
from integration.test_worker import TestWorker as TestIntegrationWorker
TestIntegrationWorker.output_path = "C:/output-test/integration"
from test.test_helper import TestHelper
from test.test_ftp_helper import TestFtpHelper
from test.test_file_helper import TestFileHelper
from test.test_file_wrapper import TestFileWrapper
from test.test_worker import TestWorker
TestWorker.output_path = "C:/output-test/worker"
from test.test_progress import TestProgress

unittest.main(verbosity=2)
