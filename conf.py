from constant import Constant

class Conf:
    host = ""
    port = 0
    username = ""
    password = ""
    model = ""

    def write_model_to_conf(self,model):
        self.model = model
        with open(Constant.file_t, 'r') as file:
            data = file.readlines()

        print(data)
        # now change the 2nd line, note that you have to add a newline
        data[len(data)-1] = 'model_serial:' +model

        # and write everything back
        with open(Constant.file_t, 'w') as file:
            file.writelines( data )