""" Use for local testing """
import os
import sys
import unittest
sys.path.append(os.path.abspath(".")+"/")
from test_worker import TestWorker

TestWorker.output_path = "D:/output-test"
unittest.main(verbosity=2)
