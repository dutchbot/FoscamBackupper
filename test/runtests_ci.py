""" Use for CI test """
import os
import sys
import unittest

sys.path.append(os.path.abspath(".")+"/")

from test_integration_worker import TestIntegrationWorker
from test_worker import TestWorker
from test_progress import TestProgress

TestWorker.output_path = "output-test-worker"
TestIntegrationWorker.output_path = "output-test-integration"
unittest.main()
