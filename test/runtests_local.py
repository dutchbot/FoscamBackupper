""" Use for local testing """
import os
import sys
import unittest
sys.path.append(os.path.abspath(".")+"/")
from test_integration_worker import TestIntegrationWorker
from test_worker import TestWorker

TestWorker.output_path = "D:/output-test/worker"
TestIntegrationWorker.output_path = "D:/output-test/integration"
unittest.main(verbosity=2)
