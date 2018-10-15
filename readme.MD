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

