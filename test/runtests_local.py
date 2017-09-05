import sys
import os
import unittest
sys.path.append(os.path.abspath(".")+"\\")
from test_worker import TestWorker

TestWorker.output_path = "D:\\output-test"
unittest.main()
