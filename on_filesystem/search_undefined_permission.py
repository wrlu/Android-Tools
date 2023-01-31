import os
import sys
import subprocess
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
    return manifest.getElementsByTagName('application')[0]

def get_defined_permissions(manifest):
    permissions = manifest.getElementsByTagName('permission')
    permissions_name_level = []
    for permission in permissions:
        name = get_android_name(permission)
        protection_level = get_android_protection_level(permission)
        permissions_name_level.append({'name': name, 'protectionLevel': protection_level})
    return permissions_name_level

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
    

    activities = get_activities(application)
    services = get_services(application)
    content_providers = get_content_providers(application)
    broadcast_receivers = get_broadcast_receivers(application)

    componment_permissions = []
    
    for activity in activities:
        if is_component_exported(activity):
            full_componment_name = package_name + '/' + get_android_name(activity)
            permission = get_componment_permission(activity)
            componment_permissions.append({'comp': full_componment_name, 'permission': permission})
    
    for service in services:
        if is_component_exported(service):
            full_componment_name = package_name + '/' + get_android_name(service)
            permission = get_componment_permission(service)
            componment_permissions.append({'comp': full_componment_name, 'permission': permission})
    
    for content_provider in content_providers:
        if is_component_exported(content_provider):
            full_componment_name = package_name + '/' + get_android_name(content_provider)
            permission = get_componment_permission(content_provider)
            read_permission = get_provider_read_permission(content_provider)
            write_permission = get_provider_write_permission(content_provider)
            componment_permissions.append({
                'comp': full_componment_name,
                'permission': permission,
                'readPermission': read_permission,
                'writePermission': write_permission
            })
    
    for broadcast_receiver in broadcast_receivers:
        if is_component_exported(broadcast_receiver):
            full_componment_name = package_name + '/' + get_android_name(broadcast_receiver)
            permission = get_componment_permission(broadcast_receiver)
            componment_permissions.append({'comp': full_componment_name, 'permission': permission})

    return componment_permissions, defined_permissions, uses_permissions

def search_undefined_componment_permissions(componment_permissions, defined_permissions):
    undefined_componment_permissions = []
    for componment_permission in componment_permissions:
        if 'permission' in componment_permission and componment_permission['permission'] != '':
            is_defined = False
            for defined_permission in defined_permissions:
                if defined_permission['name'] == componment_permission['permission']:
                    is_defined = True
                    break
            if not is_defined:
                undefined_componment_permissions.append({'comp': componment_permission['comp'], 'permission': componment_permission['permission']})
        if 'readPermission' in componment_permission and componment_permission['readPermission'] != '':
            is_defined = False
            for defined_permission in defined_permissions:
                if defined_permission['name'] == componment_permission['readPermission']:
                    is_defined = True
                    break
            if not is_defined:
                undefined_componment_permissions.append({'comp': componment_permission['comp'], 'readPermission': componment_permission['readPermission']})
        if 'writePermission' in componment_permission and componment_permission['writePermission'] != '':
            is_defined = False
            for defined_permission in defined_permissions:
                if defined_permission['name'] == componment_permission['writePermission']:
                    is_defined = True
                    break
            if not is_defined:
                undefined_componment_permissions.append({'comp': componment_permission['comp'], 'writePermission': componment_permission['writePermission']})
    return undefined_componment_permissions

def scan_dir(packages_dir):
    componment_permissions = []
    defined_permissions = []
    uses_permissions = []

    for package in os.listdir(packages_dir):
        if 'auto_generated_rro_product' in package:
            print('Skip auto_generated_rro_product folder: ' + package)
            continue
        package_dir = packages_dir + os.sep + package
        if os.path.isdir(package_dir):
            for file in os.listdir(package_dir):
                if 'auto_generated_rro_product' in file:
                    print('Skip auto_generated_rro_product apk: ' + file)
                    continue
                if file.endswith('.apk'):
                    apk_file = package_dir + os.sep + file
                    if os.path.isfile(apk_file):
                        print('Start analysis apk file: '+apk_file)
                        output_file = '/tmp/tmp_AndroidManifest.xml'
                        parse_android_manifest(apk_file, output_file)
                        try:
                            componment_permission, defined_permission, uses_permission = collect_permission_info(output_file)
                            componment_permissions.extend(componment_permission)
                            defined_permissions.extend(defined_permission)
                        except Exception as e:
                            print('Scan file '+ file + ' error, ' + str(e))
                            continue
    print('Start analysis undefined componment permissions...')
    undefined_componment_permissions = search_undefined_componment_permissions(componment_permissions, defined_permissions)
    for undefined_componment_permission in undefined_componment_permissions:
        print(undefined_componment_permission)
    print('Finish!')
if len(sys.argv) != 2:
    print('search_undefined_permission.py: Missing parameters, usage: python search_undefined_permission.py dir')
    sys.exit(1)
scan_dir(sys.argv[1])
