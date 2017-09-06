""" Wrapper for downloading to local file """
class FileWrapper:
    """ Used to hold file for callback """
    cur_file = None

    def __init__(self, local_file_path):
        """ Open a file to download our contents to in binary mode """
        self.cur_file = open(local_file_path, "w+b")

    def write_to_file(self, binaries):
        """ Write to the file we hold, this is used by RETR callback"""
        self.cur_file.write(binaries)

    def close_file(self):
        """  We use this to close the file at some point, this class does not know when to close """
        self.cur_file.close()
