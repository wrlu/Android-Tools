import os
import sys
import copy
import json

jadx_file_templete = {
  "projectVersion": 1,
  "files": [],
}

def scan_dir(packages_dir):
    for package in os.listdir(packages_dir):
        if 'auto_generated_rro_product' in package:
            print('Skip auto_generated_rro_product: ' + package)
            continue
        package_dir = packages_dir + os.sep + package
        if os.path.isdir(package_dir):
            jadx_file = package_dir + os.sep + package + ".jadx"
            jadx_file_content = copy.deepcopy(jadx_file_templete)

            for file in os.listdir(package_dir):
                full_filename = package_dir + os.sep + file
                if 'auto_generated_rro_product' in file:
                    print('Skip auto_generated_rro_product apk: ' + file)
                    continue
                if os.path.isfile(full_filename) and (file.endswith('.apk') or file.endswith('.jar') or file.endswith('.dex')):
                    jadx_file_content['files'].append(file)
            
            with open(jadx_file, 'w') as f:
                json.dump(jadx_file_content, f)

def main():
    if len(sys.argv) != 2:
        print('jadx_file_gen.py: Missing parameters, usage: python jadx_file_gen.py dir')
        sys.exit(1)
    scan_dir(sys.argv[1] + os.sep + 'packages')
    
if __name__ == '__main__':
    main()