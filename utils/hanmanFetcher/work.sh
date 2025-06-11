#!/bin/bash

filePath=$0
fileDir=`dirname $filePath`
cd $fileDir

#mainPage=`curl -s --connect-timeout 5 https://totototot.asuscomm.com | grep -F "Welcome to nginx"`
#if [ $? -eq 0 -a -n "$mainPage" ]
#then
#    echo "not use proxy"
#else
#    echo "use proxy"
#    export http_proxy="http://192.168.119.47:8080"
#    export https_proxy="http://192.168.119.47:8080"
#fi

mkdir -p log
python3 src/main.py >> log/shell.log 2>&1

/home/kzhang/github/comicViewer/utils/hanmanFetcher/log/dlImgsByFailedLog.sh
