from constant import Constant

class Conf:
    host = ""
    port = 0
    username = ""
    password = ""
    model = ""
    currently_recording = False

    def write_model_to_conf(self,model):
        self.model = model
        with open(Constant.file_t, 'r') as file:
            data = file.readlines()

        data[len(data)-1] = 'model_serial:' +model

        # and write everything back
        with open(Constant.file_t, 'w') as file:
            file.writelines( data )