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

## Note:
To get the `<model_serial>` folder name connect to the ftp server and look under the `IPCamera` folder.  
The `<port>` field seems to default to `50021`.


# Roadmap
1. Add option to store file sizes and compare to disk stored to determine state of file.
2. Add threading for zipping locally and downloading.

# Building for Windows
```
pip install pyinstaller
pyinstaller.exe main.py --noconfirm --onefile
```
