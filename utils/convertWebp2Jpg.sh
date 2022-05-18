#!/bin/sh

comicDir="$1"
if [ -z "$comicDir" ]
then
    echo ">> Missing parameter: comic directory"
    exit 1
fi

cd $1

dirs=`ls`
for d in $dirs
do
    if [ -d "$d" ]
    then
        echo "=== $d ==="
        files=`ls $d`
        for f in $files
        do
            filename=`echo $f|awk -F '.' '{print $1}'`
            ext=`echo $f|awk -F '.' '{print $2}'`
            if [ "$ext" != "jpg" ]
            then
                continue
            fi
            x=`file $d/$f|grep -F "Web/P image"`
            if [ -n "$x" ]
            then
                if [ -e "$d/filename.webp" ]
                then
                    echo "[$d/$filename.webp] exists, skip ..."
                else
                    echo "cp [$f] to [$d/$filename.webp]"
                    cp $d/$f $d/$filename.webp
                fi
                echo "convert from [$d/$f] to [$d/$filename.jpg]"
                convert $d/$f $d/$filename.jpg
            fi
        done
    fi
done