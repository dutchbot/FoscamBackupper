![GitHub Logo](https://travis-ci.org/dutchbot/FoscamBackupper.svg?branch=development)

This little python project was created for usage with a foscam camera.  
To list the dirs, copy them to local disk of choice .

**Features**:

* Deleting the remote files to clear up space.
* Zip the files locally.
* Delete the files locally after zipping.
* Limit the number of files downloaded.
* Set the output dir, default is current directory.

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
1. Add option to store file sizes and compare to disk stored to determine state of file.
2. Add threading for zipping locally and downloading.
3. Set verbosity from commandline 
4. Implement CI
5. Mock / test with ftp server
6. add test for zipping,
7. Show download progress (we probably need to parse file descriptions)

# Building for Windows
```
pip install pyinstaller
pyinstaller.exe main.py --noconfirm --onefile
```

# exec test

`python test\runtests_local.py`
