#!/bin/bash
if [ $# -eq 1 ];
then
    echo "Foreground & Single Thread Mode..."
    for file in `ls $1`
    do
        if [ -d $file ]
        then
            (cd $1"/"$file;repo sync)
        else
            echo "Skip file $file"
        fi
    done
elif [ $# -eq 2 ];
then
    if [ "$2" == "-b" ];
    then
        echo "Background & Muti-Thread Mode..."
        for file in `ls $1`
        do
            if [ -d $file ]
            then
                (cd $1"/"$file; repo sync 2>&1 > ../sync_"$file".log &)
            else
                echo "Skip file $file"
            fi
        done
    else
        echo "repo_sync_all.sh: Wrong parameters, usage: repo_sync_all.sh folder [-b]."
        echo "Tips: You can use -b parameter to sync in background."
    fi
else
    echo "repo_sync_all.sh: Missing parameters, usage: repo_sync_all.sh folder [-b]."
    echo "Tips: You can use -b parameter to sync in background & muti-thread."
fi
echo "Exit..."