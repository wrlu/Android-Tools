import sys
import os
import subprocess
import platform

def run_command(cmds, cwd='.'):
    result = subprocess.run(cmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd, text=True, check=False)
    return result.stdout

def host_cmd_sesearch_svcmgr_find(source, target, policy):
    if platform.system() == 'Windows':
        return run_command(['wsl', '-e', 'sesearch', '-A', '-s', source, '-t', target, '-c', 'service_manager', '-p', 'find', policy])
    else:
        return run_command(['sesearch', '-A', '-s', source, '-t', target, '-c', 'service_manager', '-p', 'find', policy])

def untrusted_app_service_accessible_anaylsis():
    service_tag_list = []
    with open('service_list.txt', 'r', encoding='ascii') as service_file:
        next(service_file)

        for service_line in service_file:
            service_name, service_aidl = service_line.strip().split('\t')[1].split(': ')
            service_aidl = service_aidl[1:-1]

            with open('selinux/selinux/plat_service_contexts', 'r', encoding='ascii') as context_file:
                for context_line in context_file:
                    name, label = context_line.strip().split()
                    if name == service_name:
                        tag = label.split(':')[2]
                        service_tag_list.append((service_name, service_aidl, tag))
                        break
    
    
    accessible_service_tag_list = []
    i = 1
    total = len(service_tag_list)
    for service_name, service_aidl, tag in service_tag_list:
        allowlist = host_cmd_sesearch_svcmgr_find('untrusted_app_all', tag, 'selinux/policy')

        if 'allow' in allowlist:
            show_progress(i, total, f"Allow access: {service_name}: [{service_aidl}]")
            accessible_service_tag_list.append(f"{service_name}: [{service_aidl}]")
        i = i + 1
    
    show_progress(i, total, "Done")
    return accessible_service_tag_list

def show_progress(now, total, msg):
    if total == 0:
        return
    p = (now * 100) // total
    print('[' + str(p) + '%' + '] ' + msg)

def main(workspace):
    os.chdir(workspace)
    accessible_services = untrusted_app_service_accessible_anaylsis()
    with open('accessible_services.txt', 'w') as f:
        f.writelines(accessible_services)
        # For unknown reason no SELinux policy shows untrusted app can access window service
        # But it is accessible in real Android device.
        f.write('window: [android.view.IWindowManager]')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('get_accessible_services.py: Missing parameters, usage: python get_accessible_services.py dir')
        sys.exit(1)
    main(sys.argv[1])