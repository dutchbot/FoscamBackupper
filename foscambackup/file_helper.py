import os

def open_readonly_file(path, function):
    """ Use to read file, use callback for interacting with file """
    if os.path.isfile(path):
        try:
            with open(path, "r") as read_only_file:
                function(read_only_file)
        finally:
            read_only_file.close()
    else:
        raise FileNotFoundError("File or path does not exist!")

def open_appendonly_file(path, function, args):
    """ Use to append file, use callback with args for interacting with file """
    try:
        with open(path, "a") as append_file:
            function(append_file, args)
    finally:
        append_file.close()

def open_write_file(path, function, args):
    """ Use to write file, use callback with args for interacting with file """
    if not os.path.isfile(path):
        write_file = None
        try:
            write_file = open(path, "w")
            function(write_file, args)
        finally:
            if write_file:
                write_file.close()
    else:
        raise FileExistsError("File already exists!")