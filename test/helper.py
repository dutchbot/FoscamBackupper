import os
import sys
import time
import logging
from foscambackup.constant import Constant
from foscambackup.conf import Conf

def get_abs_path(conf, mode):
    """ mode is string here """
    return construct_path("/" + Constant.base_folder, [conf.model, mode])

def close_connection(connection):
    """ Close the FTP connection """
    connection.close()

def construct_path(start, folders=[], endslash=False):
    """ Helps to get rid of all the slashes scattered throughout the program
        And thus helps migitate possible typo's.
    """
    if not isinstance(folders, type([])):
        print(type(folders))
        raise ValueError
    count = 0
    for folder in folders:
        if len(folders) != count:
            start += "/"
        start += folder
        count += 1
        if len(folders) == count and endslash:
            start += "/"
    return start

def get_current_date_time_offset(offset):
    """ For testing purposes TODO move to test helper """
    if offset != 0:
        time_str = time.strftime("%Y%m%d_%H%M%S")
        calc_offset = str(int(time_str[:-2]) + offset)
        l_timestr = list(time_str)
        l_timestr[-2] = calc_offset[0]
        l_timestr[-1] = calc_offset[1]
        time_str = ''.join(l_timestr)
        return time_str
    return time.strftime("%Y%m%d_%H%M%S")

def get_current_date():
    """ This is the format for the date folder where the subfolders and files will be located. """
    return time.strftime("%Y%m%d")

def get_current_date_time_rounded():
    """ This how the foscam model constructs the subfolders located in a date folder. """
    return time.strftime("%Y%m%d_%H0000")

def get_current_date_time():
    """ This is how the filenames are constructed on the foscam camera."""
    return time.strftime("%Y%m%d_%H%M%S")

def get_verbosity():
    import inspect
    """Return current verbosity"""
    for f in inspect.getouterframes(inspect.currentframe() ):
        args, _,_, local_dict = inspect.getargvalues(f[0])
        if len(args) > 5: 
            first_arg = args[7]
            first_value = local_dict[first_arg]
            return first_value

def generate_downloaded_path(mode_folder, args):
    dir_structure = construct_path(args['output_path'],[mode_folder])
    create_dir(dir_structure)
    new_path = generate_date_folders_local(dir_structure)
    created_files = []
    for i in range(1,3):
        val = generate_mocked_record_file(new_path + "/")
        if created_files.count(val) == 0:
            created_files.append(val)
    return (new_path, created_files)

def cleanup_directories(folder):
    import shutil
    print("Clean : "+ folder)
    shutil.rmtree(folder, ignore_errors=False, onerror=on_error)

def generate_date_folders_local(path):
    """ Create the date folder structure for local """
    new_path = path + "/" + get_current_date()
    create_dir(new_path)
    return new_path

def generate_date_folders_remote(path):
    """ Create the date folders structure for remote """
    new_path = path + "/" + get_current_date() + "/" + \
        get_current_date_time_rounded()
    create_dir(new_path)
    return new_path

def generate_mocked_record_file(path, offset = 0):
    """ create mocked avi file """
    file_content = get_rand_bytes((1024) * 200)  # 200KB file
    fname = get_current_date_time_offset(offset) + ".avi"
    fname_path = path + fname
    if not os.path.isfile(fname_path):
        try:
            with open(fname_path, "wb") as filename:
                filename.write(file_content)
        finally:
            filename.close()
    return fname

def on_error(func, path, exc_info):
    """ Callback function for OS errors when deleting a folder tree """
    print("Calling error")
    print(func)
    print(path)
    print(exc_info)

def generate_mocked_snap_file(path):
    """ create mocked jpg file """
    file_content = get_rand_bytes((1024) * 90)  # 90 KB file
    fname = get_current_date_time() + ".jpg"
    fname = path + fname
    if not os.path.isfile(fname):
        try:
            with open(fname, "wb") as filename:
                filename.write(file_content)
        finally:
            filename.close()

def get_rand_bytes(size):
    return os.urandom(size)

def create_dir(name):
    if not os.path.isdir(name):
        os.makedirs(name)

def verify_file_count(verify_path,filenames):
    """ Assert the file count """
    if os.path.exists(verify_path):
        count = 0
        for filename in filenames:
            if os.path.isfile(verify_path+"/"+filename[0]):
                count +=1
        assert count == len(filenames)
    else:
        assert False

def clear_log():
    if os.path.exists(Constant.state_file):
        os.remove(Constant.state_file)

    if os.path.exists(Constant.previous_state):
        os.remove(Constant.previous_state)

def log_to_stdout(logname):
    if get_verbosity() == 2:
        logger = logging.getLogger(logname)
        logger.setLevel(logging.DEBUG)
        channel = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        channel.setFormatter(formatter)
        logger.addHandler(channel)

def mock_dir(conf):
    # create IPCamera folder
    # create record and snap folder
    # create some mocked avi and jpg files
    dir_structure = "IPCamera/" + conf.model + "/record"
    create_dir(dir_structure)
    new_path = generate_date_folders_remote(dir_structure)
    generate_mocked_record_file(new_path + "/")
    dir_structure = "IPCamera/" + conf.model + "/snap"
    create_dir(dir_structure)
    new_path = generate_date_folders_remote(dir_structure)
    generate_mocked_snap_file(new_path + "/")

def get_args_obj():
    """ Mocked args object"""
    args = {}
    args["zip_files"] = False
    args["output_path"] = ""
    args["delete_rm"] = False
    args["verbose"] = True
    args["dry_run"] = True
    args["max_files"] = -1
    args["delete_local_f"] = False
    return args

def read_conf():
    file_conf = "test.conf"
    conf = Conf()
    with open(file_conf) as file_contents:
        content = file_contents.readlines()
        for keyvalue in content:
            split = keyvalue.split(":", 1)
            split[1] = split[1].rstrip()
            if split[0] == "host":
                conf.host = split[1]
            elif split[0] == "port":
                conf.port = int(split[1])
            elif split[0] == "username":
                conf.username = split[1]
            elif split[0] == "password":
                conf.password = split[1]
            elif split[0] == "model_serial":
                conf.model = split[1]
    return conf
