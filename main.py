from ftplib import FTP
from ftplib import error_perm
from zipfile import ZipFile
from zipfile import ZIP_LZMA
import lzma
import os
import argparse
import sys
import socket
import json
import shutil
import logging
import traceback
from progress import Progress

host = ""
port = 0
username = ""
password = ""
model = ""
f_folder = "IPCamera"
file_t = "settings.conf"
wanted_files = ['avi','avi_idx']
wanted_files_snap = ['jpg','jpg']
snap_folder="snap"
record_folder="record"
cur_folder = ""
progress = None
connection = None
current_mode = None

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
        worker = Worker(args)
        parser.read_conf()
        con = worker.open_connection()
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
    if(cur_folder != ''):
        logger.debug("Saving progress..")
        progress.save_progress_for_unfinished(current_mode+"/"+cur_folder)
    sys.exit()

class CommandParser:
    def commandline_args(self):
        parser = argparse.ArgumentParser(description='Download and retrieve recordings and snapshots from foscam webcamera, pass command line arguments for zipping and sorting.')
        parser.add_argument('-o', dest="output_path", action="store", default="", help='The absolute directory to output the files to.')
        parser.add_argument('-m', dest="max_files", action="store", default=-1, type=int,help='The max amount of files to process')
        #parser.add_argument('-sort', dest="sort_files", help='sort the files on day, month or year options d,m,y.')
        parser.add_argument('--zip', action="store_true", default=True, dest="zip_files", help='zip the files.')
        parser.add_argument('--drm', action="store_true", dest="delete_rm", help='Delete the files on ftp server after storing them locally.')
        parser.add_argument('--dlf', action="store_true", dest="delete_local_f", help='Delete the local folder after zipping it.')
        parser.add_argument('--verbose', action="store_true", dest="verbose", help='Display all actions')
        parser.add_argument('--dry', action="store_true", dest="dry_run", help='Do not delete local and remote folders')
        args = parser.parse_args()
        return args

    def read_conf(self,file_conf=""):
        global file_t
        if(file_conf != ""):
            file_t = file_conf
        with open(file_t) as f:
            content = f.readlines()
            for keyvalue in content:
                split = keyvalue.split(":",1)
                split[1] = split[1].rstrip()
                if(split[0] == "host"):
                    global host
                    host = split[1]
                elif(split[0] == "port"):
                    global port
                    port = int(split[1])
                elif(split[0] == "username"):
                    global username
                    username = split[1]
                elif(split[0] == "password"):
                    global password
                    password = split[1]
                elif(split[0] == "model_serial"):
                    global model
                    model = split[1]

class Worker:
    #object variables
    def __init__(self,args):
        if(isinstance(args.__class__, type(argparse.ArgumentParser))):
            args = args.__dict__
        logger.debug(isinstance(args.__class__, type(None)))
        self.zipped_folders = {}
        self.zip_files = args["zip_files"]
        if(args["output_path"][-1:] == ""):
            logger.debug("Using current dir")
            self.output_path = ""
        elif(args["output_path"][-1:] == "/"):
            self.output_path = args["output_path"]
        else:
            """ Fix the / """
            self.output_path = args["output_path"] + "/"
        if(self.output_path != "" and not os.path.exists(self.output_path)):
            os.mkdir(self.output_path)
        self.delete_rm = args["delete_rm"]
        logger.debug(args['max_files'])
        progress.set_max_files(args["max_files"])
        self.verbose = args["verbose"]
        self.dry_run = args["dry_run"]
        self.delete_local_f = args["delete_local_f"]

    def open_connection(self):
        global connection
        connection = FTP()
        connection.set_pasv(False)
        connection.connect(host, port)
        connection.login(username,password)
        return connection

    def close_connection(self,connection):
        connection.close()

    def get_files(self,connection):
        self.get_recorded_footage(connection)
        self.get_snapshot_footage(connection)
        logger.info("finished downloading files")

    def set_remote_folder(self,connection,mode,extra_folder = None):
        base = "CWD "+"/"+f_folder+"/"+model+"/"
        if(extra_folder == None):
            extra_folder = ""    
        if (mode == 0):
            logger.debug("Record folder selected!")
            connection.sendcmd(base+record_folder+extra_folder)
        elif (mode == 1):
            logger.debug("Snap folder selected!")
            connection.sendcmd(base+snap_folder+extra_folder)
                    
    def zip_local_files_folder(self,folder):
        split = folder.split("/")
        output = split[0]
        fname = split[1]
        if os.path.exists(self.output_path+output):
            if(os.path.exists(self.output_path+folder)):
                os.chdir(self.output_path+folder)
                logger.info("zipping "+fname+" folder... ")
            else:
                return
            if(not os.path.isfile(self.output_path+"../"+fname+'.zip')):
                with ZipFile(self.output_path+"../"+fname+'.zip', 'w',compression=ZIP_LZMA) as myzip:
                    for filex in os.listdir():
                        logger.debug(filex)
                        myzip.write(filex)
        os.chdir("../../")
                    
    def delete_local_folder(self,path):
       shutil.rmtree(self.output_path+path, ignore_errors=True)

    def set_remote_folder_fullpath(self,fullpath):
        connection.sendcmd(fullpath)

    def delete_remote_folder(self,fullpath,folder):
        try:
            self.set_remote_folder_fullpath(fullpath)
            connection.rmd(folder)
        except error_perm as perm:
            if("550" in perm.__str__()):
                logger.debug("Recursive strategy")
                """ Recursive strategy to clean folder """
                self.set_remote_folder_fullpath(fullpath+"/"+folder)
                dir_list = connection.mlsd()
                for dirt,dir_desc in dir_list:
                    self.set_remote_folder_fullpath(fullpath+"/"+folder+"/"+dirt)
                    file_list = connection.mlsd()
                    for file,desc in file_list:
                        if(desc['type'] != "dir"):
                            if(file != "." and file != ".."):
                                connection.delete(file)
                    if(dirt != "." and dirt != ".."):
                        self.set_remote_folder_fullpath(fullpath+"/"+folder)
                        logger.debug("Removing subdir: "+dirt)
                        connection.rmd(dirt)
                logger.debug("deleting top folder")
                self.set_remote_folder_fullpath(fullpath)
                connection.rmd(folder)

    def get_recorded_footage(self,connection):
        mode = {"wanted_files":wanted_files,"folder":record_folder,"int_mode":0}
        self.set_remote_folder(connection,0)
        global current_mode
        current_mode = record_folder
        self.get_footage(connection,mode)

    def get_snapshot_footage(self,connection):
        mode = {"wanted_files":wanted_files_snap,"folder":snap_folder,"int_mode":1}
        self.set_remote_folder(connection,1)
        global current_mode
        current_mode = snap_folder
        self.get_footage(connection,mode)
    
    def get_footage(self,connection,mode):
        tmp = connection.mlsd()
        # Snapshot folders are also ordered by time periods
        for pdir,desc in tmp:
            if(desc['type'] == 'dir'):
                logger.debug(pdir)
                self.set_remote_folder(connection,mode["int_mode"],"/"+pdir)
                if(progress.check_done_folder(mode["folder"],pdir) == False):
                    global cur_folder
                    cur_folder = pdir
                    self.crawl_files(connection.mlsd(),connection,False,mode,pdir)
                else:
                     logger.debug("skipping folder")
                self.check_done_folders_zip_and_delete(mode["folder"])

    def check_done_folders_zip_and_delete(self,output_dir):
        logger.debug("called zip and delete")
        done_folders = sorted(progress.check_folders_done(),reverse=True)
        logger.debug(done_folders)
        logger.debug("Zip_files "+ str(self.zip_files))
        logger.debug(self.zipped_folders)
        for folder in done_folders:
            try:
                self.zip_and_delete(folder)
            except KeyError:
                self.zipped_folders[folder] = {"zipped":0,"remote_deleted":0,"local_deleted":0}
                self.zip_and_delete(folder)

    def zip_and_delete(self,folder):
        if(self.zipped_folders[folder]['zipped'] == 0 and self.zip_files == True):
            self.zip_local_files_folder(folder)
            self.zipped_folders[folder]['zipped'] = 1
        
        if(self.delete_local_f and self.zipped_folders[folder]["local_deleted"] == 0):
            if not self.dry_run:
                self.delete_local_folder(folder)
                self.zipped_folders[folder]["local_deleted"] = 1
            else:
                self.zipped_folders[folder]["local_deleted"] = 1
                logger.info("Deleted local: "+folder)

        if(self.zipped_folders[folder]['remote_deleted'] == 0 and self.delete_rm == True ):
            if not self.dry_run:
                fullpath = "CWD "+"/"+f_folder+"/"+model+"/"+folder.split("/")[0]
                self.delete_remote_folder(fullpath,folder.split("/")[1])
                self.zipped_folders[folder]['remote_deleted'] = 1
            else:
                self.zipped_folders[folder]['remote_deleted'] = 1
                logger.debug("Deleted: "+folder)

    # more like crawl..
    def crawl_files(self,file_list,connection,recurse,mode,parent_dir=""):
        for filename,desc in file_list:
            # do not add the time period folders
            if(desc['type'] != 'dir' and not ".dat" in filename and not ".." in filename and not "." == filename):
                if(progress.check_for_previous_progress(mode["folder"],parent_dir,filename)):
                    logger.debug("skipping: "+filename)
                    continue
                if(progress.is_max_files_reached() == True):
                    save_progress_exit()
                progress.add_file_init(mode["folder"]+"/"+parent_dir,filename)
            parent_dir = parent_dir
            self.retrieve_and_write_file(connection,parent_dir,filename,desc,mode["wanted_files"],mode["folder"])
            if(desc['type'] == 'dir'):
                self.traverse_folder(connection,mode["int_mode"],parent_dir,filename)
                tmp = connection.mlsd()
                self.crawl_files(tmp,connection,False,mode,parent_dir)


    def traverse_folder(self,connection,mode,parent_dir,filename):
        if(parent_dir != ""):
            self.set_remote_folder(connection,mode,"/"+parent_dir+"/"+filename)
        else:
            self.set_remote_folder(connection,mode,"/"+filename)

    def retrieve_and_write_file(self,connection,parent_dir,filename,desc,wanted_files,folder):
        if(desc['type'] == 'file'):
            check = filename.split(".")
            if(len(check) > 1):
                check = filename.split(".")[1]
                if(check == wanted_files[0] or check == wanted_files[1]):
                    wrapper = Wrapper()
                    folder = folder +"/"+parent_dir
                    if not os.path.exists(self.output_path+folder):
                        os.makedirs(self.output_path+folder)
                    cur_file = open (self.output_path+folder+"/"+filename, "w+b")
                    wrapper.set_cur_file(cur_file)
                    #optional restart option rest
                    connection.retrbinary("RETR "+filename,wrapper.write_to_file)
                    progress.add_file_done(folder,filename)

class Wrapper:
    cur_file = None

    def set_cur_file(self,file):
        self.cur_file = file

    def write_to_file(self,binaries):
        self.cur_file.write(binaries)

if __name__ == "__main__":
    main()