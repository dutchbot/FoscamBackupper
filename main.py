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
import foscambackup.ftp_helper as ftp_helper

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
        args['conf'] = parser.read_conf()
        con = ftp_helper.open_connection(args['conf'])
        worker = Worker(con, progress, args)

        # Not ideal but we need to connect first to retrieve the model serial
        if args['conf'].model == "<model_serial>":
            args['conf'].write_model_to_conf(helper.retrieve_model_serial(con))
            worker.update_conf(args['conf'])

        worker.get_files()
    except KeyboardInterrupt:
        logger.info("Program stopped by user, bye :)")
    except socket.timeout as stime:
        logger.warning("Failed to connect to ftp server")
        logger.debug(stime.__str__())
    except socket.error as serr:
        logger.warning("Failed to contact ftp server")
        logger.debug(serr.__str__())
    except Exception:
        traceback.print_exc()
    finally:
        if con != None:
            ftp_helper.close_connection(con)
        if progress != None:
            progress.save()
        sys.exit()

if __name__ == "__main__":
    main()
