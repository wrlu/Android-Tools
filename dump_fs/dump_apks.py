import sys
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

def get_prop_build_fingerprint(serial_id):
    output = run_command(['adb', '-s', serial_id, 'shell', 'getprop', 'ro.build.fingerprint']).decode('ascii')
    print(output)

def pm_list_packages(serial_id):
    output = run_command(['adb', '-s', serial_id, 'shell', 'pm', 'list', 'packages', '-f']).decode('ascii')
    lines = output.split('\n')
    packages = []
    for line in lines:
        line = line.strip().strip('package:')
        if '=' in line:
            path = line.split('=')[0]
            package_name = line.split('=')[1]
            packages.append({'package': package_name, 'path': path})
    return packages

def dump_apk_folder(serial_id, package):
    run_command(['adb', '-s', serial_id, 'pull', package['path'][:package['path'].rindex('/')], package['package']], cwd='packages')

def select_adb_devices():
    devices = adb_devices()
    i = 1
    print('Select an adb device:')
    for device in devices:
        print(str(i) + ' => ' + device['id'] + '\t' + device['status'])
    select = int(input())
    if select > len(devices):
        print('[Error] Out of range.')
        return None
    if devices[select - 1]['status'] != 'device':
        print('[Warning] Device not avaliable, status is: ' + devices[select - 1]['status'])
    return devices[select - 1]['id']

serial_id = select_adb_devices()
get_prop_build_fingerprint(serial_id)
packages = pm_list_packages(serial_id)
os.mkdir('packages')
index_file = open('packages/package_index.csv', 'w')
for package in packages:
    index_file.write(package['package']+','+package['path'])
    dump_apk_folder(serial_id, package)
