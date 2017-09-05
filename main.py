""" Main function for running the program """
import sys
import socket
import logging
import traceback
import argparse

# own classes
from foscambackup.progress import Progress
from foscambackup.command_parser import CommandParser
from foscambackup.worker import Worker
from foscambackup.constant import Constant


def main():
    """ Main """
    progress = None
    logger = None

    try:
        parser = CommandParser()
        args = parser.commandline_args()
        if isinstance(args.__class__, type(argparse.ArgumentParser)):
            args = args.__dict__
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        channel = logging.StreamHandler(sys.stdout)
        if args["verbose"]:
            channel.setLevel(logging.INFO)
        else:
            channel.setLevel(logging.WARNING)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        channel.setFormatter(formatter)
        logger.addHandler(channel)
        progress = Progress()
        worker = Worker(progress, args)
        conf = parser.read_conf()
        con = worker.open_connection(conf)

        if conf.model == "<model_serial>":
            conf.write_model_to_conf(retrieve_model_serial(con))
            worker.update_conf(conf)

        worker.get_files(con)
    except KeyboardInterrupt:
        logger.info("Program stopped by user, bye :)")
        progress.save_progress_exit()
    except socket.timeout:
        logger.warning("Failed to connect to ftp server")
        sys.exit()
    except socket.error:
        logger.warning("Failed to contact ftp server")
        sys.exit()
    except Exception:
        traceback.print_exc()
        progress.save_progress_exit()


def retrieve_model_serial(connection):
    """ Get the serial number """
    base = "CWD " + "/" + Constant.base_folder
    connection.sendcmd(base)
    dir_list = connection.mlsd()
    for directory, _ in dir_list:
        if not "." in directory:
            return directory


if __name__ == "__main__":
    main()
