#!/bin/sh
imgDlUrl="https://bloghz.ddns.net/cmd/clImgDler"
link2DirMapFile="./link2DirMap.txt"

rm -f $link2DirMapFile
content=`cat clLinks.txt`
lineNum=`echo "$content"|wc -l`
idxes=`seq $lineNum`
for i in $idxes;
do
    line=`echo "$content"|head -n $i|tail -n 1`;
    link=`echo "$line"|awk '{print $NF}'`;
    title=`echo "$line"|awk -F '第' '{print $2}'|awk -F '话' '{print $1}'|awk -F '話' '{print $1}'`;
    x=`echo $title|grep -F "-"`
    if [ $? -ne 0 ]
    then
        dirName=`printf "%03d" $title`
    else
        start=`echo $title|awk -F '-' '{print $1}'`
        end=`echo $title|awk -F '-' '{print $2}'`
        dirName=`printf "%03d-%03d" $start $end`
    fi
    echo $dirName $link;
    echo "$dirName $link" >> $link2DirMapFile

    #continue

    curl -s -X POST -d "{\"link\": \"$link\"}" $imgDlUrl --header "Content-Type: application/json"
    echo ""
    sleep 10
done