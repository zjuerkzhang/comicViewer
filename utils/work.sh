#!/bin/sh

scripts="/home/pi/github/comicViewer/utils/clImages/clImageAutoFetcher.sh \
        /home/pi/github/comicViewer/utils/hm7mjImages/work.sh \
        /home/pi/github/comicViewer/utils/hm5wcImages/work.sh \
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

exit 0
/bin/sh /home/pi/github/comicViewer/utils/clImages/clImageAutoFetcher.sh
/bin/sh /home/pi/github/comicViewer/utils/hm5wcImages/work.sh
/bin/sh /home/pi/github/comicViewer/utils/twhmImages/work.sh
/bin/sh /home/pi/github/comicViewer/utils/yxhmImages/work.sh

