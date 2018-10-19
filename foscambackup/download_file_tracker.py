""" Wrapper for downloading to local file """
import os
import decimal
import progressbar

class DownloadFileTracker:
    """ Used to hold file for callback """
    decimal_two_places = decimal.Decimal(10) ** -2

    def __init__(self, local_file_path, byte_size):
        """ Open a file to download our contents to in binary mode """
        self.local_file = open(local_file_path, "w+b")
        self.total_size = byte_size
        self.downloaded_bytes = 0
        self.progressbar = progressbar.ProgressBar(max_value=100)
        self.progressbar.update(0)

    def write_to_file(self, binaries):
        """ Write to the file we hold, this is used by RETR callback"""
        self.local_file.write(binaries)
        self.update_progress(len(binaries))

    def update_progress(self, byte_len):
        """ Update download progression """
        self.downloaded_bytes += byte_len
        percentage = (self.downloaded_bytes / self.total_size)
        percentage = decimal.Decimal((self.downloaded_bytes / self.total_size))
        progress = round(percentage * 100, 2).quantize(self.decimal_two_places)
        if self.downloaded_bytes == self.total_size:
            self.progressbar.finish()
        else:
            self.progressbar.update(progress)

    def delete_file(self):
        """ Used when the server closed our connection during download """
        filename = self.local_file.name
        self.local_file.close()
        os.remove(filename)

    def close_file(self):
        """  We use this to close the file at some point, this class does not know when to close """
        self.local_file.close()
