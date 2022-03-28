if [ $# -eq 2 ];
then
    for file in `ls $2`
    do
        if [ -d $file ]
            then
                echo "Skip directory $file"
            else
                cat $file | grep -a $1 2>&1 > /dev/null
                if [ $? -eq 0 ];
                then
                    echo "[*] Found symbol in $file"
                fi
            fi
    done
else
    echo "search_symbol.sh: Missing parameters, usage: search_symbol.sh search folder"
fi
echo "Exit..."