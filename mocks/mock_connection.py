class Connection:

    def __iter__(self):
        yield "."
        yield {'type':'folder'}

    def mlsd(self, path):
        yield "."
        yield {'type':'folder'}