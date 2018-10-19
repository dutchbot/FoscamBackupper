
import unittest
import unittest.mock as umock
from test.mocks import mock_worker

from foscambackup.config import Config
from foscambackup.constant import Constant

class TestConfig(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.config.host = "127.0.0.1"
        self.config.port = 50021
        self.config.username = "admin"
        self.config.password = "abc@123"
        self.config.model = "FXXX_CXXX"
        self.config.currently_recording = False

    def test_config_to_str(self):
        # Arrange + Act
        result = self.config.__str__()     

        # Assert
        self.assertEqual(result, "{'host': '127.0.0.1', 'port': 50021, 'username': 'admin', 'password': 'abc@123', 'model': 'FXXX_CXXX', 'currently_recording': False}")

    def test_config_equal_to(self):
        # Arrange
        config = Config()
        config.host = "127.0.0.1"
        config.port = 50021
        config.username = "admin"
        config.password = "abc@123"
        config.model = "FXXX_CXXX"
        config.currently_recording = False

        # Act
        result = self.config.__eq__(config)

        # Assert
        self.assertTrue(result)

    def test_get_model_serial(self):
        # Arrange
        test_data = ["host:127.0.0.1", "port:50021", "username:admin", "password:abc@123", "model_serial:<model_serial>"]
        read_file = umock.mock_open(read_data=test_data)
        read_file.readlines = umock.MagicMock(return_value=test_data)
        open_write_file = umock.MagicMock()
        write_model_serial = umock.MagicMock()
        calls = [umock.call.open_write_file(Constant.settings_file, write_model_serial, test_data)]

        # Act
        with umock.patch("foscambackup.util.file_helper.open_write_file", open_write_file), \
            umock.patch("foscambackup.config.Config.write_model_serial", write_model_serial):
                self.config.get_model_serial(read_file)
        # Assert
        self.assertListEqual(open_write_file.call_args_list, calls)
    
    def test_write_model_serial(self):
        # Arrange
        args = {'data':'dummy'}
        write_file = umock.MagicMock()
        write_file.writelines = umock.MagicMock()

        # Act
        self.config.write_model_serial(write_file, args)

        # Assert
        self.assertListEqual(write_file.writelines.call_args_list, [umock.call('dummy')])

    def test_write_model_to_conf(self):
        # Arrange
        model_serial = "FXXX_CXXX"
        readonly_file = umock.MagicMock()
        get_model_serial = umock.MagicMock()
        calls = [umock.call.open_write_file(Constant.settings_file, get_model_serial)]

        # Act
        with umock.patch("foscambackup.util.file_helper.open_readonly_file", readonly_file), \
            umock.patch("foscambackup.config.Config.get_model_serial", get_model_serial):
                self.config.write_model_to_conf(model_serial)
                
        # Assert
        self.assertListEqual(readonly_file.call_args_list, calls)
