import argparse

from conf import Conf
from constant import Constant

class CommandParser:

    def commandline_args(self):
        parser = argparse.ArgumentParser(description='Download and retrieve recordings and snapshots from foscam webcamera, pass command line arguments for zipping and sorting.')
        parser.add_argument('-o', dest="output_path", action="store", default="", help='The absolute directory to output the files to.')
        parser.add_argument('-m', dest="max_files", action="store", default=-1, type=int,help='The max amount of files to process')
        #parser.add_argument('-sort', dest="sort_files", help='sort the files on day, month or year options d,m,y.')
        parser.add_argument('--zip', action="store_true", default=True, dest="zip_files", help='zip the files.')
        parser.add_argument('--drm', action="store_true", dest="delete_rm", help='Delete the files on ftp server after storing them locally.')
        parser.add_argument('--dlf', action="store_true", dest="delete_local_f", help='Delete the local folder after zipping it.')
        parser.add_argument('--verbose', action="store_true", dest="verbose", help='Display all actions')
        parser.add_argument('--dry', action="store_true", dest="dry_run", help='Do not delete local and remote folders')
        args = parser.parse_args()
        return args

    def read_conf(self):
        file_conf = Constant.file_t
        conf = Conf()
        with open(file_conf) as f:
            content = f.readlines()
            for keyvalue in content:
                split = keyvalue.split(":",1)
                split[1] = split[1].rstrip()
                if(split[0] == "host"):
                    conf.host = split[1]
                elif(split[0] == "port"):
                    conf.port = int(split[1])
                elif(split[0] == "username"):
                    conf.username = split[1]
                elif(split[0] == "password"):
                    conf.password = split[1]
                elif(split[0] == "model_serial"):
                    conf.model = split[1]
        return conf
