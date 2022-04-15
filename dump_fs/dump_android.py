import os
import subprocess
import re

def run_command(cmds, cwd='.'):
    return subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd).communicate()[0]

def cmd_getprop_ro_build_fingerprint(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'getprop', 'ro.build.fingerprint']).decode('ascii')

def cmd_pm_list_packages(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'pm', 'list', 'packages', '-f', '-U']).decode('ascii')

def cmd_service_list(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'service', 'list']).decode('ascii')

def cmd_lshal(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'lshal']).decode('ascii')

def cmd_netstat_nlptu(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'netstat', '-nlptu']).decode('ascii')

def cmd_pm_dump_signatures(serial_id, package_name):
    return run_command(['adb', '-s', serial_id, 'shell', 'pm', 'dump', package_name, '|', 'grep', 'signatures:']).decode('ascii')

def cmd_pm_dump_privileged(serial_id, package_name):
    return run_command(['adb', '-s', serial_id, 'shell', 'pm', 'dump', package_name, '|', 'grep', 'PRIVILEGED']).decode('ascii')

def adb_devices():
    output = run_command(['adb', 'devices']).decode('ascii')
    lines = output.split('\n')
    device_serial = []
    for line in lines:
        line = line.strip()
        if '\t' in line:
            id = line.split('\t')[0]
            status = line.split('\t')[1]
            build_fingerprint = cmd_getprop_ro_build_fingerprint(id).strip()
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

def is_privileged(serial_id, package_name):
    dump_output = cmd_pm_dump_privileged(serial_id, package_name)
    return 'PRIVILEGED' in dump_output

def get_package_signature(serial_id, package_name):
    dump_output = cmd_pm_dump_signatures(serial_id, package_name)
    pattern = r'signatures:\[([0-9a-fA-F, ]*)\]\,'
    search_result = re.search(pattern, dump_output)
    signature = search_result.group(1)
    return signature

def get_platform_signature(serial_id):
    return get_package_signature(serial_id, 'android')

def get_package_selinux_label(serial_id, package, platform_signature):
    if int(package['uid']) == 1000:
        return 'system_app'
    is_priv = is_privileged(serial_id, package['package_name'])
    is_platform = platform_signature in get_package_signature(serial_id, package['package_name'])
    if is_platform:
        return 'platform_app'
    if is_priv:
        return 'priv_app'
    return 'untrusted_app'

def get_packages(serial_id):
    platform_signature = get_platform_signature(serial_id)
    pm_list_output = cmd_pm_list_packages(serial_id)
    lines = pm_list_output.split('\n')
    packages = []
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
            print(package_name)
    return packages

def dump_apk_folder(serial_id, package):
    run_command(['adb', '-s', serial_id, 'pull', package['path'][:package['path'].rindex('/')], package['package_name']], cwd='packages')

def dump_system_lib(serial_id):
    run_command(['adb', '-s', serial_id, 'pull', '/system/lib64/'], cwd='libs')
    run_command(['adb', '-s', serial_id, 'pull', '/system/lib/'], cwd='libs')

def dump_system_bin(serial_id):
    run_command(['adb', '-s', serial_id, 'pull', '/system/bin/'], cwd='binaries')

def dump_selinux_policy(serial_id):
    run_command(['adb', '-s', serial_id, 'pull', '/sys/fs/selinux/policy'], cwd='selinux')


serial_id = select_adb_devices()

print('[Task 1/7] Dump Android framework & Apps')
packages = get_packages(serial_id)
os.mkdir('packages')
package_index_file = open('package_index.csv', 'w')
package_index_file.write('package_name,path,uid,label\n')
for package in packages:
    package_index_file.write(package['package_name']+','+package['path']+','+package['uid']+','+package['label']+'\n')
    package_index_file.flush()
    dump_apk_folder(serial_id, package)
    
package_index_file.close()

print('[Task 2/7] Dump libraries')
os.mkdir('libs')
dump_system_lib(serial_id)

print('[Task 3/7] Dump binaries')
os.mkdir('binaries')
dump_system_bin(serial_id)

print('[Task 4/7] Dump SELinux policy')
os.mkdir('selinux')
dump_selinux_policy(serial_id)

print('[Task 5/6] Run service list cmd')
service_list_file = open('service_list.txt', 'w')
service_list_file.write(cmd_service_list(serial_id))
service_list_file.close()

print('[Task 6/7] Run lshal cmd')
lshal_file = open('lshal.txt', 'w')
lshal_file.write(cmd_lshal(serial_id))
lshal_file.close()

print('[Task 7/7] Run netstat -nlptu cmd')
netstat_file = open('netstat.txt', 'w')
netstat_file.write(cmd_netstat_nlptu(serial_id))
netstat_file.close()