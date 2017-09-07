""" Use for local testing """
import os
import sys
import unittest
sys.path.append(os.path.abspath(".")+"/")
from test_intergration_worker import TestIntergrationWorker
from test_worker import TestWorker

TestWorker.output_path = "D:/output-test/worker"
TestIntergrationWorker.output_path = "D:/output-test/intergration"
unittest.main(verbosity=2)
