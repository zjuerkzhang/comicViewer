#!/bin/sh

filePath=$0
fileDir=`dirname $filePath`
cd $fileDir
comicRootDir="../comic/00-连载中/"

scripts="/home/pi/github/comicViewer/utils/clImages/clImageAutoFetcher.sh \
        /home/pi/github/comicViewer/utils/hm7mjImages/work.sh \
        /home/pi/github/comicViewer/utils/twhmImages/work.sh \
        /home/pi/github/comicViewer/utils/yxhmImages/work.sh"

for s in $scripts
do
    pidStr=`ps aux|grep -F "$s"|grep -v grep`
    if [ -z "$pidStr" ]
    then
        echo "\n\n=== execute $s ===\n\n"
        /bin/sh "$s"
    else
        echo "\n\n=== $s is running, skip ===\n\n"
    fi
done

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
/bin/sh /home/pi/github/comicViewer/utils/clImages/clImageAutoFetcher.sh
/bin/sh /home/pi/github/comicViewer/utils/hm5wcImages/work.sh
/bin/sh /home/pi/github/comicViewer/utils/hm7mjImages/work.sh
/bin/sh /home/pi/github/comicViewer/utils/twhmImages/work.sh
/bin/sh /home/pi/github/comicViewer/utils/yxhmImages/work.sh

