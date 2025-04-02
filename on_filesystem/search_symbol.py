import os
import sys
from androguard.core.bytecodes.apk import APK
from androguard.core.bytecodes.dvm import DalvikVMFormat

def match_filter(str):
    return False

def find_string_in_apk(apk_obj, file, matcher):
    all_matched_strings = []
    for dex_bytes in apk_obj.get_all_dex():
        dex_vm = DalvikVMFormat(dex_bytes)
        for str in dex_vm.get_strings():
            if matcher(str):
                all_matched_strings.append({'find': str, 'file': file})
    return all_matched_strings

def process_apk(apk_file):
    apk_obj = APK(apk_file)
    return find_string_in_apk(apk_obj, apk_file, match_filter)

def scan_dir(packages_dir):
    all_matched_strings = []
    for package in os.listdir(packages_dir):
        if 'auto_generated_rro_product' in package:
            print('Skip auto_generated_rro_product: ' + package)
            continue
        package_dir = packages_dir + os.sep + package
        if os.path.isdir(package_dir):
            for file in os.listdir(package_dir):
                if 'auto_generated_rro_product' in file:
                    print('Skip auto_generated_rro_product apk: ' + file)
                    continue
                full_filename = package_dir + os.sep + file
                if os.path.isfile(full_filename) and (file.endswith('.apk') or file.endswith('.jar') or file.endswith('.dex')):
                    try:
                        result = process_apk(full_filename)
                        if len(result) > 0:
                            all_matched_strings = all_matched_strings + result
                        print('Scan file success: '+ full_filename)
                    except Exception as e:
                        print('Scan file '+ full_filename + ' error, reason: ' + str(e))
                        continue
        elif os.path.isfile(package_dir) and package.endswith('.apk'):
            apk_file = package_dir
            try:
                result = process_apk(apk_file)
                if len(result) > 0:
                    all_matched_strings = all_matched_strings + result
                print('Scan file success: '+ apk_file)
            except Exception as e:
                print('Scan file '+ apk_file + ' error, reason: ' + str(e))
                continue
    print(all_matched_strings)

def main():
    if len(sys.argv) != 2:
        print('search_symbol.py: Missing parameters, usage: python search_symbol.py dir')
        sys.exit(1)
    scan_dir(sys.argv[1])

if __name__ == '__main__':
    main()
