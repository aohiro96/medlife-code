#!/bin/sh

processName=$1
restartFile=$2
interval=600

while true
do
    isAlive=`ps -ef | grep "$processName" | grep -v grep | grep -v srvchk | wc -l`
    if [ $isAlive = 1 ]; then
        echo "Server is running."
    else
        echo "Server is dead, restarting..."
        $restartFile
    fi
    sleep $interval
done
