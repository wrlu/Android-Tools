import os
import subprocess
import re
import argparse
import copy
import json

settings_table = ['global', 'system', 'secure']

class Log:
    @staticmethod
    def send(msg):
        print('[Send] ' + msg)

    @staticmethod
    def print(msg):
        print(msg)

    @staticmethod
    def warn(msg):
        print('\033[0;33m' + msg + '\033[0m')

    @staticmethod
    def error(msg):
        print('\033[0;31m' + msg + '\033[0m')

def run_command(cmds, cwd='.'):
    result = subprocess.run(cmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd, check=False)
    return result.stdout

def adb_cmd_adb_devices():
    return run_command(['adb', 'devices'])

def adb_cmd_getprop_ro_build_fingerprint(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'getprop', 'ro.build.fingerprint'])

def adb_cmd_pm_list_packages_all(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'pm', 'list', 'packages', '--user', '0', '-f', '-U'])

def adb_cmd_pm_list_packages_third(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'pm', 'list', 'packages', '--user', '0', '-f', '-3', '-U'])

def adb_cmd_pm_list_packages_system(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'pm', 'list', 'packages', '--user', '0', '-f', '-s', '-U'])

def adb_cmd_pm_list_packages_apex_only(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'pm', 'list', 'packages', '--user', '0', '-f', '--apex-only'])

def adb_cmd_pm_list_permissions(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'pm', 'list', 'permissions', '-f'])

def adb_cmd_service_list(serial_id, root_status):
    if root_status == 'su_root':
        return run_command(['adb', '-s', serial_id, 'shell', 'su', '-c', 'service', 'list'])
    else:
        return run_command(['adb', '-s', serial_id, 'shell', 'service', 'list'])

def adb_cmd_lshal(serial_id, root_status):
    if root_status == 'su_root':
        return run_command(['adb', '-s', serial_id, 'shell', 'su', '-c', 'lshal'])
    else:
        return run_command(['adb', '-s', serial_id, 'shell', 'lshal'])

def adb_cmd_netstat_nlptu(serial_id, root_status):
    if root_status == 'su_root':
        return run_command(['adb', '-s', serial_id, 'shell', 'su', '-c', 'netstat', '-nlptu'])
    else:
        return run_command(['adb', '-s', serial_id, 'shell', 'su', '-c', 'netstat', '-nlptu'])

def adb_cmd_dumpsys_package(serial_id, package_name):
    return run_command(['adb', '-s', serial_id, 'shell', 'dumpsys', 'package', package_name])

def adb_cmd_adb_root(serial_id):
    return run_command(['adb', '-s', serial_id, 'root'])

def adb_cmd_whoami(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'whoami'])

def adb_cmd_getprop(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'getprop'])

def adb_cmd_su_whoami(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'su', '-c', 'whoami'])

def adb_cmd_mkdir_dump_tmp(serial_id):
    run_command(['adb', '-s', serial_id, 'shell', 'mkdir', '/sdcard/.dump_android_script/'])

def adb_cmd_mkdir_dump_tmp_subdir(serial_id, sub):
    run_command(['adb', '-s', serial_id, 'shell', 'mkdir', '/sdcard/.dump_android_script/' + sub])

def adb_cmd_rm_dump_tmp(serial_id):
    run_command(['adb', '-s', serial_id, 'shell', 'rm', '-rf', '"/sdcard/.dump_android_script"'])

def adb_cmd_settings_list(serial_id, table):
    if table in settings_table:
        return run_command(['adb', '-s', serial_id, 'shell', 'settings', 'list', table])

def dump_apk_folder(serial_id, package):
    apk_folder = package['path'][:package['path'].rindex('/')]
    if package['package_name'] == 'com.miui.rom':
        apk_folder = '/system_ext/framework'
    run_command(['adb', '-s', serial_id, 'pull', apk_folder, package['package_name']], cwd='packages')

def dump_apex_folder(serial_id, apex):
    # Mounted apex path is /apex/{apex_name}, contains readable apex files.
    mounted_apex_path = '/apex/' + apex['apex_name']
    run_command(['adb', '-s', serial_id, 'pull', mounted_apex_path, apex['apex_name']], cwd='apex')

def dump_binary_folder(serial_id, binary_path, partition, cwd, root_status):
    if root_status == 'adb_root':
        dump_binary_folder_directly(serial_id, binary_path, cwd)
    else:
        if root_status == 'su_root':
            run_command(['adb', '-s', serial_id, 'shell', 'su', '-c', 'cp', '-r', binary_path, os.path.join('/sdcard/.dump_android_script/', partition)])
        else:
            run_command(['adb', '-s', serial_id, 'shell', 'cp', '-r', binary_path, os.path.join('/sdcard/.dump_android_script/', partition)])
        run_command(['adb', '-s', serial_id, 'pull', os.path.join('/sdcard/.dump_android_script/', binary_path[1:])], cwd=cwd)

def dump_binary_folder_directly(serial_id, binary_path, cwd):
    run_command(['adb', '-s', serial_id, 'pull', binary_path], cwd=cwd)

def dump_selinux_policy(serial_id):
    run_command(['adb', '-s', serial_id, 'pull', '/sys/fs/selinux/policy'], cwd='selinux')
    run_command(['adb', '-s', serial_id, 'pull', '/system/etc/selinux'], cwd='selinux')

def get_adb_privilege_status(serial_id):
    adb_cmd_adb_root(serial_id)
    whoami = adb_cmd_whoami(serial_id).decode('ascii').strip()
    if whoami == 'root':
        return 'adb_root'
    su_whoami = adb_cmd_su_whoami(serial_id).decode('ascii').strip()
    if su_whoami == 'root':
        return 'su_root'
    else:
        return 'shell'

def adb_devices():
    output = adb_cmd_adb_devices().decode('ascii')
    lines = output.split('\n')
    device_serial = []
    for line in lines:
        line = line.strip()
        if '\t' in line:
            id = line.split('\t')[0]
            status = line.split('\t')[1]
            if status == 'device':
                build_fingerprint = adb_cmd_getprop_ro_build_fingerprint(id).decode('ascii').strip()
                root_status = get_adb_privilege_status(id)
            else:
                build_fingerprint = 'unknown'
                root_status = 'unknown'
            device_serial.append({'id': id, 'status': status, 'build_fingerprint': build_fingerprint, 'root_status': root_status})
    return device_serial

def select_adb_devices(pre_select_val):
    devices = adb_devices()
    i = 1
    Log.print('Please select an adb device:')
    for device in devices:
        if device['status'] == 'device':
            Log.print(str(i) + ' => ' + device['id'] + '\t' + device['build_fingerprint'] + '\t' + device['root_status'])
        else:
            Log.print(str(i) + ' => ' + device['id'] + '\t' + device['status'])
        i = i + 1
    if pre_select_val == -1:
        select = int(input())
    else:
        select = pre_select_val
    Log.print('You select device on line '+str(select))
    if select > len(devices):
        Log.error('Out of range.')
        return None
    if devices[select - 1]['status'] != 'device':
        Log.warn('Device not avaliable, status is: ' + devices[select - 1]['status'])
        return None
    if devices[select - 1]['root_status'] == 'shell':
        Log.warn('Non-root device, can only dump less binaries & libraries due to permission issue.')
    return devices[select - 1]

def is_privileged(package_info):
    return 'priv-app' in package_info['path']

def get_package_signature(dumpsys_package_output):
    pattern = r'signatures:\[([0-9a-fA-F, ]*)\]\,'
    search_result = re.search(pattern, dumpsys_package_output.decode('utf8'))
    signature = search_result.group(1)
    return signature

def get_package_selinux_label(package_info, dumpsys_package_output, platform_signature):
    if int(package_info['uid']) == 1000:
        return 'system_app'
    is_platform = platform_signature in get_package_signature(dumpsys_package_output)
    is_priv = is_privileged(package_info)
    if is_platform:
        return 'platform_app'
    if is_priv:
        return 'priv_app'
    return 'untrusted_app'

def get_packages(serial_id, pkg_filter_mode):
    if pkg_filter_mode == 1:
        pm_list_output = adb_cmd_pm_list_packages_system(serial_id).decode('ascii')
    elif pkg_filter_mode == 2:
        pm_list_output = adb_cmd_pm_list_packages_third(serial_id).decode('ascii')
    else:
        pm_list_output = adb_cmd_pm_list_packages_all(serial_id).decode('ascii')
    lines = pm_list_output.split('\n')
    packages = []
    total = len(lines)
    i = 0
    android_dumpsys_package_output = adb_cmd_dumpsys_package(serial_id, 'android')
    platform_signature = get_package_signature(android_dumpsys_package_output)
    for line in lines:
        line = line.strip().strip('package:')
        if '=' in line and ' ' in line:
            path = line[:line.rindex('=')]
            package_name = line[line.rindex('=') + 1:line.rindex(' ')]
            uid = line[line.rindex(' ') + 1:].strip('uid:')
            if ',' in uid:
                uid = uid.split(',')[0]
            package_dumpsys_package_output = adb_cmd_dumpsys_package(serial_id, package_name)
            package_info = {}
            package_info['package_name'] = package_name
            package_info['path'] = path
            package_info['uid'] = uid
            package_info['label'] = get_package_selinux_label(package_info, package_dumpsys_package_output, platform_signature)
            packages.append(package_info)
            show_progress(i, total, 'Collect package info for ' + package_name)
        i = i + 1
    return packages

def get_apex(serial_id):
    pm_list_output = adb_cmd_pm_list_packages_apex_only(serial_id).decode('ascii')
    lines = pm_list_output.split('\n')
    apexs = []
    for line in lines:
        line = line.strip().strip('package:')
        if '=' in line:
            path = line[:line.rindex('=')]
            apex_name = line[line.rindex('=') + 1:]
            apex_info = {}
            apex_info['apex_name'] = apex_name
            apex_info['path'] = path
            apexs.append(apex_info)
    return apexs

def show_progress(now, total, msg):
    if total == 0:
        return
    p = (now * 100) // total
    Log.print('[' + str(p) + '%' + '] ' + msg)


def gen_jadx_project_file(packages_dir):
    jadx_file_templete = {
        "projectVersion": 1,
        "files": [],
    }
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
    parser = argparse.ArgumentParser(description='Dump useful files from Android devices.')
    parser.add_argument('-m', '--metadata', action='store_true', help='Dump metadata only without any binaries.')
    parser.add_argument('-j', '--jadx', action='store_true', help='Generate jadx project files for every package.')
    exclusive_group = parser.add_mutually_exclusive_group()
    exclusive_group.add_argument('-s', '--system', action='store_true', help='Only dump system packages.')
    exclusive_group.add_argument('-3', '--third-party', action='store_true', help='Only dump third party packages.')
    args = parser.parse_args()

    metadata_only = args.metadata
    is_system = args.system
    is_third = args.third_party
    gen_jadx = args.jadx

    pkg_filter_mode = 0
    if is_system:
        pkg_filter_mode = 1
        Log.print('-s or --system: will only dump system packages.')
    elif is_third:
        pkg_filter_mode = 2
        Log.print('-3 or --third-party detected: will only dump third party packages.')
    if gen_jadx:
        Log.print('-j or --jadx detected: will generate jadx project files.')
    if metadata_only:
        Log.print('-m or --metadata detected: will only dump metadata without any binaries.')

    device_info = select_adb_devices(-1)
    if device_info == None:
        return
    serial_id = device_info['id']
    root_status = device_info['root_status']

    Log.print('[Task 1] Dump Android framework & Apps')

    packages = get_packages(serial_id, pkg_filter_mode)
    os.makedirs('packages', exist_ok=True)
    with open('package_index.csv', 'w') as f:
        f.write('package_name,path,uid,label\n')
        total = len(packages)
        i = 0
        for package in packages:
            f.write(package['package_name']+','+package['path']+','+package['uid']+','+package['label']+'\n')
            f.flush()
            if not metadata_only:
                dump_apk_folder(serial_id, package)
                show_progress(i, total, 'Dump package binaries for ' + package['package_name'])
            i = i + 1
    
    if gen_jadx:
        gen_jadx_project_file('packages')

    if pkg_filter_mode != 2:
        apexs = get_apex(serial_id)
        os.makedirs('apex', exist_ok=True)
        with open('apex_index.csv', 'w') as f:
            f.write('apex_name,path\n')
            total = len(apexs)
            i = 0
            for apex in apexs:
                f.write(apex['apex_name']+','+apex['path']+'\n')
                f.flush()
                if not metadata_only:
                    dump_apex_folder(serial_id, apex)
                    show_progress(i, total, 'Dump apex binaries for ' + apex['apex_name'])
                i = i + 1
    else:
        return
   
    
    Log.print('[Task 2] Dump SELinux & seccomp policy')
    os.makedirs('selinux', exist_ok=True)
    dump_selinux_policy(serial_id)

    Log.print('[Task 3] Run useful commands')
    with open('service_list.txt', 'wb') as f:
        f.write(adb_cmd_service_list(serial_id, root_status))
    
    with open('lshal.txt', 'wb') as f:
        f.write(adb_cmd_lshal(serial_id, root_status))

    with open('netstat.txt', 'wb') as f:
        f.write(adb_cmd_netstat_nlptu(serial_id, root_status))

    with open('getprop.txt', 'wb') as f:
        f.write(adb_cmd_getprop(serial_id))
    
    with open('permissions.txt', 'wb') as f:
        f.write(adb_cmd_pm_list_permissions(serial_id))

    for table in settings_table:
        with open('settings_' + table + '.txt', 'wb') as f:
            f.write(adb_cmd_settings_list(serial_id, table))

    if not metadata_only:
        os.makedirs('system_libs', exist_ok=True)
        os.makedirs('vendor_libs', exist_ok=True)
        os.makedirs('system_binaries', exist_ok=True)
        os.makedirs('vendor_binaries', exist_ok=True)
        if root_status != 'adb_root':
            adb_cmd_mkdir_dump_tmp(serial_id)
            adb_cmd_mkdir_dump_tmp_subdir(serial_id, 'system')
            adb_cmd_mkdir_dump_tmp_subdir(serial_id, 'vendor')
        
        Log.print('[Task 4] Dump libraries')
        dump_binary_folder_directly(serial_id, '/system/lib64/', 'system_libs')
        dump_binary_folder_directly(serial_id, '/system/lib/', 'system_libs')
        dump_binary_folder(serial_id, '/vendor/lib64/', 'vendor', 'vendor_libs', root_status)
        dump_binary_folder(serial_id, '/vendor/lib/', 'vendor', 'vendor_libs', root_status)

        Log.print('[Task 5] Dump binaries')
        dump_binary_folder(serial_id, '/system/bin/', 'system', 'system_binaries', root_status)
        dump_binary_folder(serial_id, '/vendor/bin/', 'vendor', 'vendor_binaries', root_status)

        if root_status != 'adb_root':
            adb_cmd_rm_dump_tmp(serial_id)
    
    Log.print('[Task 4] Initial anaylsis')

        
    Log.print('Done')    

if __name__ == '__main__':
    main()