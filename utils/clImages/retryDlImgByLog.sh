#!/bin/sh

lines=`cat log.log |grep jpg|awk '{print $10"#"$NF}'`

for l in $lines
do
    s=`echo $l|awk -F '#' '{print $1}'`
    d=`echo $l|awk -F '#' '{print $NF}'`
    echo "$s --> $d"
    curl -L $s -o ./images/$d
done