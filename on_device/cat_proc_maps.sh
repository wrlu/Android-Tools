#!/bin/bash
if [ $# -eq 1 ];
then
    ps -AZ -p 1 -o USER,UID,PID,PPID,NAME | grep LABEL
    for pid in $(ps -Ao PID)
    do
        if [ "$pid" == "PID" ];
        then
            continue
        fi
        if [ $pid -eq $$ ];
        then
            continue
        fi
        cat /proc/$pid/maps | grep $1 2>&1 > /dev/null
        if [ $? -eq 0 ];
        then
            ps -AZ -p $pid -o USER,UID,PID,PPID,NAME | grep $pid
        fi
    done
else
    echo "cat_proc_maps.sh: Missing parameters, usage: cat_proc_maps.sh module_name."
fi