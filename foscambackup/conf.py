""" Holds configuration class """
from foscambackup.constant import Constant

class Conf:
    """ Hold the config options for use in program """
    host = ""
    port = 0
    username = ""
    password = ""
    model = ""
    currently_recording = False

    def write_model_to_conf(self, model):
        """ Retrieves the model_serial folder name and writes to conf """
        self.model = model
        try:
            with open(Constant.file_t, 'r') as config_file:
                data = config_file.readlines()
        finally:
            config_file.close()
        data[len(data)-1] = 'model_serial:' +model

        # and write everything back
        try:
            with open(Constant.file_t, 'w') as config_file:
                config_file.writelines(data)
        finally:
            config_file.close()
