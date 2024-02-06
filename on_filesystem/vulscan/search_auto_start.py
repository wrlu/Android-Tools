import os
import sys
import json
from androguard.core.bytecodes.apk import APK
from androguard.core.bytecodes.dvm import DalvikVMFormat

def match_content_filter(str):
    if str.startswith('content://'):
        if str.replace('content://', '') == '':
            return False
        elif str.startswith('content://sms') or \
            str.startswith('content://mms') or \
            str.startswith('content://media') or \
            str.startswith('content://settings') or \
            str.startswith('content://download') or \
            str.startswith('content://icc') or \
            str.startswith('content://telephony') or \
            str.startswith('content://com.tencent.mm') or \
            str.startswith('content://call_log'):
            return False
        else:
            return True
    else:
        return False

def find_string_in_apk(apk_obj, file, matcher):
    all_matched_strings = []
    for dex_bytes in apk_obj.get_all_dex():
        dex_vm = DalvikVMFormat(dex_bytes)
        for str in dex_vm.get_strings():
            if matcher(str):
                all_matched_strings.append({'string': str, 'file': file})
    return all_matched_strings

def process_apk(apk_file):
    apk_obj = APK(apk_file)
    apk_providers = list(apk_obj.get_all_attribute_value("provider", "authorities"))
    apk_content_strings = find_string_in_apk(apk_obj, apk_file, match_content_filter)
    result = {
        'providers': apk_providers,
        'content_strings': apk_content_strings
    }
    return result

def scan_dir(packages_dir):
    all_providers = []
    all_content_strings = []
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
                            result = process_apk(apk_file)
                            all_providers = all_providers + result['providers']
                            all_content_strings = all_content_strings + result['content_strings']
                            print('Scan file success: '+ apk_file)
                        except Exception as e:
                            print('Scan file '+ apk_file + ' error, reason: ' + str(e))
                            continue
        elif package.endswith('.apk'):
            apk_file = package_dir
            if os.path.isfile(apk_file):
                try:
                    result = process_apk(apk_file)
                    all_providers = all_providers + result['providers']
                    all_content_strings = all_content_strings + result['content_strings']
                    print('Scan file success: '+ apk_file)
                except Exception as e:
                    print('Scan file '+ apk_file + ' error, reason: ' + str(e))
                    continue
    with open('all_content_strings_oppo.json', 'w') as f:
        f.write(json.dumps(all_content_strings))
    with open('all_providers_oppo.json', 'w') as f:
        f.write(json.dumps(all_providers))
    matched_content_strings = []
    for content_string in all_content_strings:
        contains = False
        for provider in all_providers:
            # Provider may use multiple authorities and will split by `;`
            if ';' in provider:
                multi_providers = provider.split(';')
                for per_multi_provider in multi_providers:
                    if per_multi_provider in content_string['string'] and per_multi_provider != '':
                        contains = True
                        break
            else:
                if provider in content_string['string']:
                    contains = True
                    break
        if not contains:
            matched_content_strings.append(content_string)
            print(content_string)
    with open('matched_content_strings_oppo.json', 'w') as f:
        f.write(json.dumps(matched_content_strings))

def main():
    if len(sys.argv) != 2:
        print('search_auto_start.py: Missing parameters, usage: python search_auto_start.py dir')
        sys.exit(1)
    scan_dir(sys.argv[1])

if __name__ == '__main__':
    main()
