#!/bin/bash

filePath=$0
fileDir=`dirname $filePath`
cd $fileDir

mkdir -p log
python3 src/kamu.py