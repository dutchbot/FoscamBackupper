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
import foscambackup.helper as helper


def main():
    """ Main """
    progress = None
    logger = None
    con = None
    try:
        parser = CommandParser()
        progress = Progress()
        args = parser.commandline_args()
        if isinstance(args.__class__, type(argparse.ArgumentParser)):
            args = args.__dict__
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        channel = logging.StreamHandler(sys.stdout)
        if args["verbose"] == 'i':
            channel.setLevel(logging.INFO)
        elif args["verbose"] == 'w':
            channel.setLevel(logging.WARNING)
        elif args["verbose"] == 'd':
            channel.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        channel.setFormatter(formatter)
        logger.addHandler(channel)
        worker = Worker(progress, args)
        conf = parser.read_conf()
        con = worker.open_connection(conf)

        # Not ideal but we need to connect first to retrieve the model serial
        if conf.model == "<model_serial>":
            conf.write_model_to_conf(retrieve_model_serial(con))
            worker.update_conf(conf)

        worker.get_files(con)
    except KeyboardInterrupt:
        logger.info("Program stopped by user, bye :)")
    except socket.timeout as stime:
        logger.warning("Failed to connect to ftp server")
        logger.debug(stime.__str__())
        sys.exit()
    except socket.error as serr:
        logger.warning("Failed to contact ftp server")
        logger.debug(serr.__str__())
        sys.exit()
    except Exception:
        traceback.print_exc()
    finally:
        if con != None:
            helper.close_connection(con)
        if progress != None:
            progress.save_progress_exit()


def retrieve_model_serial(connection):
    """ Get the serial number """
    base = "CWD " + "/" + Constant.base_folder
    connection.sendcmd(base)
    dir_list = helper.mlsd(connection, "")
    for directory, _ in dir_list:
        if not "." in directory:
            return directory


if __name__ == "__main__":
    main()
