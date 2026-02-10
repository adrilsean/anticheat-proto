@echo off
echo Downloading Poppins fonts...

REM Download Poppins Regular
powershell -Command "Invoke-WebRequest -Uri 'https://fonts.gstatic.com/s/poppins/v20/pxiEyp8kv8JHgFVrFJA.ttf' -OutFile 'fonts\Poppins-Regular.ttf'"

REM Download Poppins Medium
powershell -Command "Invoke-WebRequest -Uri 'https://fonts.gstatic.com/s/poppins/v20/pxiByp8kv8JHgFVrLGT9Z1xlFd2JQEk.ttf' -OutFile 'fonts\Poppins-Medium.ttf'"

REM Download Poppins Bold
powershell -Command "Invoke-WebRequest -Uri 'https://fonts.gstatic.com/s/poppins/v20/pxiByp8kv8JHgFVrLCz7Z1xlFd2JQEk.ttf' -OutFile 'fonts\Poppins-Bold.ttf'"

echo Font download complete!
echo Please restart the application to use Poppins fonts.