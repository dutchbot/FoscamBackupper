import sys
import socket
import shutil
import logging
import traceback

# own classes
from progress import Progress
from command_parser import CommandParser
from worker import Worker
from constant import Constant

progress = None
connection = None

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

def main():
    try:
        parser = CommandParser()
        global progress
        progress = Progress()
        args = parser.commandline_args()
        worker = Worker(progress,args)
        conf = parser.read_conf()
        con = worker.open_connection(conf)

        if conf.model == "<model_serial>":
            conf.write_model_to_conf(retrieve_model_serial(con))
            worker.update_conf(conf)

        worker.get_files(con)
    except KeyboardInterrupt:
        logger.info("Program stopped by user, bye :)")
        save_progress_exit()
    except socket.timeout:
        logger.warning("Failed to connect to ftp server")
        sys.exit()
    except socket.error:
        logger.warning("Failed to contact ftp server")
        sys.exit()
    except Exception as t:
        traceback.print_exc()
        save_progress_exit()

def save_progress_exit():
    if(progress.get_cur_folder() != ''):
        logger.debug("Saving progress..")
        progress.save_progress_for_unfinished(progress.current_mode+"/"+progress.get_cur_folder())
    sys.exit()

def retrieve_model_serial(connection):
    base = "CWD "+"/"+Constant.f_folder
    connection.sendcmd(base)
    dir_list = connection.mlsd()
    for dir,detail in dir_list:
        if not "." in dir:
            return dir

if __name__ == "__main__":
    main()