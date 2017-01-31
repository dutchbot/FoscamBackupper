import json
import os.path
import logging

logger = logging.getLogger()

class Progress:
    global logger
    max_files = -1
    done_files = 1
    done_folders = []
    done_progress = {}
    current_mode = None
    cur_folder = ""

    def __init__(self):
        previous = "previous_state.json"
        if(os.path.isfile(previous)):
            cur_file = open(previous,"r")
            with open(previous) as f:
                tmp = json.load(f)
                # don't slice here /n already removed
                self.done_progress[tmp['path']] = tmp

        fname ="progress.state"
        if(os.path.isfile(fname)):
            cur_file = open(fname,"r")
            with open(fname) as f:
                content = f.readlines()
                for line in content:
                    self.done_progress[line[:-1]] = {"done":1,"path":line[:-1]}
                    self.done_folders.append(line[:-1])
    
    # getters/setters
    def set_max_files(self,max_files):
        self.max_files = max_files

    def set_current_mode(self,cur_mode):
        self.cur_mode = cur_mode
    
    def set_cur_folder(self,cur_folder):
        self.cur_folder = cur_folder
    
    def get_cur_folder(self):
        return self.cur_folder

    #end
    
    def check_for_previous_progress(self,prefix,folder,filename):
        try:
            if(self.done_progress[prefix+"/"+folder][filename] == 1):
                return True
            return False
        except KeyError:
            return False

    def check_done_folder(self,mode,foldername):
        logger.debug("Mode "+mode+" "+foldername)
        #check all the files for 1 value
        for folder in self.done_folders:  
            if(folder == mode+"/"+foldername):
                return True
        return False

    def is_max_files_reached(self):
        logger.debug("max_files: " + str(self.max_files))
        logger.debug("done files: "+ str(self.done_files))
        if(self.max_files != -1):
            return self.max_files <= self.done_files
        else:
            return False
    
    def add_file_init(self,combined,filename):
        try:
            self.done_progress[combined][filename] = 0
        except:
            logger.error("Key error init " + combined)
            self.done_progress[combined] = {"done":0,"path":combined}
            self.done_progress[combined][filename] = 0

    def add_file_done(self,folder,filename):
        try:
            self.done_files += 1
            self.done_progress[folder][filename] = 1
        except:
            logger.error("Key error file_done")
            logger.debug(self.done_progress)

    def check_folders_done(self):
        tmp = []
        for folder_name,folder in self.done_progress.items():
            if(folder["done"] != 1):
                number_of_files = len(folder.keys()) - 2
                actual_done = 0
                for key,value in folder.items():
                    if(key != "done" and key != "path"):
                        if(value == 1):
                            actual_done +=1

                logger.debug(folder_name)
                logger.debug("Files: "+str(number_of_files) + " Actual: " + str(actual_done))
                if(number_of_files == actual_done):
                    cur_file = open("state.log","a")
                    enc = folder["path"] + "\n"
                    cur_file.write(enc)
                    tmp.append(folder["path"])
                    self.done_progress[folder_name]["done"] = 1
            else:
                tmp.append(folder["path"])
        return tmp
    
    # save the progress of the last folder
    def save_progress_for_unfinished(self,folder):
        try:
            logger.debug(self.done_folders)
            for dir in self.done_folders:
                if(dir == folder):
                    return
            last_file = self.done_progress[folder]
            cur_file = open("previous_state.json","w")
            enc = json.dumps(last_file)
            cur_file.write(enc)
        except:
            logger.warning("Key: "+folder)
            logger.warning("Key error in save_progress_for_unfinished")
            logger.warning(self.done_progress)
