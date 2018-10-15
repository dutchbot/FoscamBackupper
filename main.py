""" Main function for running the program """
import sys
import socket
import logging
import traceback
import argparse
from io import StringIO

from foscambackup.worker import Worker
from foscambackup.constant import Constant
import foscambackup.util.ftp_helper as ftp_helper
from foscambackup.conf_factory import ConfigFactory
from foscambackup.command_parser import CommandParser

def main():
    """ Main """
    logger = None
    con = None
    worker = None
    stream = StringIO()
    exc = None
    try:
        parser = CommandParser()
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

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        channel.setFormatter(formatter)
        logger.addHandler(channel)

        handler = logging.StreamHandler(stream)
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        args['conf'] = ConfigFactory().read_conf(Constant.file_t)
        con = ftp_helper.open_connection(args['conf'])

        if args['conf'].model == "<model_serial>":
            args['conf'].write_model_to_conf(ftp_helper.retrieve_model_serial(con))

        worker = Worker(con, args)
        worker.get_files()
    except KeyboardInterrupt as interrupt:
        exc = interrupt
        logger.info("Program stopped by user, bye :)")
    except socket.timeout as stime:
        exc = stime
        logger.warning("Failed to connect to ftp server")
        logger.debug(stime.__str__())
    except socket.error as serr:
        exc = serr
        logger.warning("Failed to contact ftp server")
        logger.debug(serr.__str__())
    except Exception as generic:
        exc = generic
    finally:
        if worker != None and worker.progress_objects != None:
            for progress in worker.progress_objects:
                progress.save()
        if con != None:
            ftp_helper.close_connection(con)
        if exc != None:
            with open("debug.log", "a") as file_debug:
                file_debug.write(stream.getvalue())
                traceback.print_tb(exc.__traceback__, file=file_debug)
        sys.exit(exc)

if __name__ == "__main__":
    main()
