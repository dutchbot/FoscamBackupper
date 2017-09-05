class FileWrapper:
    cur_file = None

    def set_cur_file(self,file):
        self.cur_file = file

    def write_to_file(self,binaries):
        self.cur_file.write(binaries)
    
    def close_file(self):
        self.cur_file.close()
