""" Parse commands for the program """
import argparse
from foscambackup.config import Config
from foscambackup.constant import Constant
import foscambackup.util.helper as helper


class CommandParser:
    """ Parse commands and read config file """
    @staticmethod
    def commandline_args():
        """ Commands and descriptions """
        parser = argparse.ArgumentParser(
            description='Download and retrieve recordings and snapshots from foscam webcamera,'
            'pass command line arguments for zipping and sorting.')
        parser.add_argument('-o', dest="output_path", action="store",
                            default="", help='The absolute directory to output the files to.')
        parser.add_argument('-m', dest="max_files", action="store",
                            default=-1, type=int, help='The max amount of files to process')
        parser.add_argument('--zip', action="store_true",
                            default=True, dest="zip_files", help='zip the files.')
        parser.add_argument('--drm', action="store_true", dest="delete_rm",
                            help='Delete the files on ftp server after storing them locally.')
        parser.add_argument('--dlf', action="store_true", dest="delete_local_f",
                            help='Delete the local folder after zipping it.')
        parser.add_argument('--verbose', action="store",
                            dest="verbose", help='Output logging level with e,w,v')
        parser.add_argument('-mode', action="store", dest="mode",
                            default=None, help="Limit the mode to: 'record' or 'snap")
        parser.add_argument('--dry', action="store_true", dest="dry_run",
                            help='Do not delete local and remote folders')
        args = parser.parse_args()
        return args
