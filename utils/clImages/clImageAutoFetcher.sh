#!/bin/sh
cd /home/pi/github/comicViewer/utils/clImages
link2DirMapFile="../link2DirMap.txt"
logFile="log.log"

generate_img_dir_by_config_file()
{
    configFileName=$1
    dirName=`echo $configFileName|awk -F '.' '{print $1}'`
    return 0
}

generate_img_dir_by_page_title()
{
    dirName=''
    if [ -e $link2DirMapFile ]
    then
        configFileName=$1
        pageLink=`cat config/$configFileName|grep pageLink|awk -F '"pageLink"' '{print $NF}'|awk -F '"' '{print $2}'`
        if [ -z "$pageLink" ]
        then
            return 1
        fi
        line=`cat $link2DirMapFile|grep -F "$pageLink"`
        if [ -z "$line" ]
        then
            return 1
        fi
        dirName=`echo $line|awk '{print $1}'`
        return 0
    else
        return 1
    fi


}

notifier_url='https://bloghz.ddns.net/cmd/notify/'

configFileList='configFiles.list'
echo "-------------------------"
echo `date`

scp -P 26639 root@bloghz.ddns.net:/root/clImages/config/*.json config/
configFiles=`ls config`

notifyContent=''
for cf in $configFiles
do
    #[to del] dirName=`echo $cf|awk -F '.' '{print $1}'`
    generate_img_dir_by_page_title $cf
    if [ $? -ne 0 ]
    then
        generate_img_dir_by_config_file $cf
    fi
    echo "$cf --> $dirName"

    if [ -d "images/$dirName" ]
    then
        #echo "images/$dirName already exists, skip downloading images"
        continue
    fi
    grepStr=`grep "$cf" $configFileList`
    if [ -n "$grepStr" ]
    then
        #echo "$cf already handled, skip downloading images"
	continue
    fi
    echo "`date`: create images/$dirName and download images" >> $logFile
    mkdir images/$dirName
    links=`cat config/$cf|grep http|grep -v pageLink|awk -F '"' '{print $2}'`
    title=`cat config/$cf|grep '"title":'|awk -F ':' '{print $NF}'|tr ' ' '_'|awk -F '"' '{print $2}'`
    pageLink=`cat config/$cf|grep pageLink|awk -F '"' '{print $4}'`
    echo "$title [$pageLink]" >> $logFile
    partlySuccess=0
    echo "$pageLink" > images/$dirName/$title.txt
    ifNameIdx=1
    for l in $links
    do
        #ifName=`echo $l|awk -F '/' '{print $NF}'`
        ext=`echo "$l"|awk -F '.' '{print $NF}'`
        ifName=`printf "%03d.%s" $ifNameIdx $ext`
        echo "$l --> $ifName"
        #wget -q -T 30 $l -O images/$dirName/$ifName
        retryTimes=`seq 5`
        imgDownloadFailed=1
        proxyFlag=""
        for i in $retryTimes
        do
            if [ $i -gt 2 ]
            then
                proxyFlag="-x http://127.0.0.1:8080"
            fi
            curl -s -L -m 30 $proxyFlag -o images/$dirName/$ifName $l
            if [ $? -eq 0 ]
            then
                imgDownloadFailed=0
                break
                sleep 5
            fi
        done
        if [ $imgDownloadFailed -eq 1 ]
        then
            echo "`date`: Fail to download $l --> $dirName/$ifName" >> $logFile
            partlySuccess=1
        fi
        ifNameIdx=`expr $ifNameIdx + 1`
        sleep 1
    done
    echo $cf >> $configFileList
    notifyContent="$notifyContent$dirName\n$title\n"
    if [ $partlySuccess -eq 1 ]
    then
        notifyContent="$notifyContent   [Partly Successful]\n"
    fi
    sleep 10
done
if [ -n "$notifyContent" ]
then
    echo "Finished"
    curl -s -X POST -d "{\"subject\": \"Caoliu Image Download\", \"content\": \"$notifyContent\", \"channel\": \"telegram\"}" $notifier_url --header "Content-Type: application/json"
fi
echo "-------------------------"
