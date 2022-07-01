import subprocess
import sys

def run_command(cmd):
    subprocess.call(cmd, stdout=sys.stdout, stdin=sys.stdin, stderr=sys.stderr, shell=True)

def run_command(cmds, cwd='.'):
    return subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd).communicate()[0]

def cmd_adb_devices():
    return run_command(['adb', 'devices'])

def cmd_getprop_ro_build_fingerprint(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'getprop', 'ro.build.fingerprint'])


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


serial_id = select_adb_devices()
real_cmd = ''
i = 0
for arg in sys.argv:
    if i == 0:
        i = i + 1
        continue
    real_cmd = real_cmd + arg
    real_cmd = real_cmd + ' '
    i = i + 1
print('Run ' + real_cmd + ' on device ' + serial_id)
run_command('adb -s ' + serial_id + ' ' + real_cmd)
