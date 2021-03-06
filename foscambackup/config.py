""" Holds configuration class """
from foscambackup.util import helper
from foscambackup.constant import Constant
import foscambackup.util.file_helper as file_helper

class Config:
    """ Hold the config options for use in program """
    host = ""
    port = 0
    username = ""
    password = ""
    model = ""
    currently_recording = False

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other): 
        return self.__dict__ == other.__dict__

    def get_model_serial(self, read_file):
        """ get the model serial from file """
        data = read_file.readlines()
        data[len(data)-1] = 'model_serial:' + self.model
        file_helper.open_write_file(Constant.settings_file, self.write_model_serial, data)

    def write_model_serial(self, write_file, args):
        """ Write the data to file """
        write_file.writelines(args['data'])

    def write_model_to_conf(self, model):
        """ Retrieves the model_serial folder name and writes to conf """
        self.model = model
        file_helper.open_readonly_file(Constant.settings_file, self.get_model_serial)
