import sys
import os
import subprocess

android_framework_jar = '/home/xiaolu/Android/Sdk/platforms/android-30/android.jar'

def start_anaylsis(target, stdout, stderr):
    stdout.write('## ' + target + os.linesep)
    stderr.write('Error of ' + target + os.linesep)
    stdout.flush()
    stderr.flush()
    subprocess.run(['java', '-jar', './piscan.jar', '-f', target, '-a', android_framework_jar], stdout=stdout, stderr=stderr)

if len(sys.argv) >= 2:
    if len(sys.argv) > 2:
        print('[Warning] received ' + sys.argv - 1 + ' parameters, ignored ' + sys.argv - 2 + '.')
        print('[Info] Usage: piscan.py folder.')
    working_dir = sys.argv[1]

    result_log_file = open('result.log', 'a+')
    # result_log_file = sys.stdout
    error_log_file = open('error.log', 'a+')
    # error_log_file = open('/dev/null', 'w')
    
    for file in os.listdir(working_dir):
        full_file_path = working_dir + os.sep + file
        if os.path.isdir(full_file_path):
            default_apk_file = full_file_path + os.sep + file + '.apk'
            if os.path.isfile(default_apk_file):
                print('[Debug] Start anaylsis ' + default_apk_file)
                start_anaylsis(default_apk_file, result_log_file, error_log_file)
            else:
                print('[Info] ' + file + ' is a Harmony OS application folder, use full scan mode.')
                for sub_file in os.listdir(full_file_path):
                    full_sub_file = full_file_path + os.sep + sub_file
                    if os.path.isfile(full_sub_file) and (sub_file.endswith('.apk') or sub_file.endswith('.hap')):
                        print('[Debug] Start anaylsis ' + full_sub_file)
                        start_anaylsis(full_sub_file, result_log_file, error_log_file)
                    else:
                        print('[Info] Ignore non apk or hap file ' + file)

        else:
            print('[Info] Ignore regular file ' + file)

    result_log_file.close()
    error_log_file.close()
    
else:
    print('[Error] Missing parameters.')
    print('[Info] Usage: piscan.py folder.')

print('Stop.')