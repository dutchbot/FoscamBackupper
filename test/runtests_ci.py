""" Use for CI test """
import os
import sys
import unittest

sys.path.append(os.path.abspath(".")+"/")

#from test_integration_worker import TestIntegrationWorker
#TestIntegrationWorker.output_path = "output-test-integration"
from test_helper import TestHelper
from test_progress import TestProgress
from test_worker import TestWorker
TestWorker.output_path = "output-test-worker"

unittest.main()
