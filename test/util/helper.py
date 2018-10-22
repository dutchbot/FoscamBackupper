import os
import sys
import time
import logging
from foscambackup.constant import Constant
from foscambackup.config import Config
import foscambackup.util.helper as helper

TEST_FILE_DELETION = True

def slash():
    """ return slash in use """
    return "/"

def get_abs_path(conf, mode):
    """ mode is string here """
    return construct_path(slash() + Constant.base_folder, [conf.model, mode])

def close_connection(connection):
    """ Close the FTP connection """
    if connection != None:
        connection.close()

def construct_path(start, folders=[], endslash=False):
    """ Helps to get rid of all the slashes scattered throughout the program
        And thus helps migitate possible typo's.
    """
    if not isinstance(folders, type([])):
        raise ValueError
    count = 0
    for folder in folders:
        if len(folders) != count:
            start += slash()
        start += folder
        count += 1
        if len(folders) == count and endslash:
            start += slash()
    return start

def get_current_date_time_offset(offset, sep="_"):
    """ Get current date with offset """
    if offset != 0:
        time_str = time.strftime("%Y%m%d"+sep+"%H%M%S")
        calc_offset = str(int(time_str[:-2]) + offset)
        l_timestr = list(time_str)
        l_timestr[-2] = calc_offset[0]
        l_timestr[-1] = calc_offset[1]
        time_str = ''.join(l_timestr)
        return time_str
    return time.strftime("%Y%m%d_%H%M%S")

def get_current_date():
    """ This is the format for the date folder where the subfolders and files will be located. """
    return helper.get_current_date()

def get_current_date_time_rounded(custom_time, sep='_'):
    """ This how the foscam model constructs the subfolders located in a date folder. """
    return time.strftime("%Y%m%d"+sep+"%H0000", custom_time)

def get_current_date_offset_day():
    """ Get current date and offset the day """
    offset = 1
    time_str = time.strftime("%Y%m%d")
    int_offset = int(time_str[-2:]) + offset
    if int_offset < 10:
        calc_offset = str("0"+str(int_offset))
    else:
        calc_offset = str(int_offset)
    l_timestr = list(time_str)
    l_timestr[-2] = calc_offset[0]
    l_timestr[-1] = calc_offset[1]
    time_str = ''.join(l_timestr)
    return time_str

def get_current_date_time_rounded_offset(sep='_'):
    """ This how the foscam model constructs the subfolders located in a date folder. """
    offset = 1
    time_str = time.strftime("%Y%m%d"+sep+"%H0000")
    calc_offset = str(int(time_str[-6:-4]) + offset)
    l_timestr = list(time_str)
    l_timestr[-6] = calc_offset[0]
    l_timestr[-5] = calc_offset[1]
    time_str = ''.join(l_timestr)
    return time_str

def get_current_date_time(sep='_'):
    """ This is how the filenames are constructed on the foscam camera."""
    return time.strftime("%Y%m%d"+sep+"%H%M%S")

def get_verbosity():
    """Return current verbosity"""
    import inspect
    for frame in inspect.getouterframes(inspect.currentframe()):
        args, _, _, local_dict = inspect.getargvalues(frame[0])
        if len(args) > 5:
            first_arg = args[7]
            first_value = local_dict[first_arg]
            return first_value

def generate_downloaded_path(mode_folder, args):
    dir_structure = construct_path(args['output_path'], [mode_folder])
    create_dir(dir_structure)
    new_path = generate_date_folders_local(dir_structure)
    created_files = []
    for _ in range(1, 3):
        val = generate_mocked_record_file(new_path + slash())
        if created_files.count(val) == 0:
            created_files.append(val)
    return (new_path, created_files)

def generate_date_folders_local(path):
    """ Create the date folder structure for local """
    new_path = path + slash() + get_current_date()
    create_dir(new_path)
    return new_path

def check_not_curup(foldername):
    """ Check if the folder is current or one directory up.
        Note: Not necessary in test mode but real ftp server needs it to prevent recursion
    """
    return foldername != '.' or foldername != '..'

def mlsd(con, path):
    """ Cleans the dot and dotdot folders TEST """
    file_list = con.mlsd(path)
    cleaned = [i for i in file_list if check_not_curup(i[0])]
    return cleaned

def generate_date_folders_remote(path, cur_date_call, call):
    """ Create the date folders structure for remote """
    new_path = path + slash() + cur_date_call() + slash() + call()
    create_dir(new_path)
    return new_path

def generate_mocked_record_file(path, offset=0):
    """ create mocked avi file """
    file_content = get_rand_bytes((1024) * 10)  # 10KB file
    file_name = get_current_date_time_offset(offset) + ".avi"
    file_path = path + file_name
    if not os.path.isfile(file_path):
        try:
            with open(file_path, "wb") as record_file:
                record_file.write(file_content)
        finally:
            record_file.close()
    return file_name

def on_error(func, path, exc_info):
    """ Callback function for OS errors when deleting a folder tree """
    print("Calling error")
    print(func)
    print(path)
    print(exc_info)

def generate_mocked_snap_file(path):
    """ create mocked jpg file """
    file_content = get_rand_bytes((1024) * 2)  # 2 KB file
    file_path = get_current_date_time("-") + ".jpg"
    file_path = path + file_path
    if not os.path.isfile(file_path):
        try:
            with open(file_path, "wb") as snap_file:
                snap_file.write(file_content)
        finally:
            snap_file.close()

def get_rand_bytes(size):
    """ Random bytes """
    return os.urandom(size)

def create_dir(name):
    """ If dir does note exist, create """
    if not os.path.isdir(name):
        os.makedirs(name)

def verify_file_count(verify_path, filenames):
    """ Assert the file count """
    if os.path.exists(verify_path):
        count = 0
        for filename in filenames:
            if os.path.isfile(verify_path+slash()+filename[0]):
                count += 1
        assert count == len(filenames)
    else:
        assert False

def verify_files_deleted(verify_path, filenames):
    """ Assert the file count """
    if os.path.exists(verify_path):
        count = 0
        for filename in filenames:
            if os.path.isfile(verify_path+slash()+filename[0]):
                count += 1
        assert count == len(filenames)
    else:
        assert True

def clear_log():
    if TEST_FILE_DELETION:
        if os.path.exists(Constant.state_file):
            os.remove(Constant.state_file)

        if os.path.exists(Constant.previous_state):
            os.remove(Constant.previous_state)

def cleanup_directories(folder):
    if TEST_FILE_DELETION:
        import shutil
        shutil.rmtree(folder, ignore_errors=False, onerror=on_error)

def log_to_stdout(logname, level=''):
    if get_verbosity() == 2:
        logger = logging.getLogger(logname)
        if level == '':
            logger.setLevel(logging.DEBUG)
        elif level == 'info':
            logger.setLevel(logging.INFO)
        channel = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        channel.setFormatter(formatter)
        logger.addHandler(channel)

def mock_dir(conf):
    """ create IPCamera folder
        create record and snap folder
        create some mocked avi and jpg files
    """
    dir_structure = "IPCamera/" + conf.model + "/record"
    create_dir(dir_structure)
    new_path = generate_date_folders_remote(dir_structure, get_current_date, lambda:get_current_date_time_rounded(time.localtime()))
    generate_mocked_record_file(new_path + slash())
    dir_structure = "IPCamera/" + conf.model + "/snap"
    create_dir(dir_structure)
    new_path = generate_date_folders_remote(dir_structure, get_current_date, lambda:get_current_date_time_rounded(time.localtime(), '-'))
    generate_mocked_snap_file(new_path + slash())

    sdrec_file_path = Constant.base_folder+slash()+Constant.sd_rec
    if os.path.isfile(Constant.base_folder+slash()+Constant.sd_rec):
        with open(sdrec_file_path, 'w') as file:
            file.write(get_current_date())
        file.close()

def mock_dir_offset_subdir(conf):
    dir_structure = "IPCamera/" + conf.model + "/record"
    create_dir(dir_structure)
    new_path = generate_date_folders_remote(dir_structure, get_current_date, lambda: get_current_date_time_rounded_offset())
    generate_mocked_record_file(new_path + slash())
    dir_structure = "IPCamera/" + conf.model + "/snap"
    create_dir(dir_structure)
    new_path = generate_date_folders_remote(dir_structure, get_current_date, lambda: get_current_date_time_rounded_offset('-'))
    generate_mocked_snap_file(new_path + slash())

def mock_dir_offset_parentdir(conf):
    dir_structure = "IPCamera/" + conf.model + "/record"
    create_dir(dir_structure)
    new_path = generate_date_folders_remote(dir_structure, get_current_date_offset_day, lambda: get_current_date_time_rounded(time.localtime()))
    generate_mocked_record_file(new_path + slash())
    dir_structure = "IPCamera/" + conf.model + "/snap"
    create_dir(dir_structure)
    new_path = generate_date_folders_remote(dir_structure, get_current_date_offset_day, lambda: get_current_date_time_rounded(time.localtime(),'-'))
    generate_mocked_snap_file(new_path + slash())

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
    args["mode"] = None
    args['conf'] = None
    return args

def read_conf():
    """ Read conf and create conf object """
    conf = Config()
    conf.host = os.environ['config_host']
    conf.port = int(os.environ['config_port'])
    conf.username = os.environ['config_username']
    conf.password = os.environ['config_password']
    conf.model = os.environ['config_model_serial']
    return conf
