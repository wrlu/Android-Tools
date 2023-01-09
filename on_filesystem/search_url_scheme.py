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
    exported = component.getAttribute('android:exported')
    if exported == 'true':
        return True
    elif exported =='false':
        return False
    else:
        return len(get_component_intent_filters(component)) != 0

def is_browsable_category(category):
    return get_android_name(category) == 'android.intent.category.BROWSABLE'

def is_activity_browsable(activity):
    if is_component_exported(activity):
        intent_filters = get_component_intent_filters(activity)
        for intent_filter in intent_filters:
            categories = intent_filter.getElementsByTagName('category')
            for category in categories:
                if is_browsable_category(category):
                    return True
    return False

def get_activity_pattern(activity):
    intent_filters = get_component_intent_filters(activity)
    patterns = []
    for intent_filter in intent_filters:
        actions = intent_filter.getElementsByTagName('action')
        action_pattern = 'action=[ '
        for action in actions:
            action_name = get_android_name(action)
            action_pattern = action_pattern + action_name + ' '
        action_pattern = action_pattern + ']'

        data = intent_filter.getElementsByTagName('data')
        scheme = ''
        host = ''
        port = ''
        path = ''
        pathPrefix = ''
        pathPattern = ''
        mimeType = ''
        
        for per_data in data:
            scheme = per_data.getAttribute('android:scheme')
            host = per_data.getAttribute('android:host')
            port = per_data.getAttribute('android:port')
            path = per_data.getAttribute('android:path')
            pathPrefix = per_data.getAttribute('android:pathPrefix')
            pathPattern = per_data.getAttribute('android:pathPattern')
            mimeType = per_data.getAttribute('android:mimeType')
        
        if scheme == '':
            scheme = '*'
        if host == '':
            host = '*'
        if port == '':
            port = '*'
            full_host = f'{scheme}://{host}'
        else:
            full_host = f'{scheme}://{host}:{port}'
        
        if mimeType == '':
            mimeType = '*'
        
        has_path = False
        if path != '':
            data_pattern = f'data=[{full_host}{path} | mimeType={mimeType}]'
            has_path = True
        if pathPrefix != '':
            data_pattern = f'data=[{full_host}{pathPrefix} | mimeType={mimeType}]'
            has_path = True
        if pathPattern != '':
            data_pattern = f'data=[{full_host}/{pathPattern} | mimeType={mimeType}]'
            has_path = True
        if has_path is False:
            data_pattern = f'data=[{scheme}://{host}:{port} | mimeType={mimeType}]'
        
        pattern = f'{action_pattern}, {data_pattern}'
        patterns.append(pattern)
    return patterns

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
            uri_patterns = get_activity_pattern(activity)
            for uri_pattern in uri_patterns:
                print('\t' + uri_pattern)
            browsable_activities.append({'name': full_activity_name, 'patterns': uri_patterns})
    
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

if len(sys.argv) != 2:
    print('search_url_scheme.py: Missing parameters, usage: python search_url_scheme.py dir')
    sys.exit(1)
scan_dir(sys.argv[1])
