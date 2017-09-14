import progressbar
""" Wrapper for downloading to local file """


class FileWrapper:
    """ Used to hold file for callback """

    def __init__(self, local_file_path, byte_size):
        """ Open a file to download our contents to in binary mode """
        self.cur_file = open(local_file_path, "w+b")
        self.total_size = byte_size
        self.count_called = 1
        self.remainder = None
        self.next = -1
        self.progressbar = progressbar.ProgressBar(max_value=100)
        self.progressbar.update(0)

    def write_to_file(self, binaries):
        """ Write to the file we hold, this is used by RETR callback"""
        self.cur_file.write(binaries)
        self.update_progress(binaries)

    def update_progress(self, binaries):
        """ FIXME for the n-1 step """
        if not self.remainder:
            self.remainder = self.total_size % len(binaries)
        divider = ((self.total_size) / (len(binaries) * self.count_called))
        progress = 100 / divider
        next_progress = 100 / ((self.total_size) / (len(binaries) * (self.count_called + 1)))
        if next_progress < 100 and self.next == -1:
            self.count_called += 1
        else:
            if self.next == -1:
                self.next = 100
        if self.next != -1:
            progress = self.next
        self.progressbar.update(progress)

    def close_file(self):
        """  We use this to close the file at some point, this class does not know when to close """
        self.cur_file.close()
