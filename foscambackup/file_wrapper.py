class FileWrapper:
    cur_file = None

    def __init__(self, local_file_path):
        self.cur_file = open(local_file_path, "w+b")

    def write_to_file(self,binaries):
        self.cur_file.write(binaries)
    
    def close_file(self):
        self.cur_file.close()
