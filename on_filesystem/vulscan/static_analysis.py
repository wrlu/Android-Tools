import os
import sys
import subprocess
import re
import json

output_dir = 'output'
run_id = 0

def run_command(cmds, cwd='.'):
    return subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd).communicate()[0]

def run_mariana_trench_tool(apk_file, output_dir):
    cmd_out = run_command(['/mnt/c/Users/xiaolu/Repos/Tools/mariana-trench/analyze.sh', apk_file, output_dir])
    pattern = re.compile(rb'Saving [0-9]+ issues')
    match_list = pattern.findall(cmd_out)
    if len(match_list) > 0:
        print(match_list[0].decode('utf8'))
    else:
        print('[ERROR] Cannot detect saving issues count in command output.')

def process_apk(apk_file):
    global run_id
    run_mariana_trench_tool(apk_file, output_dir)
    run_id = run_id + 1

def scan_dir(packages_dir):
    run_id_mapping = {}
    os.mkdir(output_dir)
    for package in os.listdir(packages_dir):
        if 'auto_generated_rro_product' in package:
            print('Skip auto_generated_rro_product: ' + package)
            continue
        package_dir = packages_dir + os.sep + package
        if os.path.isdir(package_dir):
            for file in os.listdir(package_dir):
                if file.endswith('.apk') or file.endswith('.jar') or file.endswith('.dex'):
                    apk_file = package_dir + os.sep + file
                    if os.path.isfile(apk_file):
                        try:
                            process_apk(apk_file)
                            run_id_mapping[run_id] = apk_file
                            print('Scan file success: '+ apk_file)
                        except Exception as e:
                            print('Scan file '+ apk_file + ' error, reason: ' + str(e))
                            continue
        elif package.endswith('.apk'):
            apk_file = package_dir
            if os.path.isfile(apk_file):
                try:
                    process_apk(apk_file)
                    run_id_mapping[run_id] = apk_file
                    print('Scan file success: '+ apk_file)
                except Exception as e:
                    print('Scan file '+ apk_file + ' error, reason: ' + str(e))
                    continue
    with open('sapp_db.mapping', 'w') as f:
        f.write(json.dumps(run_id_mapping))

def main():
    if len(sys.argv) != 2:
        print('static_analysis.py: Missing parameters, usage: python static_analysis.py dir')
        sys.exit(1)
    scan_dir(sys.argv[1])

if __name__ == '__main__':
    main()
