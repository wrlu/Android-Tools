import sys
import os
import subprocess
import platform

def run_command(cmds, cwd='.'):
    return subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd).communicate()[0]

def host_cmd_sesearch_check_service(source, target, tclass, policy):
    if platform.system() == 'Windows':
        return run_command(['wsl', '-e', 'sesearch', '-A', '-s', source, '-t', target, '-c', tclass, policy])
    else:
        return run_command(['sesearch', '-A', '-s', source, '-t', target, '-c', tclass, policy])

def untrusted_app_service_accessible_anaylsis():
    service_names = []
    with open('service_list.txt', 'r', encoding='ascii') as service_file:
        lines = service_file.readlines()
        for line in lines[1:]:
            service_name = line.strip().split('\t')[1].split(':')[0]
            service_names.append(service_name)
    service_tag_mapping = {}
    with open('selinux/selinux/plat_service_contexts', 'r', encoding='ascii') as context_file:
        lines = context_file.readlines()
        for line in lines:
            parts = line.strip().split()
            if len(parts) == 2:
                name = parts[0]
                if name in service_names:
                    tag = parts[1].split(':')[2]
                    service_tag_mapping[name] = tag
    accessible_services = []
    i = 1
    total = len(service_tag_mapping)
    for service, tag in service_tag_mapping.items():
        result = host_cmd_sesearch_check_service('untrusted_app_all', tag,'service_manager', 'selinux/policy')
        if b'allow' in result:
            show_progress(i, total, f"Allow access: {service}")
            accessible_services.append(service)
        i = i + 1
    return accessible_services

def show_progress(now, total, msg):
    if total == 0:
        return
    p = (now * 100) // total
    print('[' + str(p) + '%' + '] ' + msg)

def main(workspace):
    os.chdir(workspace)
    accessible_services = untrusted_app_service_accessible_anaylsis()
    with open('accessible_services.txt', 'w') as f:
        for service in accessible_services:
            f.write(service)
            f.write('\n')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('get_accessible_services.py: Missing parameters, usage: python get_accessible_services.py dir')
        sys.exit(1)
    main(sys.argv[1])