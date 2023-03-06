import os
import sys
import subprocess
import platform
from Crypto.PublicKey import RSA
from factordb.factordb import FactorDB

begin_cert = '-----BEGIN CERTIFICATE-----'
end_cert = '-----END CERTIFICATE-----'

def run_command(cmds, cwd='.'):
    return subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd).communicate()[0]

def apksign_verify(apk_file):
    return run_command(['apksigner.bat', 'verify', '--print-certs-pem', apk_file])

def do_verify(apk_file):
    print(apk_file)
    encoding = 'utf8'
    lfchar = '\n'
    if platform.system() == 'Windows':
        encoding = 'gbk'
        lfchar = '\r\n'
    
    verify_output_lines = apksign_verify(apk_file).decode(encoding).split(lfchar)
    is_cert_line = False
    with open('.pubkey.pem', 'w') as cert_file:
        for line in verify_output_lines:
            if line.startswith(begin_cert):
                is_cert_line = True
            if is_cert_line is True:
                cert_file.write(line)
                cert_file.write('\n')
            if line.startswith(end_cert):
                is_cert_line = False
                break
    with open('.pubkey.pem', 'rb') as key_data:
        key = RSA.importKey(key_data.read())
        print("n: " + str(key.n))
        print("e: " + str(key.e))
        f = FactorDB(key.n)
        f.connect()
        print(f.get_status())
    os.remove('.pubkey.pem')

def scan_dir(packages_dir):
    for package in os.listdir(packages_dir):
        package_dir = packages_dir + os.sep + package
        if os.path.isdir(package_dir):
            for file in os.listdir(package_dir):
                if file.endswith('.apk'):
                    apk_file = package_dir + os.sep + file
                    if os.path.isfile(apk_file):
                        try:
                            do_verify(apk_file)
                        except Exception as e:
                            print(e)
        elif package.endswith('.apk'):
            apk_file = package_dir
            if os.path.isfile(apk_file):
                try:
                    do_verify(apk_file)
                except Exception as e:
                    print(e)


if len(sys.argv) != 2:
    print('verify_apk_sign.py: Missing parameters, usage: python verify_apk_sign.py dir')
    sys.exit(1)
scan_dir(sys.argv[1])
