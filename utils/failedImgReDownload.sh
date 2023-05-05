#!/bin/sh

filePath=$0
fileDir=`dirname $filePath`
cd $fileDir
logFile="./log/log.log"

dateStr=`date +"%Y-%m-%d 08:"`
dateStr=`tail -n 1 $logFile|awk -F ':' '{print $1}'`

logPart=`cat $logFile|grep -v "縱夏夜之夢"|grep "Fail to fetch image from"|grep -F "$dateStr"|awk -F '[' '{print $3 $4}'|awk -F ']' '{print $1 $2}'`
lineCount=`echo "$logPart"|wc -l`
idxes=`seq $lineCount`
for i in $idxes
do
    line=`echo "$logPart"|head -n $i|tail -n 1`
    link=`echo $line|awk '{print $1}'`
    targetPath=`echo $line|awk '{print $3}'`
    echo "download [$link] to path [$targetPath]"
    wget "$link" -O $targetPath
done
