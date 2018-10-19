import unittest
import unittest.mock as umock
from io import StringIO
from foscambackup.config_factory import ConfigFactory
from foscambackup.config import Config

class TestConfigFactory(unittest.TestCase):

    def setUp(self):
        self.config_factory = ConfigFactory()
        self.conf = Config()
        self.conf.host = "127.0.0.1"
        self.conf.port = 50021
        self.conf.username = "admin"
        self.conf.password = "abc@123"
        self.conf.model = "FXXXXXX_CXXXXXXXXXXX"

    def test_config_factory_read_conf(self):
        TEST_DATA = ("host:127.0.0.1\nport:50021\nusername:admin\npassword:abc@123\nmodel_serial:FXXXXXX_CXXXXXXXXXXX")
        
        with umock.patch("builtins.open", new_callable=umock.mock_open, read_data=TEST_DATA):
            result = self.config_factory.read_conf("fake/path")
            self.assertEqual(self.conf, result)
