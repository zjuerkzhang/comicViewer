#!/bin/sh

filePath=$0
fileDir=`dirname $filePath`
cd $fileDir
comicRootDir="../comic/00-连载中/"
logFile="utils.log"

rm -f $logFile




scripts="/home/kzhang/github/comicViewer/utils/clImages/clImageAutoFetcher.sh \
        /home/kzhang/github/comicViewer/utils/hanmanFetcher/work.sh"

for s in $scripts
do
    pidStr=`ps aux|grep -F "$s"|grep -v grep`
    if [ -z "$pidStr" ]
    then
        echo "\n\n=== execute $s ===\n\n"
        /bin/sh "$s" >> $logFile 2>&1
    else
        echo "\n\n=== $s is running, skip ===\n\n"
    fi
done
exit 0

comicDirs=`ls $comicRootDir`
for d in $comicDirs
do
    dirPath="$comicRootDir$d"
    if [ -d "$dirPath" ]
    then
        configFile="$dirPath/info.json"
        if [ -e "$configFile" ]
        then
            lastChapterId=`cat $configFile|jq .latestChapterIdx`
            lastChapterDir=`printf "%03d" $lastChapterId`
            chapterDirs=`ls -l $dirPath|grep -E "^dr"|awk '{print $NF}'|grep -E "^[0-9]"|grep -v -F "-"`
            for chapterDir in $chapterDirs
            do
                if [ "$chapterDir" -gt "$lastChapterDir" ]
                then
                    echo "rm -rf $dirPath/$chapterDir"
                    rm -rf $dirPath/$chapterDir
                fi
            done
        fi
    fi
done


exit 0

