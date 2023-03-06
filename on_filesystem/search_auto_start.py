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

def get_package_name(manifest):
    return manifest.getAttribute('package')

def get_application(manifest):
    return manifest.getElementsByTagName('application')[0]

def get_services(application):
    return application.getElementsByTagName('service')

def get_content_providers(application):
    return application.getElementsByTagName('provider')

def get_component_intent_filters(component):
    return component.getElementsByTagName('intent-filter')

def get_intent_filter_actions(intent_filter):
    return intent_filter.getElementsByTagName('action')

def is_component_exported(component):
    exported = component.getAttribute('android:exported')
    if exported == 'true':
        return True
    elif exported == 'false':
        return False
    else:
        return len(get_component_intent_filters(component)) != 0

def filter(item):
    if 'push' in item:
        return False
    if 'message' in item:
        return False
    if 'huawei' in item:
        return True
    if 'xiaomi' in item:
        return True
    if 'vivo' in item:
        return True
    if 'oppo' in item or 'oplus' in item:  
        return True
    if 'honor' in item:
        return True
    if 'mtk' in item:
        return True
    if 'google' in item:
        return True
    if 'hisi' in item:
        return True
    return False

def search(xml_content):
    manifest_file_content = minidom.parse(xml_content)

    manifest = manifest_file_content.documentElement
    package_name = get_package_name(manifest)
    application = get_application(manifest)
    
    services = get_services(application)
    content_providers = get_content_providers(application)

    result = []
    
    for service in services:
        comp_name = get_android_name(service)
        intent_filters = get_component_intent_filters(service)
        for intent_filter in intent_filters:
            actions = get_intent_filter_actions(intent_filter)
            for action in actions:
                action_name = get_android_name(action)
                if filter(action_name):
                    result.append({'comp': comp_name, 'type': 'service' ,'item': action_name})
    
    for content_provider in content_providers:
        comp_name = get_android_name(content_provider)
        authorities = content_provider.getAttribute('android:authorities')
        if filter(authorities):
            result.append({'comp': comp_name, 'type': 'provider' ,'item': authorities})
    
    return package_name, result

def scan_dir(packages_dir):
    for package in os.listdir(packages_dir):
        if 'auto_generated_rro_product' in package:
            print('Skip auto_generated_rro_product: ' + package)
            continue
        package_dir = packages_dir + os.sep + package
        if os.path.isdir(package_dir):
            for file in os.listdir(package_dir):
                if file.endswith('.apk'):
                    apk_file = package_dir + os.sep + file
                    if os.path.isfile(apk_file):
                        output_file = '/tmp/tmp_AndroidManifest.xml'
                        parse_android_manifest(apk_file, output_file)
                        try:
                            package_name, result = search(output_file)
                            print_result(package_name, result)
                        except Exception as e:
                            print('Scan file '+ file + ' error, ' + str(e))
                            continue
        elif package.endswith('.apk'):
            apk_file = package_dir
            if os.path.isfile(apk_file):
                output_file = '/tmp/tmp_AndroidManifest.xml'
                parse_android_manifest(apk_file, output_file)
                try:
                    package_name, result = search(output_file)
                    print_result(package_name, result)
                except Exception as e:
                    print('Scan file '+ file + ' error, ' + str(e))
                    continue

def print_result(package_name, result):
    print(package_name)
    for item in result:
        print('\t' + str(item))

if len(sys.argv) != 2:
    print('search_auto_start.py: Missing parameters, usage: python search_auto_start.py dir')
    sys.exit(1)
scan_dir(sys.argv[1])
