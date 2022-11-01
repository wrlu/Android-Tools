import os
import sys
import subprocess
import re

class Log:
    @staticmethod
    def send(msg):
        print('[Send] ' + msg)
    
    @staticmethod
    def print(msg):
        print(msg)

    @staticmethod
    def info(msg):
        print('[Info] ' + msg)

    @staticmethod
    def warn(msg):
        print('\033[0;33m[Warning] ' + msg + '\033[0m')

    @staticmethod
    def error(msg):
        print('\033[0;31m[Error] ' + msg + '\033[0m')

def run_command(cmds, cwd='.'):
    return subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd).communicate()[0]

def cmd_adb_devices():
    return run_command(['adb', 'devices'])

def cmd_getprop_ro_build_fingerprint(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'getprop', 'ro.build.fingerprint'])

def cmd_pm_list_packages(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'pm', 'list', 'packages', '-f', '-U'])

def cmd_service_list(serial_id, su_exec):
    if su_exec:
        return run_command(['adb', '-s', serial_id, 'shell', 'su', '-c', 'service', 'list'])
    else:
        return run_command(['adb', '-s', serial_id, 'shell', 'service', 'list'])

def cmd_lshal(serial_id, su_exec):
    if su_exec:
        return run_command(['adb', '-s', serial_id, 'shell', 'su', '-c', 'lshal'])
    else:
        return run_command(['adb', '-s', serial_id, 'shell', 'lshal'])

def cmd_netstat_nlptu(serial_id, su_exec):
    if su_exec:
        return run_command(['adb', '-s', serial_id, 'shell', 'su', '-c', 'netstat', '-nlptu'])
    else:
        return run_command(['adb', '-s', serial_id, 'shell', 'su', '-c', 'netstat', '-nlptu'])

def cmd_pm_dump_signatures(serial_id, package_name):
    return run_command(['adb', '-s', serial_id, 'shell', 'pm', 'dump', package_name, '|', 'grep', 'signatures:'])

def cmd_pm_dump_flag_system(serial_id, package_name):
    return run_command(['adb', '-s', serial_id, 'shell', 'pm', 'dump', package_name, '|', 'grep', 'FLAG_SYSTEM'])

def cmd_adb_root(serial_id):
    return run_command(['adb', '-s', serial_id, 'root'])

def cmd_whoami(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'whoami'])

def cmd_su_whoami(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'su', '-c', 'whoami'])

def dump_apk_folder(serial_id, package):
    run_command(['adb', '-s', serial_id, 'pull', package['path'][:package['path'].rindex('/')], package['package_name']], cwd='packages')

def dump_system_lib(serial_id):
    run_command(['adb', '-s', serial_id, 'pull', '/system/lib64/'], cwd='system_libs')
    run_command(['adb', '-s', serial_id, 'pull', '/system/lib/'], cwd='system_libs')
    
def dump_vendor_lib(serial_id):
    run_command(['adb', '-s', serial_id, 'pull', '/vendor/lib64/'], cwd='vendor_libs')
    run_command(['adb', '-s', serial_id, 'pull', '/vendor/lib/'], cwd='vendor_libs')

def dump_system_bin(serial_id):
    run_command(['adb', '-s', serial_id, 'pull', '/system/bin/'], cwd='system_binaries')

def dump_vendor_bin(serial_id):
    run_command(['adb', '-s', serial_id, 'pull', '/vendor/bin/'], cwd='vendor_binaries')

def dump_selinux_policy(serial_id):
    run_command(['adb', '-s', serial_id, 'pull', '/sys/fs/selinux/policy'], cwd='selinux')

def get_adb_privilege_status(serial_id):
    cmd_adb_root(serial_id)
    whoami = cmd_whoami(serial_id).decode('ascii').strip()
    if whoami == 'root':
        return 'adb root'
    su_whoami = cmd_su_whoami(serial_id).decode('ascii').strip()
    if su_whoami == 'root':
        return 'su root'
    else:
        return 'shell'

def adb_devices():
    output = cmd_adb_devices().decode('ascii')
    lines = output.split('\n')
    device_serial = []
    for line in lines:
        line = line.strip()
        if '\t' in line:
            id = line.split('\t')[0]
            status = line.split('\t')[1]
            if status == 'device':
                build_fingerprint = cmd_getprop_ro_build_fingerprint(id).decode('ascii').strip()
                root_status = get_adb_privilege_status(id)
            device_serial.append({'id': id, 'status': status, 'build_fingerprint': build_fingerprint, 'root_status': root_status})
    return device_serial

def select_adb_devices():
    devices = adb_devices()
    i = 1
    Log.print('Select an adb device:')
    for device in devices:
        if device['status'] == 'device':
            Log.print(str(i) + ' => ' + device['id'] + '\t' + device['build_fingerprint'] + '\t' + device['root_status'])
        else:
            Log.print(str(i) + ' => ' + device['id'] + '\t' + device['status'])
        i = i + 1
    select = int(input())
    if select > len(devices):
        Log.error('Out of range.')
        return None
    if devices[select - 1]['status'] != 'device':
        Log.warn('Device not avaliable, status is: ' + devices[select - 1]['status'])
    return devices[select - 1]

def is_privileged(package):
    return 'priv-app' in package['path']

def get_package_signature(serial_id, package_name):
    dump_output = cmd_pm_dump_signatures(serial_id, package_name).decode('ascii')
    pattern = r'signatures:\[([0-9a-fA-F, ]*)\]\,'
    search_result = re.search(pattern, dump_output)
    signature = search_result.group(1)
    return signature

def get_platform_signature(serial_id):
    return get_package_signature(serial_id, 'android')

def get_package_selinux_label(serial_id, package, platform_signature):
    if int(package['uid']) == 1000:
        return 'system_app'
    is_platform = platform_signature in get_package_signature(serial_id, package['package_name'])
    is_priv = is_privileged(package)
    if is_platform:
        return 'platform_app'
    if is_priv:
        return 'priv_app'
    return 'untrusted_app'

def get_packages(serial_id):
    platform_signature = get_platform_signature(serial_id)
    pm_list_output = cmd_pm_list_packages(serial_id).decode('ascii')
    lines = pm_list_output.split('\n')
    packages = []
    total = len(lines)
    i = 0
    for line in lines:
        line = line.strip().strip('package:')
        if '=' in line and ' ' in line:
            path = line[:line.rindex('=')]
            package_name = line[line.rindex('=') + 1:line.rindex(' ')]
            uid = line[line.rindex(' ') + 1:].strip('uid:')
            package_info = {}
            package_info['package_name'] = package_name
            package_info['path'] = path
            package_info['uid'] = uid
            package_info['label'] = get_package_selinux_label(serial_id, package_info, platform_signature)
            packages.append(package_info)
            show_progress(i, total, 'Collect package info for ' + package_name)
        i = i + 1
            
    return packages

def show_progress(now, total, msg):
    if total == 0:
        return
    p = (now * 100) // total
    Log.info(' {' + str(p) + '%' + '} ' + msg)


def main():
    is_info_only = False
    if len(sys.argv) == 2 and sys.argv[1] == '--info-only':
        is_info_only = True
        Log.info('--info-only detected: do not dump apks, libraries and binaries.')
    device_info = select_adb_devices()
    serial_id = device_info['id']
    root_status = device_info['root_status']
    su_exec = (root_status == 'su root')

    Log.info('[Task 1] Dump Android framework & Apps')

    packages = get_packages(serial_id)
    os.mkdir('packages')
    package_index_file = open('package_index.csv', 'w')
    package_index_file.write('package_name,path,uid,label\n')
    total = len(packages)
    i = 0
    for package in packages:
        package_index_file.write(package['package_name']+','+package['path']+','+package['uid']+','+package['label']+'\n')
        package_index_file.flush()
        if not is_info_only:
            dump_apk_folder(serial_id, package)
            show_progress(i, total, 'Dump package binaries for ' + package['package_name'])
        i = i + 1
    
    package_index_file.close()

    Log.info('[Task 2] Dump SELinux & seccomp policy')
    os.mkdir('selinux')
    dump_selinux_policy(serial_id)

    Log.info('[Task 3] Run service list cmd')
    service_list_file = open('service_list.txt', 'wb')
    service_list_file.write(cmd_service_list(serial_id, su_exec))
    service_list_file.close()

    Log.info('[Task 4] Run lshal cmd')
    lshal_file = open('lshal.txt', 'wb')
    lshal_file.write(cmd_lshal(serial_id, su_exec))
    lshal_file.close()

    Log.info('[Task 5] Run netstat -nlptu cmd')
    netstat_file = open('netstat.txt', 'wb')
    netstat_file.write(cmd_netstat_nlptu(serial_id, su_exec))
    netstat_file.close()

    if not is_info_only:
        Log.info('[Task 6] Dump libraries')
        os.mkdir('system_libs')
        dump_system_lib(serial_id)
        os.mkdir('vendor_libs')
        dump_vendor_lib(serial_id)

        Log.info('[Task 7] Dump binaries')
        os.mkdir('system_binaries')
        dump_system_bin(serial_id)
        os.mkdir('vendor_binaries')
        dump_vendor_bin(serial_id)


main()