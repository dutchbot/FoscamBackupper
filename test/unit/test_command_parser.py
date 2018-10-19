import unittest
import unittest.mock as umock
from foscambackup.command_parser import CommandParser

class TestCommandParser(unittest.TestCase):
    
    def test_command_parser_given_all_options_verify_arguments(self):
        # Arrange
        args = ["main.py","-o","output","-m","100","--zip","--drm","--dlf","--verbose","w","-mode","record","--dry"]
        expected = {
            "delete_local_f":True, 
            "delete_rm":True, 
            "dry_run":True, 
            "max_files":100,
            "mode":'record', 
            "output_path":'output', 
            "verbose":'w', 
            "zip_files":True
        }

        # Act
        with umock.patch('sys.argv', args):
            parsed = CommandParser.commandline_args()

        # Assert
        self.assertDictEqual(expected, parsed.__dict__)
