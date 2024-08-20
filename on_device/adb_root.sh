resetprop ro.debuggable 1
resetprop service.adb.root 1
magiskpolicy --live 'allow adbd adbd process setcurrent'
magiskpolicy --live 'allow adbd su process dyntransition'
magiskpolicy --live 'permissive { su }'
kill -9 `ps -A | grep adbd | awk '{print $2}'`
