import os
import sys
import json
from androguard.core.apk import APK
from androguard.core.dex import DEX

def find_aidl_in_dex(dex_bytes):
    aidl_file = []
    dex = DEX(dex_bytes)
    for clazz in dex.get_classes():
        if 'Landroid/os/IInterface;' == clazz.get_superclassname():
            aidl_name = clazz.get_name()
            aidl_method = []
            for method in clazz.get_methods():
                aidl_method.append(method.get_short_string())
            aidl_file.append({
                'aidl_name': aidl_name,
                'aidl_method': aidl_method
            })
    return aidl_file

def find_aidl(apk_obj):
    aidl_file = []
    for dex_bytes in apk_obj.get_all_dex():
        aidl_file_dex = find_aidl_in_dex(dex_bytes)
        aidl_file = aidl_file + aidl_file_dex

def process_apk(apk_file):
    apk_obj = APK(apk_file)
    aidl_file = find_aidl(apk_obj)
        
    result = {
        'aidl_file': aidl_file
    }
    return result

def scan_dir(packages_dir):
    final_result = []
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
                            final_result.append({
                                'file': package + os.sep + file,
                                'aidl_result': result
                            })
                            print('Scan file success: '+ apk_file)
                        except Exception as e:
                            print('Scan file '+ apk_file + ' error, reason: ' + str(e))
                            continue
        elif package.endswith('.apk'):
            apk_file = package_dir
            if os.path.isfile(apk_file):
                try:
                    result = process_apk(apk_file)
                    final_result.append({
                        'file': package,
                        'aidl_result': result
                    })
                    print('Scan file success: '+ apk_file)
                except Exception as e:
                    print('Scan file '+ apk_file + ' error, reason: ' + str(e))
                    continue
    with open('aidl_result.json', 'w') as f:
        f.write(json.dumps(final_result))

def main():
    test_main()
    # if len(sys.argv) != 2:
    #     print('search_auto_start.py: Missing parameters, usage: python search_auto_start.py dir')
    #     sys.exit(1)
    # scan_dir(sys.argv[1])

def test_main():
    result = process_apk('C:\\Users\\xiaolu\\RawContent\\ROM\\Android\\Honor\\PGT-AN00_8.0.0.127\\packages\\android\\framework.jar')
    print(result)

if __name__ == '__main__':
    main()
