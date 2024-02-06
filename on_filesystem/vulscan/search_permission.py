import os
import sys
import subprocess
import json
import tempfile
from xml.dom import minidom

def run_command(cmds, cwd='.'):
    return subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd).communicate()[0]

def parse_android_manifest(apk_file, output_file):
    return run_command(['androguard', 'axml', '-o', output_file, apk_file])

def get_android_name(element):
    return element.getAttribute('android:name')

def get_android_protection_level(element):
    return element.getAttribute('android:protectionLevel')

def get_package_name(manifest):
    return manifest.getAttribute('package')

def get_application(manifest):
    applications = manifest.getElementsByTagName('application')
    if len(applications) > 0:
        return applications[0]
    else:
        return None

def get_defined_permissions(manifest):
    permissions = manifest.getElementsByTagName('permission')
    permissions_name_level = []
    for permission in permissions:
        name = get_android_name(permission)
        protection_level = get_android_protection_level(permission)
        permissions_name_level.append({'name': name, 'protectionLevel': protection_level})
    return permissions_name_level

def is_permission_privileged(defined_permission):
    return not ('normal' in defined_permission['protectionLevel'] or 'dangerous' in defined_permission['protectionLevel'])

def get_uses_permissions(manifest):
    uses_permissions = manifest.getElementsByTagName('uses-permission')
    uses_permissions_name = []
    for uses_permission in uses_permissions:
        name = get_android_name(uses_permission)
        uses_permissions_name.append(name)
    return uses_permissions_name
        
def get_activities(application):
    return application.getElementsByTagName('activity')

def get_services(application):
    return application.getElementsByTagName('service')

def get_content_providers(application):
    return application.getElementsByTagName('provider')

def get_broadcast_receivers(application):
    return application.getElementsByTagName('receiver')

def get_component_intent_filters(component):
    return component.getElementsByTagName('intent-filter')

def is_component_exported(component):
    exported = component.getAttribute('android:exported')
    if exported == 'true':
        return True
    elif exported =='false':
        return False
    else:
        return len(get_component_intent_filters(component)) != 0

def get_componment_permission(componment):
    return componment.getAttribute('android:permission')

def get_provider_read_permission(provider):
    return provider.getAttribute('android:readPermission')

def get_provider_write_permission(provider):
    return provider.getAttribute('android:writePermission')

def collect_permission_info(xml_content):
    manifest_file_content = minidom.parse(xml_content)

    manifest = manifest_file_content.documentElement
    package_name = get_package_name(manifest)
    application = get_application(manifest)
    defined_permissions = get_defined_permissions(manifest)
    uses_permissions = get_uses_permissions(manifest)

    if application == None:
        print('Cannot get application tag in ' + package_name)
        return None

    activities = get_activities(application)
    services = get_services(application)
    providers = get_content_providers(application)
    receivers = get_broadcast_receivers(application)

    componments = []
    
    for activity in activities:
        if is_component_exported(activity):
            full_componment_name = package_name + '/' + get_android_name(activity)
            permission = get_componment_permission(activity)
            componments.append({
                'name': full_componment_name,
                'type': 'activity',
                'permission': permission,
            })
    
    for service in services:
        if is_component_exported(service):
            full_componment_name = package_name + '/' + get_android_name(service)
            permission = get_componment_permission(service)
            componments.append({
                'name': full_componment_name,
                'type': 'service',
                'permission': permission,
            })
    
    for provider in providers:
        if is_component_exported(provider):
            full_componment_name = package_name + '/' + get_android_name(provider)
            permission = get_componment_permission(provider)
            read_permission = get_provider_read_permission(provider)
            write_permission = get_provider_write_permission(provider)
            componments.append({
                'name': full_componment_name,
                'type': 'provider',
                'permission': permission,
                'readPermission': read_permission,
                'writePermission': write_permission
            })
    
    for receiver in receivers:
        if is_component_exported(receiver):
            full_componment_name = package_name + '/' + get_android_name(receiver)
            permission = get_componment_permission(receiver)
            componments.append({
                'name': full_componment_name,
                'type': 'receiver',
                'permission': permission,
            })
    result = {
        "componments": componments,
        "defined_permissions": defined_permissions,
        "uses_permissions": uses_permissions
    }
    return result

def search_componment_permission_issues(componments, defined_permissions):
    undef_pem_comps = {
        'activity': [],
        'service': [],
        'provider': [],
        'receiver': []
    }
    no_pem_comps = {
        'activity': [],
        'service': [],
        'provider': [],
        'receiver': []
    }
    for componment in componments:
        no_priv_permission = {
            'writePermission': True,
            'readPermission': True,
            'permission': True
        }
        not_defined = {
            'writePermission': True,
            'readPermission': True,
            'permission': True
        }
        if componment['type'] == 'Provider':
            provider_pem_key_words = ['writePermission', 'readPermission', 'permission']
            for pem_key_word in provider_pem_key_words:
                if pem_key_word in componment and componment[pem_key_word] != '':
                    for defined_permission in defined_permissions:
                        if defined_permission['name'] == componment[pem_key_word]:
                            not_defined[pem_key_word] = False
                            if is_permission_privileged(defined_permission):
                                no_priv_permission[pem_key_word] = False
                            break
                    if not_defined[pem_key_word]:
                        undef_pem_comps[componment['type']].append({
                            'name': componment['name'],
                            pem_key_word: componment[pem_key_word]
                        })
                        continue
                if no_priv_permission[pem_key_word] and pem_key_word != 'permission':
                    no_pem_comps[componment['type']].append({
                        'name': componment['name'],
                        pem_key_word: componment[pem_key_word]
                    })
        else:
            if 'permission' in componment and componment['permission'] != '':
                for defined_permission in defined_permissions:
                    if defined_permission['name'] == componment['permission']:
                        not_defined['permission'] = False
                        if is_permission_privileged(defined_permission):
                            no_priv_permission['permission'] = False
                        break
                if not_defined['permission']:
                    undef_pem_comps[componment['type']].append({
                        'name': componment['name'],
                        'permission': componment['permission']
                    })
                    continue
            if no_priv_permission['permission']:
                no_pem_comps[componment['type']].append({
                    'name': componment['name'],
                    'permission': componment['permission']
                })
    for comp_type in undef_pem_comps.keys():
         with open('undef_pem_issues_' + comp_type + '.json', 'w') as f:
            f.write(json.dumps(undef_pem_comps[comp_type]))
    
    for comp_type in no_pem_comps.keys():
         with open('no_pem_issues_' + comp_type + '.json', 'w') as f:
            f.write(json.dumps(no_pem_comps[comp_type]))

def process_apk(apk_file):
    print('Start analysis apk file: '+apk_file)
    _, output_file = tempfile.mkstemp()
    parse_android_manifest(apk_file, output_file)
    return collect_permission_info(output_file)

def scan_dir(packages_dir):
    componments = []
    defined_permissions = []
    uses_permissions = []

    for package in os.listdir(packages_dir):
        if 'auto_generated_rro_product' in package:
            print('Skip auto_generated_rro_product: ' + package)
            continue
        package_dir = packages_dir + os.sep + package
        if os.path.isdir(package_dir):
            for file in os.listdir(package_dir):
                if 'auto_generated_rro_product' in file:
                    print('Skip auto_generated_rro_product apk: ' + file)
                    continue
                if 'auto_generated_rro_product' in file:
                    print('Skip auto_generated_rro_product apk: ' + file)
                    continue
                if file.endswith('.apk'):
                    apk_file = package_dir + os.sep + file
                    if os.path.isfile(apk_file):
                        tmp_result = process_apk(apk_file)
                        if tmp_result == None:
                            continue
                        componments.extend(tmp_result['componments'])
                        defined_permissions.extend(tmp_result['defined_permissions'])
                        
        elif package.endswith('.apk'):
            apk_file = package_dir
            if os.path.isfile(apk_file):
                tmp_result = process_apk(apk_file)
                if tmp_result == None:
                    continue
                componments.extend(tmp_result['componments'])
                defined_permissions.extend(tmp_result['defined_permissions'])
    print('Start analysis undefined componment permissions...')
    search_componment_permission_issues(componments, defined_permissions)
    print('Finish!')
if len(sys.argv) != 2:
    print('search_permission.py: Missing parameters, usage: python search_permission.py dir')
    sys.exit(1)
scan_dir(sys.argv[1])
