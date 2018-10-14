""" Wrapper for downloading to local file """
import os
import decimal
import progressbar

TWOPLACES = decimal.Decimal(10) ** -2

class FileWrapper:
    """ Used to hold file for callback """

    def __init__(self, local_file_path, byte_size):
        """ Open a file to download our contents to in binary mode """
        self.cur_file = open(local_file_path, "w+b")
        self.total_size = byte_size
        self.downloaded_bytes = 0
        self.progressbar = progressbar.ProgressBar(max_value=100)
        self.progressbar.update(0)

    def write_to_file(self, binaries):
        """ Write to the file we hold, this is used by RETR callback"""
        self.cur_file.write(binaries)
        self.update_progress(len(binaries))

    def update_progress(self, byte_len):
        """ Update download progression """
        self.downloaded_bytes += byte_len
        percentage = (self.downloaded_bytes / self.total_size)
        percentage = decimal.Decimal((self.downloaded_bytes / self.total_size))
        progress = round(percentage * 100, 2).quantize(TWOPLACES)
        if self.downloaded_bytes == self.total_size:
            self.progressbar.finish()
        else:
            self.progressbar.update(progress)

    def delete_file(self):
        """ Used when the server closed our connection during download """
        filename = self.cur_file.name
        self.cur_file.close()
        os.remove(filename)

    def close_file(self):
        """  We use this to close the file at some point, this class does not know when to close """
        self.cur_file.close()
