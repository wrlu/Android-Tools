import os
import subprocess

def run_command(cmds, cwd='.'):
    return subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd).communicate()[0]

def adb_devices():
    output = run_command(['adb', 'devices']).decode('ascii')
    lines = output.split('\n')
    device_serial = []
    for line in lines:
        line = line.strip()
        if '\t' in line:
            id = line.split('\t')[0]
            status = line.split('\t')[1]
            device_serial.append({'id': id, 'status': status})
    return device_serial

def select_adb_devices():
    devices = adb_devices()
    i = 1
    print('Select an adb device:')
    for device in devices:
        print(str(i) + ' => ' + device['id'] + '\t' + device['status'])
        i = i + 1
    select = int(input())
    if select > len(devices):
        print('[Error] Out of range.')
        return None
    if devices[select - 1]['status'] != 'device':
        print('[Warning] Device not avaliable, status is: ' + devices[select - 1]['status'])
    return devices[select - 1]['id']

def get_build_fingerprint(serial_id):
    output = run_command(['adb', '-s', serial_id, 'shell', 'getprop', 'ro.build.fingerprint']).decode('ascii')
    print(output)

def service_list(serial_id):
    output = run_command(['adb', '-s', serial_id, 'shell', 'service', 'list']).decode('ascii')
    lines = output.split('\n')
    packages = []
    for line in lines:
        line = line.strip()
        if '=' in line:
            path = line[:line.rindex('=')]
            package_name = line[line.rindex('=') + 1:]
            packages.append({'package': package_name, 'path': path})
    return packages

def netstat_nlptu(serial_id):
    run_command(['adb', '-s', serial_id, 'root'])

def pm_list_packages(serial_id):
    output = run_command(['adb', '-s', serial_id, 'shell', 'pm', 'list', 'packages', '-f']).decode('ascii')
    lines = output.split('\n')
    packages = []
    for line in lines:
        line = line.strip().strip('package:')
        if '=' in line:
            path = line[:line.rindex('=')]
            package_name = line[line.rindex('=') + 1:]
            packages.append({'package': package_name, 'path': path})
    return packages

def dump_apk_folder(serial_id, package):
    run_command(['adb', '-s', serial_id, 'pull', package['path'][:package['path'].rindex('/')], package['package']], cwd='packages')

def dump_system_lib(serial_id):
    run_command(['adb', '-s', serial_id, 'pull', '/system/lib64/'], cwd='libs')
    run_command(['adb', '-s', serial_id, 'pull', '/system/lib/'], cwd='libs')

def dump_system_bin(serial_id):
    run_command(['adb', '-s', serial_id, 'pull', '/system/bin/'], cwd='binaries')

def dump_selinux_policy(serial_id):
    run_command(['adb', '-s', serial_id, 'pull', '/sys/fs/selinux/policy'], cwd='selinux')



serial_id = select_adb_devices()
print('[0/4] Get build fingerprint')
get_build_fingerprint(serial_id)

print('[1/4] Dump Android framework & Apps')
packages = pm_list_packages(serial_id)
os.mkdir('packages')
package_index_file = open('packages/package_index.csv', 'w')
for package in packages:
    package_index_file.write(package['package']+','+package['path']+'\n')
    dump_apk_folder(serial_id, package)
    package_index_file.flush()
package_index_file.close()

print('[2/4] Dump libs')
os.mkdir('libs')
dump_system_lib(serial_id)

print('[3/4] Dump binaries')
os.mkdir('binaries')
dump_system_bin(serial_id)

print('[4/4] Dump SELinux policy')
os.mkdir('selinux')
dump_selinux_policy(serial_id)