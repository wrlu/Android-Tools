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

# https://developer.android.com/reference/android/R.attr#protectionLevel
def is_permission_privileged(defined_permission):
    if defined_permission['protectionLevel'] == '':
        return False
    protectionLevelInt = int(defined_permission['protectionLevel'], base=16)
    # Only care with base permission types here, ignore the additional flags.
    # signature
    if protectionLevelInt & 0x2 == 0x2:
        return True
    # signatureOrSystem
    # if protectionLevelInt & 0x3 == 0x3:
    #     return True
    # internal
    if protectionLevelInt & 0x4 == 0x4:
        return True
    # system
    if protectionLevelInt & 0x10 == 0x10:
        return True
    # dangerous
    # if protectionLevelInt & 0x1 == 0x1:
    #     return False
    return False

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

def get_component_permission(component):
    return component.getAttribute('android:permission')

def get_provider_read_permission(provider):
    return provider.getAttribute('android:readPermission')

def get_provider_write_permission(provider):
    return provider.getAttribute('android:writePermission')

def get_provider_path(provider):
    return provider.getAttribute('android:path')

def get_provider_path_prefix(provider):
    return provider.getAttribute('android:pathPrefix')

def get_provider_path_pattern(provider):
    return provider.getAttribute('android:pathPattern')

def get_provider_path_permission(provider):
    return provider.getElementsByTagName('path-permission')

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

    components = []
    
    for activity in activities:
        name = get_android_name(activity)
        if name == '':
            continue
        if is_component_exported(activity):
            full_component_name = package_name + '/' + name
            permission = get_component_permission(activity)
            components.append({
                'name': full_component_name,
                'type': 'activity',
                'permission': permission,
            })
    
    for service in services:
        name = get_android_name(service)
        if name == '':
            continue
        if is_component_exported(service):
            
            full_component_name = package_name + '/' + name
            permission = get_component_permission(service)
            components.append({
                'name': full_component_name,
                'type': 'service',
                'permission': permission,
            })
    
    for provider in providers:
        name = get_android_name(provider)
        if name == '':
            continue
        if is_component_exported(provider):
            full_component_name = package_name + '/' + name
            permission = get_component_permission(provider)
            read_permission = get_provider_read_permission(provider)
            write_permission = get_provider_write_permission(provider)
            path_permission = []
            for path_permission_element in get_provider_path_permission(provider):
                path = get_provider_path(path_permission_element)
                pathPrefix = get_provider_path_prefix(path_permission_element)
                pathPattern = get_provider_path_pattern(path_permission_element)
                path_permission_def = get_component_permission(path_permission_element)
                path_readPermission = get_provider_read_permission(path_permission_element)
                path_writePermission = get_provider_write_permission(path_permission_element)

                per_path_permission = {}
                if path != None and path != '':
                    per_path_permission['path'] = path
                if pathPrefix != None and pathPrefix != '':
                    per_path_permission['pathPrefix'] = pathPrefix
                if pathPattern != None and pathPattern != '':
                    per_path_permission['pathPattern'] = pathPattern
                if path_permission_def != None and path_permission_def != '':
                    per_path_permission['permission'] = path_permission_def
                if path_readPermission != None and path_readPermission != '':
                    per_path_permission['readPermission'] = path_readPermission
                if path_writePermission != None and path_writePermission != '':
                    per_path_permission['writePermission'] = path_writePermission
                
                path_permission.append(per_path_permission)
                
            components.append({
                'name': full_component_name,
                'type': 'provider',
                'permission': permission,
                'readPermission': read_permission,
                'writePermission': write_permission,
                'path_permission': path_permission
            })
    
    for receiver in receivers:
        name = get_android_name(receiver)
        if name == '':
            continue
        if is_component_exported(receiver):
            full_component_name = package_name + '/' + name
            permission = get_component_permission(receiver)
            action_names = get_all_action_names(receiver)
            components.append({
                'name': full_component_name,
                'type': 'receiver',
                'actions': action_names,
                'permission': permission,
            })
    result = {
        'components': components,
        'defined_permissions': defined_permissions,
        'uses_permissions': uses_permissions,
        'protected_broadcasts': protected_broadcasts
    }
    return package_name, result

def search_component_permission_issues(base_data):
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
    base_data_merge = {
        'components': [],
        'defined_permissions': [],
        'uses_permissions': [],
        'protected_broadcasts': []
    }
    for per_apk_data in base_data:
        base_data_merge['components'].extend(per_apk_data['components'])
        base_data_merge['defined_permissions'].extend(per_apk_data['defined_permissions'])
        base_data_merge['uses_permissions'].extend(per_apk_data['uses_permissions'])
        base_data_merge['protected_broadcasts'].extend(per_apk_data['protected_broadcasts'])
    
    for component in base_data_merge['components']:
        status = {
            'permission': 'blank',
            'readPermission': 'blank',
            'writePermission': 'blank',
        }

        # Provider has readPermission and writePermission, will use special check logic.
        if component['type'] == 'provider':
            provider_pem_key_words = ['writePermission', 'readPermission', 'permission']
            for pem_key_word in provider_pem_key_words:
                if pem_key_word in component and component[pem_key_word] != '':
                    status[pem_key_word] = 'undefined'
                    for defined_permission in base_data_merge['defined_permissions']:
                        if defined_permission['name'] == component[pem_key_word]:
                            if is_permission_privileged(defined_permission):
                                status[pem_key_word] = 'privileged'
                            else:
                                status[pem_key_word] = 'unprivileged'
                            break
                # If permission/readPermission/writePermission keep blank mean unprivileged.
                else:
                    status[pem_key_word] = 'unprivileged'
            
            if status['permission'] == 'unprivileged':
                if status['writePermission'] == 'undefined' or status['readPermission'] == 'undefined':
                    undef_pem_comps[component['type']].append({
                        'name': component['name'],
                        'writePermission': component['writePermission'],
                        'readPermission': component['readPermission'],
                        'permission': component['permission'],
                        'path_permission': component['path_permission']
                    })
                    continue
                if status['writePermission'] == 'unprivileged' or status['readPermission'] == 'unprivileged':
                    unpriv_pem_comps[component['type']].append({
                        'name': component['name'],
                        'writePermission': component['writePermission'],
                        'readPermission': component['readPermission'],
                        'permission': component['permission'],
                        'path_permission': component['path_permission']
                    })
                    continue
            elif status['permission'] == 'undefined':
                if status['writePermission'] == 'unprivileged' or status['readPermission'] == 'unprivileged':
                    undef_pem_comps[component['type']].append({
                        'name': component['name'],
                        'writePermission': component['writePermission'],
                        'readPermission': component['readPermission'],
                        'permission': component['permission'],
                        'path_permission': component['path_permission']
                    })
                    continue
                if status['writePermission'] == 'undefined' or status['readPermission'] == 'undefined':
                    undef_pem_comps[component['type']].append({
                        'name': component['name'],
                        'writePermission': component['writePermission'],
                        'readPermission': component['readPermission'],
                        'permission': component['permission'],
                        'path_permission': component['path_permission']
                    })
                    continue
            
            # Check path permission
            for per_path_permission in component['path_permission']:
                found = False
                for key in per_path_permission.keys():
                    if (key == 'permission' or key == 'readPermission' or key == 'writePermission') and per_path_permission[key] != '':
                        defined = False
                        privileged = False
                        for defined_permission in base_data_merge['defined_permissions']:
                            if defined_permission['name'] == per_path_permission[key]:
                                defined = True
                                if not is_permission_privileged(defined_permission):
                                    unpriv_pem_comps[component['type']].append({
                                        'name': component['name'],
                                        'writePermission': component['writePermission'],
                                        'readPermission': component['readPermission'],
                                        'permission': component['permission'],
                                        'path_permission': component['path_permission']
                                    })
                                    privileged = False
                                else:
                                    privileged = True
                                break
                        if not defined:
                            undef_pem_comps[component['type']].append({
                                'name': component['name'],
                                'writePermission': component['writePermission'],
                                'readPermission': component['readPermission'],
                                'permission': component['permission'],
                                'path_permission': component['path_permission']
                            })
                        if not defined or not privileged:
                            found = True
                            break
                if found:
                    break

        # Other components only have permission, use normal logic.
        else:
            if 'permission' in component and component['permission'] != '':
                status['permission'] = 'undefined'
                for defined_permission in base_data_merge['defined_permissions']:
                    if defined_permission['name'] == component['permission']:
                        if is_permission_privileged(defined_permission):
                            status['permission'] = 'privileged'
                        else:
                            status['permission'] = 'unprivileged'
            else:
                status['permission'] = 'unprivileged'
            
            # Exported receiver should have an intent filter with unprotected action if is vulnerable. 
            if component['type'] == 'receiver':
                has_unprotected_action = False
                for action in component['actions']:
                    if action not in base_data_merge['protected_broadcasts']:
                        has_unprotected_action = True
                        break
                if has_unprotected_action == False:
                    continue

            if status['permission'] == 'undefined':
                undef_pem_comps[component['type']].append({
                    'name': component['name'],
                    'permission': component['permission']
                })
            elif status['permission'] == 'unprivileged':
                unpriv_pem_comps[component['type']].append({
                    'name': component['name'],
                    'permission': component['permission']
                })
    final_result = {}
    final_result['undefined_permissions'] = undef_pem_comps
    final_result['unprivileged_permissions'] = unpriv_pem_comps
    return final_result

def process_apk(apk_file):
    print('Start analysis apk file: '+apk_file)
    _, output_file = tempfile.mkstemp()
    parse_android_manifest(apk_file, output_file)
    return collect_permission_info(output_file)

def scan_dir(packages_dir):
    base_data = []

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
                        package_name, tmp_result = process_apk(apk_file)
                        if tmp_result == None:
                            continue
                        base_data.append({
                            'package': package_name,
                            'filename': apk_file,
                            'components': tmp_result['components'],
                            'defined_permissions': tmp_result['defined_permissions'],
                            'uses_permissions': tmp_result['uses_permissions'],
                            'protected_broadcasts': tmp_result['protected_broadcasts'],
                        })
                        
        elif package.endswith('.apk'):
            apk_file = package_dir
            if os.path.isfile(apk_file):
                package_name, tmp_result = process_apk(apk_file)
                if tmp_result == None:
                    continue
                base_data.append({
                    'package': package_name,
                    'filename': apk_file,
                    'components': tmp_result['components'],
                    'defined_permissions': tmp_result['defined_permissions'],
                    'uses_permissions': tmp_result['uses_permissions'],
                    'protected_broadcasts': tmp_result['protected_broadcasts'],
                })
    return base_data

def main():
    if len(sys.argv) != 2:
        print('search_permission.py: Missing parameters, usage: python search_permission.py dir')
        sys.exit(1)
    
    base_data = {}
    if os.path.exists(sys.argv[1] + os.sep + 'all_comp.json'):
        with open(sys.argv[1] + os.sep + 'all_comp.json', 'r') as f:
            base_data = json.load(f)
    else:
        base_data = scan_dir(sys.argv[1] + os.sep + 'packages')
        with open(sys.argv[1] + os.sep + 'all_comp.json', 'w') as f:
            json.dump(base_data, f)
    
    print('Start analysis component permissions...')
    final_result = search_component_permission_issues(base_data)
    with open(sys.argv[1] + os.sep + 'accessible_comp.json', 'w') as f:
        json.dump(final_result, f)

    print('Finish!')
    
if __name__ == '__main__':
    main()