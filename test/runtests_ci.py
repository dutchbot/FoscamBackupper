import os
import sys
import unittest

sys.path.append(os.path.abspath(".")+"\\")

from test_worker import TestWorker

TestWorker.output_path = "output-test\\"
unittest.main()
