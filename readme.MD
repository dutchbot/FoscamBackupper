![GitHub Logo](https://travis-ci.org/dutchbot/FoscamBackupper.svg?branch=master)
[![Build status](https://ci.appveyor.com/api/projects/status/pypbqfr3k08in3sq?svg=true)](https://ci.appveyor.com/project/dutchbot/foscambackupper)

This project was created for usage with a foscam camera.  
To list the dirs, copy them to local disk of choice.

**Features**:

* Deleting the remote files to clear up space.
* Zip the files locally.
* Delete the files locally after zipping.
* Limit the number of files downloaded.
* Track progress, so retries are possible.

## Set the following in settings.conf

```
host:<host>  
port:<port> 
username:<username>  
password:<password> 
model_serial:<model_serial>
```
Note that the model_serial can be left as it is, the code will try to retrieve it from the ftp server.

# Roadmap
1. Show zipping / deletion progress.
2. Add threading for zipping locally and downloading.
3. Add option to store file sizes and compare to disk stored to determine state of file.

# Building for Windows
```
pip install pyinstaller
pyinstaller.exe main.py --noconfirm --onefile --exclude test
```

# exec test

`python test\runtests_local.py`

