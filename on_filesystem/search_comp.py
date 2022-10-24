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
    elif exported == 'false':
        return False
    else:
        return len(get_component_intent_filters(component)) != 0

def count_comp(xml_content):
    manifest_file_content = minidom.parse(xml_content)

    manifest = manifest_file_content.documentElement
    package_name = get_package_name(manifest)
    application = get_application(manifest)
    
    activities = get_activities(application)
    services = get_services(application)
    content_providers = get_content_providers(application)
    broadcast_receivers = get_broadcast_receivers(application)

    exported_activities = []
    exported_services = []
    exported_content_providers = []
    exported_broadcast_receivers = []

    for activity in activities:
        if is_component_exported(activity):
            exported_activities.append(activity)
    
    for service in services:
        if is_component_exported(service):
            exported_services.append(service)
    
    for content_provider in content_providers:
        if is_component_exported(content_provider):
            exported_content_providers.append(content_provider)
    
    for broadcast_receiver in broadcast_receivers:
        if is_component_exported(broadcast_receiver):
            exported_broadcast_receivers.append(broadcast_receiver)

    print('['+ package_name + '] ' + 'Activity = ' + str(len(exported_activities)) + ', Service = ' + str(len(exported_services)) + ', ContentProvider = ' + str(len(exported_content_providers)) + ', BroadcastReceiver = ' + str(len(exported_broadcast_receivers)))

def scan_dir(packages_dir):
    for package in os.listdir(packages_dir):
        package_dir = packages_dir + os.sep + package
        if os.path.isdir(package_dir):
            for file in os.listdir(package_dir):
                if file.endswith('.apk'):
                    apk_file = package_dir + os.sep + file
                    if os.path.isfile(apk_file):
                        output_file = '/tmp/tmp_AndroidManifest.xml'
                        parse_android_manifest(apk_file, output_file)
                        try:
                            count_comp(output_file)
                        except Exception as e:
                            print('Scan file '+ file + ' error, ' + str(e))
                            continue

if len(sys.argv) != 2:
    print('search_comp.py: Missing parameters, usage: python search_comp.py dir')
    sys.exit(1)
scan_dir(sys.argv[1])
