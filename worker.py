import argparse
import logging
import lzma
import os
import time
import shutil

from ftplib import FTP
from ftplib import error_perm
from zipfile import ZipFile
from zipfile import ZIP_LZMA

# own classes
from file_wrapper import FileWrapper
from progress import Progress
from constant import Constant

class Worker:
    #object variables
    logger = logging.getLogger()
    progress = None
    conf = None

    def __init__(self,progress,args):
        self.progress = progress
        if(isinstance(args.__class__, type(argparse.ArgumentParser))):
            args = args.__dict__
        self.logger.debug(isinstance(args.__class__, type(None)))
        self.zipped_folders = {}
        self.zip_files = args["zip_files"]
        if(args["output_path"][-1:] == ""):
            self.logger.debug("Using current dir")
            self.output_path = ""
        elif(args["output_path"][-1:] == "/"):
            self.output_path = args["output_path"]
        else:
            """ Fix the / """
            self.output_path = args["output_path"] + "/"
        if(self.output_path != "" and not os.path.exists(self.output_path)):
            os.mkdir(self.output_path)
        self.delete_rm = args["delete_rm"]
        self.logger.debug(args['max_files'])
        self.progress.set_max_files(args["max_files"])
        self.verbose = args["verbose"]
        self.dry_run = args["dry_run"]
        self.delete_local_f = args["delete_local_f"]

    def check_currently_recording(self,connection):
        base = "CWD "+"/"+Constant.f_folder
        connection.sendcmd(base)
        dir_list = connection.mlsd()
        for dir,detail in dir_list:
            if dir == ".SdRec":
                connection.retrbinary("RETR "+dir,self.read_sdrec_content)
                break

    def read_sdrec_content(self,bin):
        if(time.strftime("%Y%m%d") == bin.decode('ascii').split("_")[0]):
            self.logger.info("Skipping current date, because currently recording.")
            self.conf.currently_recording = True

    def update_conf(self,conf):
        self.conf = conf

    def open_connection(self,conf):
        self.conf = conf

        connection = FTP()
        connection.set_pasv(False)
        connection.connect(conf.host, conf.port)
        connection.login(conf.username,conf.password)

        self.check_currently_recording(connection)

        return connection

    def close_connection(self,connection):
        connection.close()

    def get_files(self,connection):
        self.get_recorded_footage(connection)
        self.get_snapshot_footage(connection)
        self.logger.info("finished downloading files")

    def set_remote_folder(self,connection,mode,extra_folder = None):
        base = "CWD "+"/"+Constant.f_folder+"/"+self.conf.model+"/"
        if(extra_folder == None):
            extra_folder = ""    
        if (mode == 0):
            self.logger.debug("Record folder selected!")
            connection.sendcmd(base+Constant.record_folder+extra_folder)
        elif (mode == 1):
            self.logger.debug("Snap folder selected!")
            connection.sendcmd(base+Constant.snap_folder+extra_folder)
                    
    def zip_local_files_folder(self,folder):
        split = folder.split("/")
        output = split[0]
        fname = split[1]
        if os.path.exists(self.output_path+output):
            if(os.path.exists(self.output_path+folder)):
                os.chdir(self.output_path+folder)
                self.logger.info("zipping "+fname+" folder... ")
            else:
                return
            if(not os.path.isfile(self.output_path+fname+'.zip')):
                with ZipFile(self.output_path+fname+'.zip', 'w',compression=ZIP_LZMA) as myzip:
                    for filex in os.listdir():
                        self.logger.debug(filex)
                        myzip.write(filex)
        os.chdir("../../")
                    
    def delete_local_folder(self,path):
       shutil.rmtree(self.output_path+path, ignore_errors=True)

    def set_remote_folder_fullpath(self,connection,fullpath):
        connection.sendcmd(fullpath)

    def delete_remote_folder(self,connection,fullpath,folder):
        try:
            self.set_remote_folder_fullpath(connection,fullpath)
            connection.rmd(folder)
        except error_perm as perm:
            if("550" in perm.__str__()):
                self.logger.debug("Recursive strategy")
                """ Recursive strategy to clean folder """
                self.set_remote_folder_fullpath(connection,fullpath+"/"+folder)
                dir_list = connection.mlsd()
                for dirt,dir_desc in dir_list:
                    self.set_remote_folder_fullpath(connection,fullpath+"/"+folder+"/"+dirt)
                    file_list = connection.mlsd()
                    for file,desc in file_list:
                        if(desc['type'] != "dir"):
                            if(file != "." and file != ".."):
                                connection.delete(file)
                    if(dirt != "." and dirt != ".."):
                        self.set_remote_folder_fullpath(connection,fullpath+"/"+folder)
                        self.logger.debug("Removing subdir: "+dirt)
                        connection.rmd(dirt)
                self.logger.debug("deleting top folder")
                self.set_remote_folder_fullpath(connection,fullpath)
                connection.rmd(folder)

    def get_recorded_footage(self,connection):
        mode = {"wanted_files":Constant.wanted_files,"folder":Constant.record_folder,"int_mode":0}
        self.set_remote_folder(connection,0)
        self.progress.current_mode = Constant.record_folder
        self.get_footage(connection,mode)

    def get_snapshot_footage(self,connection):
        mode = {"wanted_files":Constant.wanted_files_snap,"folder":Constant.snap_folder,"int_mode":1}
        self.set_remote_folder(connection,1)
        self.progress.current_mode = Constant.snap_folder
        self.get_footage(connection,mode)
    
    def get_footage(self,connection,mode):
        tmp = connection.mlsd()
        # Snapshot folders are also ordered by time periods
        for pdir,desc in tmp:
            if(desc['type'] == 'dir'):
                if(self.conf.currently_recording):
                    if (time.strftime("%Y%m%d") == pdir):
                        self.logger.info("Skipping current recording folder: " + pdir)
                        continue
                self.logger.debug(pdir)
                self.set_remote_folder(connection,mode["int_mode"],"/"+pdir)
                if(self.progress.check_done_folder(mode["folder"],pdir) == False):
                    self.progress.set_cur_folder(pdir)
                    self.crawl_files(connection.mlsd(),connection,False,mode,pdir)
                else:
                     self.logger.debug("skipping folder")
                self.check_done_folders_zip_and_delete(connection,mode["folder"])

    def check_done_folders_zip_and_delete(self,connection,output_dir):
        self.logger.debug("called zip and delete")
        done_folders = sorted(self.progress.check_folders_done(),reverse=True)
        self.logger.debug(done_folders)
        self.logger.debug("Zip_files "+ str(self.zip_files))
        self.logger.debug(self.zipped_folders)
        for folder in done_folders:
            try:
                self.zip_and_delete(connection,folder)
            except KeyError:
                self.zipped_folders[folder] = {"zipped":0,"remote_deleted":0,"local_deleted":0}
                self.zip_and_delete(connection,folder)

    def zip_and_delete(self,connection,folder):
        if(self.zipped_folders[folder]['zipped'] == 0 and self.zip_files == True):
            self.zip_local_files_folder(folder)
            self.zipped_folders[folder]['zipped'] = 1
        
        if(self.delete_local_f and self.zipped_folders[folder]["local_deleted"] == 0):
            if not self.dry_run:
                self.delete_local_folder(folder)
                self.zipped_folders[folder]["local_deleted"] = 1
            else:
                self.zipped_folders[folder]["local_deleted"] = 1
                self.logger.info("Deleted local: "+folder)

        if(self.zipped_folders[folder]['remote_deleted'] == 0 and self.delete_rm == True ):
            if not self.dry_run:
                fullpath = "CWD "+"/"+Constant.f_folder+"/"+self.conf.model+"/"+folder.split("/")[0]
                self.delete_remote_folder(connection,fullpath,folder.split("/")[1])
                self.zipped_folders[folder]['remote_deleted'] = 1
            else:
                self.zipped_folders[folder]['remote_deleted'] = 1
                self.logger.debug("Deleted: "+folder)

    def crawl_files(self,file_list,connection,recurse,mode,parent_dir=""):
        for filename,desc in file_list:
            # do not add the time period folders
            if(desc['type'] != 'dir' and not ".dat" in filename and not ".." in filename and not "." == filename):
                if(self.progress.check_for_previous_progress(mode["folder"],parent_dir,filename)):
                    self.logger.debug("skipping: "+filename)
                    continue
                if(self.progress.is_max_files_reached() == True):
                    save_progress_exit()
                self.progress.add_file_init(mode["folder"]+"/"+parent_dir,filename)
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
                if(check == Constant.wanted_files[0] or check == Constant.wanted_files[1]):
                    wrapper = FileWrapper()
                    folder = folder +"/"+parent_dir
                    if not os.path.exists(self.output_path+folder):
                        os.makedirs(self.output_path+folder)
                    cur_file = open (self.output_path+folder+"/"+filename, "w+b")
                    wrapper.set_cur_file(cur_file)
                    connection.retrbinary("RETR "+filename,wrapper.write_to_file)
                    self.progress.add_file_done(folder,filename)
