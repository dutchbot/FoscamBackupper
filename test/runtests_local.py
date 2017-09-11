""" Use for local testing """
import os
import sys
import unittest
sys.path.append(os.path.abspath(".")+"/")
# from test_integration_worker import TestIntegrationWorker
# TestIntegrationWorker.output_path = "D:/output-test/integration"
from test_helper import TestHelper
from test_ftp_helper import TestFtpHelper
from test_file_helper import TestFileHelper
from test_worker import TestWorker
TestWorker.output_path = "D:/output-test/worker"
from test_progress import TestProgress

unittest.main(verbosity=2)
