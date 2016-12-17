This little python project was created for usage with a foscam camera.  
To list the dirs, copy them to local disk of choice .

**Optional**:

* Deleting the remote files to clear up space.
* Zip the files locally.
* Sort the files locally.
* Set the output dir, default is current directory.

## Set the following in testdata.txt

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


Roadmap
Add option to limit number of files pulled
Add option to store file sizes and compare to disk stored to determine state of file.
Add logger
Add threading for zipping locally and downloading

Decisions:
Organize the zips based on foscam folders or other means?
Should we predetermine how many files one zip must contain? (for even spreading)
Should we zip after we got the amount of files needed for 1 zip file? (concurrent?)


# Building for Windows
```
	pip install pyinstaller
	pyinstaller.exe main.py --noconfirm --onefile
```