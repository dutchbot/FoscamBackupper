from foscambackup.constant import Constant
import foscambackup.util.helper as helper
from foscambackup.config import Config

class ConfigFactory:

    def read_conf(self, file_path):
        """ Read config to conf object """
        file_conf = file_path
        conf = Config()
        with open(file_conf) as filename:
            content = filename.readlines()
            for keyvalue in content:
                split = keyvalue.split(":", 1)
                split[1] = split[1].rstrip()
                if helper.retrieve_split(split, "host"):
                    conf.host = split[1]
                elif helper.retrieve_split(split, "port"):
                    conf.port = int(split[1])
                elif helper.retrieve_split(split, "username"):
                    conf.username = split[1]
                elif helper.retrieve_split(split, "password"):
                    conf.password = split[1]
                elif helper.retrieve_split(split, "model_serial"):
                    conf.model = split[1]
        return conf