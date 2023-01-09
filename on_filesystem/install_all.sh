#!/bin/bash
if [ $# -eq 1 ];
then
    for file in `ls $2`
    do
        if [ -d $file ]
        then
            for sub_file in `ls $file`
            do
                if [ -d $file/$sub_file ]
                then
                    echo "Skip directory $file/$sub_file"
                else
                    echo "Start install package $file/$sub_file"
                    adb install $file/$sub_file
                fi
            done
        else
            echo "Start install package $file"
            adb install $file
        fi
    done
else
    echo "install_all.sh: Missing parameters, usage: install_all.sh folder"
fi
echo "Exit..."