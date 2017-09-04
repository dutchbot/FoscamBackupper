from foscambackup.constant import Constant

class Conf:
    host = ""
    port = 0
    username = ""
    password = ""
    model = ""
    currently_recording = False

    def write_model_to_conf(self,model):
        """ Retrieves the model_serial folder name and writes to conf """
        self.model = model
        try:
            with open(Constant.file_t, 'r') as file:
                data = file.readlines()
        finally:
            file.close()
        data[len(data)-1] = 'model_serial:' +model

        # and write everything back
        try:
            with open(Constant.file_t, 'w') as file:
                file.writelines( data )
        finally:
            file.close()