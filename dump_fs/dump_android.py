import os
import sys
import subprocess
import re

def run_command(cmds, cwd='.'):
    return subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd).communicate()[0]

def cmd_adb_devices():
    return run_command(['adb', 'devices'])

def cmd_getprop_ro_build_fingerprint(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'getprop', 'ro.build.fingerprint'])

def cmd_pm_list_packages(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'pm', 'list', 'packages', '-f', '-U'])

def cmd_service_list(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'service', 'list'])

def cmd_lshal(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'lshal'])

def cmd_netstat_nlptu(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'netstat', '-nlptu'])

def cmd_pm_dump_signatures(serial_id, package_name):
    return run_command(['adb', '-s', serial_id, 'shell', 'pm', 'dump', package_name, '|', 'grep', 'signatures:'])

def cmd_pm_dump_privileged(serial_id, package_name):
    return run_command(['adb', '-s', serial_id, 'shell', 'pm', 'dump', package_name, '|', 'grep', 'PRIVILEGED'])

def adb_devices():
    output = cmd_adb_devices().decode('ascii')
    lines = output.split('\n')
    device_serial = []
    for line in lines:
        line = line.strip()
        if '\t' in line:
            id = line.split('\t')[0]
            status = line.split('\t')[1]
            build_fingerprint = cmd_getprop_ro_build_fingerprint(id).decode('ascii').strip()
            device_serial.append({'id': id, 'status': status, 'build_fingerprint': build_fingerprint})
    return device_serial

def select_adb_devices():
    devices = adb_devices()
    i = 1
    print('Select an adb device:')
    for device in devices:
        print(str(i) + ' => ' + device['id'] + '\t' + device['status'] + '\t' + device['build_fingerprint'])
        i = i + 1
    select = int(input())
    if select > len(devices):
        print('[Error] Out of range.')
        return None
    if devices[select - 1]['status'] != 'device':
        print('[Warning] Device not avaliable, status is: ' + devices[select - 1]['status'])
    return devices[select - 1]['id']

def is_privileged(serial_id, package):
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
    is_priv = is_privileged(serial_id, package)
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

def show_progress(now, total, msg):
    if total == 0:
        return
    p = (now * 100) // total
    print('<' + str(p) + '%' + '>' + msg)


def main():
    is_info_only = False
    if len(sys.argv) == 2 and sys.argv[1] == '--info-only':
        is_info_only = True
        print('--info-only detected: do not dump apks, libraries and binaries.')
    serial_id = select_adb_devices()

    print('[Task 1] Dump Android framework & Apps')

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

    print('[Task 2] Dump SELinux policy')
    os.mkdir('selinux')
    dump_selinux_policy(serial_id)

    print('[Task 3] Run service list cmd')
    service_list_file = open('service_list.txt', 'wb')
    service_list_file.write(cmd_service_list(serial_id))
    service_list_file.close()

    print('[Task 4] Run lshal cmd')
    lshal_file = open('lshal.txt', 'wb')
    lshal_file.write(cmd_lshal(serial_id))
    lshal_file.close()

    print('[Task 5] Run netstat -nlptu cmd')
    netstat_file = open('netstat.txt', 'wb')
    netstat_file.write(cmd_netstat_nlptu(serial_id))
    netstat_file.close()

    if not is_info_only:
        print('[Task 6] Dump libraries')
        os.mkdir('system_libs')
        dump_system_lib(serial_id)
        os.mkdir('vendor_libs')
        dump_vendor_lib(serial_id)

        print('[Task 7] Dump binaries')
        os.mkdir('system_binaries')
        dump_system_bin(serial_id)
        os.mkdir('vendor_binaries')
        dump_vendor_bin(serial_id)


main()