#!/bin/bash

filePath=$0
fileDir=`dirname $filePath`
cd $fileDir

mkdir -p log
mkdir -p images
python3 src/twhmFetcher.py