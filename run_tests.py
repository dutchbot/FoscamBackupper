""" Used for convenience in CI """
import os
import sys
import unittest

from test.integration.test_worker import TestWorker as TestIntegrationWorker
from test.unit.test_file_wrapper import TestFileWrapper
from test.unit.test_file_helper import TestFileHelper
from test.unit.test_ftp_helper import TestFtpHelper
from test.unit.test_progress import TestProgress
from test.unit.test_worker import TestWorker
from test.unit.test_helper import TestHelper

output_path = os.environ["output_path"]

TestIntegrationWorker.output_path = output_path + "/integration"
TestWorker.output_path = output_path + "/worker"

unittest.main(verbosity=2)
