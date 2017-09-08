""" Holds configuration class """
from foscambackup.constant import Constant
import foscambackup.file_helper as file_helper

class Conf:
    """ Hold the config options for use in program """
    host = ""
    port = 0
    username = ""
    password = ""
    model = ""
    currently_recording = False

    def get_model_serial(self, read_file):
        data = read_file.readlines()
        data[len(data)-1] = 'model_serial:' + self.model
        file_helper.open_write_file(Constant.file_t, self.write_model_serial, data)

    def write_model_serial(self, write_file, args):
        write_file.writelines(args['data'])

    def write_model_to_conf(self, model):
        """ Retrieves the model_serial folder name and writes to conf """
        self.model = model
        file_helper.open_readonly_file(Constant.file_t, self.get_model_serial)
