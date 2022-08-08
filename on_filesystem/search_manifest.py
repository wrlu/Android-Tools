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

def get_activities(application):
    return application.getElementsByTagName('activity')    

def get_component_intent_filters(component):
    return component.getElementsByTagName('intent-filter')

def is_component_exported(component):
    exported_attr = component.getAttribute('android:exported')
    if exported_attr == 'true':
        return True
    elif exported_attr =='false':
        return False
    else:
        return len(get_component_intent_filters(component)) != 0

def is_browsable_category(category):
    return get_android_name(category) == 'android.intent.category.BROWSABLE'

def is_activity_browsable(activity):
    if is_component_exported(activity):
        intent_filters = get_component_intent_filters(activity)
        for intent_filter in intent_filters:
            actions = intent_filter.getElementsByTagName('action')
            data = intent_filter.getElementsByTagName('data')
            categories = intent_filter.getElementsByTagName('category')
            for category in categories:
                if is_browsable_category(category):
                    return True
    return False

def get_browsable_activities(xml_content):
    manifest_file_content = minidom.parse(xml_content)

    manifest = manifest_file_content.documentElement
    package_name = get_package_name(manifest)
    application = get_application(manifest)
    activities = get_activities(application)
    
    browsable_activities = []

    for activity in activities:
        if is_activity_browsable(activity):
            full_activity_name = package_name + '/' + get_android_name(activity)
            print(full_activity_name)
            browsable_activities.append(full_activity_name)
    
    return browsable_activities

def scan_dir(packages_dir):
    browsable_activities = []
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
                            tmp_result = get_browsable_activities(output_file)
                            browsable_activities.append(tmp_result)
                        except Exception as e:
                            print('Scan file '+ file + ' error, ' + str(e))
                            continue
    return browsable_activities

if len(sys.argv) != 2:
    print('search_manifest.py: Missing parameters, usage: python search_manifest.py dir')    
scan_dir(sys.argv[1])
