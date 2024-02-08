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

def get_protected_broadcast(manifest):
    protected_broadcasts = manifest.getElementsByTagName('protected-broadcast')
    protected_broadcast_name = []
    for protected_broadcast in protected_broadcasts:
        name = get_android_name(protected_broadcast)
        protected_broadcast_name.append(name)
    return protected_broadcast_name
        
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

def get_intent_filter_actions(intent_filter):
    return intent_filter.getElementsByTagName('action')

def get_all_action_names(component):
    intent_filters = get_component_intent_filters(component)
    action_names = []
    for intent_filter in intent_filters:
        actions = get_intent_filter_actions(intent_filter)
        for action in actions:
            action_names.append(get_android_name(action))
    return action_names

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
    protected_broadcasts = get_protected_broadcast(manifest)

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
            action_names = get_all_action_names(receiver)
            componments.append({
                'name': full_componment_name,
                'type': 'receiver',
                'actions': action_names,
                'permission': permission,
            })
    result = {
        'componments': componments,
        'defined_permissions': defined_permissions,
        'uses_permissions': uses_permissions,
        'protected_broadcasts': protected_broadcasts
    }
    return result

def search_componment_permission_issues(base_data):
    undef_pem_comps = {
        'activity': [],
        'service': [],
        'provider': [],
        'receiver': []
    }
    unpriv_pem_comps = {
        'activity': [],
        'service': [],
        'provider': [],
        'receiver': []
    }
    for componment in base_data['componments']:
        unprivileged = {
            'writePermission': True,
            'readPermission': True,
            'permission': True
        }
        undefined = {
            'writePermission': True,
            'readPermission': True,
            'permission': True
        }
        if componment['type'] == 'provider':
            provider_pem_key_words = ['writePermission', 'readPermission', 'permission']
            for pem_key_word in provider_pem_key_words:
                if pem_key_word in componment and componment[pem_key_word] != '':
                    for defined_permission in base_data['defined_permissions']:
                        if defined_permission['name'] == componment[pem_key_word]:
                            undefined[pem_key_word] = False
                            if is_permission_privileged(defined_permission):
                                unprivileged[pem_key_word] = False
                            break
                else:
                    unprivileged[pem_key_word] = True
                    undefined[pem_key_word] = False
            # readPermission or writePermission undefined, and permission unprivileged or undefined.
            # the undefined readPermission/writePermission is vulnerable.
            if (unprivileged['permission'] or undefined['permission']) and (undefined['writePermission'] or undefined['readPermission']):
                undef_pem_comps[componment['type']].append({
                    'name': componment['name'],
                    'writePermission': componment['writePermission'],
                    'readPermission': componment['readPermission'],
                    'permission': componment['permission'],
                })
            # permission undefined, and readPermission or writePermission unprivileged.
            # the undefined permission is vulnerable.
            elif undefined['permission'] and (unprivileged['readPermission'] or unprivileged['writePermission']):
                undef_pem_comps[componment['type']].append({
                    'name': componment['name'],
                    'writePermission': componment['writePermission'],
                    'readPermission': componment['readPermission'],
                    'permission': componment['permission'],
                })
            # permission unprivileged, and readPermission or writePermission unprivileged.
            # the unprivileged permission is vulnerable.
            elif unprivileged['permission'] and (unprivileged['writePermission'] or unprivileged['readPermission']):
                unpriv_pem_comps[componment['type']].append({
                    'name': componment['name'],
                    'writePermission': componment['writePermission'],
                    'readPermission': componment['readPermission'],
                    'permission': componment['permission'],
                })
        else:
            if 'permission' in componment and componment['permission'] != '':
                for defined_permission in base_data['defined_permissions']:
                    if defined_permission['name'] == componment['permission']:
                        undefined['permission'] = False
                        if is_permission_privileged(defined_permission):
                            unprivileged['permission'] = False
                        break
            else:
                unprivileged['permission'] = True
                undefined['permission'] = False
            if componment['type'] == 'receiver':
                has_unprotected_action = False
                for action in componment['actions']:
                    if action not in base_data['protected_broadcasts']:
                        has_unprotected_action = True
                        break
                if has_unprotected_action == False:
                    continue

            if undefined['permission']:
                undef_pem_comps[componment['type']].append({
                    'name': componment['name'],
                    'permission': componment['permission']
                })
            elif unprivileged['permission']:
                unpriv_pem_comps[componment['type']].append({
                    'name': componment['name'],
                    'permission': componment['permission']
                })
    for comp_type in undef_pem_comps.keys():
         with open('undef_pem_issues_' + comp_type + '.json', 'w') as f:
            f.write(json.dumps(undef_pem_comps[comp_type]))
    
    for comp_type in unpriv_pem_comps.keys():
         with open('unpriv_pem_issues_' + comp_type + '.json', 'w') as f:
            f.write(json.dumps(unpriv_pem_comps[comp_type]))

def process_apk(apk_file):
    print('Start analysis apk file: '+apk_file)
    _, output_file = tempfile.mkstemp()
    parse_android_manifest(apk_file, output_file)
    return collect_permission_info(output_file)

def scan_dir(packages_dir):
    base_data = {
        'componments': [],
        'defined_permissions': [],
        'uses_permissions': [],
        'protected_broadcasts': []
    }

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
                        base_data['componments'].extend(tmp_result['componments'])
                        base_data['defined_permissions'].extend(tmp_result['defined_permissions'])
                        base_data['uses_permissions'].extend(tmp_result['uses_permissions'])
                        base_data['protected_broadcasts'].extend(tmp_result['protected_broadcasts'])
                        
        elif package.endswith('.apk'):
            apk_file = package_dir
            if os.path.isfile(apk_file):
                tmp_result = process_apk(apk_file)
                if tmp_result == None:
                    continue
                base_data['componments'].extend(tmp_result['componments'])
                base_data['defined_permissions'].extend(tmp_result['defined_permissions'])
                base_data['uses_permissions'].extend(tmp_result['uses_permissions'])
                base_data['protected_broadcasts'].extend(tmp_result['protected_broadcasts'])
    print('Start analysis undefined componment permissions...')
    search_componment_permission_issues(base_data)
    print('Finish!')
if len(sys.argv) != 2:
    print('search_permission.py: Missing parameters, usage: python search_permission.py dir')
    sys.exit(1)
scan_dir(sys.argv[1])
