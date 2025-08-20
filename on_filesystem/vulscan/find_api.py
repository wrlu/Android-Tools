import os
import sys
from androguard.misc import AnalyzeAPK

def process_apk(apk_file, api_name):
    print('Start analysis apk file: '+apk_file)
    try:
        a, d, dx = AnalyzeAPK(apk_file)
        for method in dx.get_methods():
            if method.is_external():
                continue
            for _, called_method in method.get_xref_to():
                if called_method.name == api_name:
                    print('Found API: ' + api_name + ' in apk: ' + apk_file)
                    return True
        return False
    except Exception as e:
        print('Error processing apk file: ' + apk_file + ', error: ' + str(e))
        

def scan_dir(packages_dir, api_name):
    final_result = []

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
                if file.endswith('.apk'):
                    apk_file = package_dir + os.sep + file
                    if os.path.isfile(apk_file):
                        result = process_apk(apk_file, api_name)
                        if result == True:
                            final_result.append(apk_file)
                        
        elif os.path.isfile(package_dir) and package.endswith('.apk'):
            apk_file = package_dir
            result = process_apk(apk_file, api_name)
            if result == True:
                final_result.append(apk_file)
                
    return final_result

def main():
    if len(sys.argv) != 3:
        print('find_api.py: Missing parameters, usage: python find_api.py dir api_name')
        sys.exit(1)
    
    final_result = scan_dir(sys.argv[1] + os.sep + 'packages', sys.argv[2])
    with open(sys.argv[1] + os.sep + 'final_result.txt', 'w') as f:
        for result in final_result:
            f.write(result + '\n')
    
if __name__ == '__main__':
    main()