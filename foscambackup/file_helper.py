import os

def open_readonly_file(path, function):
    if os.path.isfile(path):
        try:
            with open(path, "r") as read_only_file:
                function(read_only_file)
        finally:
            read_only_file.close()
    raise FileNotFoundError("File or path does not exist!")

def open_appendonly_file(path, function, args):
    try:
        with open(path, "a") as append_file:
            function(append_file, args)
    finally:
        append_file.close()

def open_write_file(path, function, args):
    if not os.path.isfile(path):
        try:
            with open(path, "w") as write_file:
                function(write_file, args)
        finally:
            write_file.close()
    raise FileExistsError("File already exists!")