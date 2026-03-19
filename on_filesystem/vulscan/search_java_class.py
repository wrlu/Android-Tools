import os
import sys
from androguard.misc import AnalyzeAPK

def process_apk(apk_file, class_name_to_find):
    """
    Analyzes a single APK file to see if it contains the specified Java class.

    :param apk_file: Path to the APK file.
    :param class_name_to_find: The Java class name in standard format (e.g., "com.example.MyClass").
    :return: True if the class is found, False otherwise.
    """
    print(f"[*] Analyzing: {apk_file}")
    try:
        # Analyze the APK. This is the most time-consuming part.
        a, d, dx = AnalyzeAPK(apk_file)

        # Convert the user-provided class name (e.g., com.example.Foo)
        # to the Dalvik internal format used by androguard (e.g., Lcom/example/Foo;).
        dalvik_class_name = f"L{class_name_to_find.replace('.', '/')};"

        # dx.get_classes() returns a list of ClassAnalysis objects.
        for cls in dx.get_classes():
            if cls.name == dalvik_class_name:
                return True  # Found a match

        # If the loop completes, the class was not found.
        return False

    except Exception as e:
        # Catch potential errors during analysis (e.g., corrupted APKs).
        print(f"[!] Error analyzing {apk_file}: {e}", file=sys.stderr)
        return False

def scan_dir(target_dir, class_name):
    """
    Scans a directory for APK files and checks for the existence of a specific Java class.

    :param target_dir: The directory to scan.
    :param class_name: The Java class name to search for.
    :return: A list of paths to APKs that contain the class.
    """
    matched_apks = []

    if not os.path.isdir(target_dir):
        print(f"[!] Error: Directory not found at '{target_dir}'", file=sys.stderr)
        return matched_apks

    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if file.endswith('.apk'):
                apk_file = os.path.join(root, file)
                if os.path.isfile(apk_file):
                    # Process each APK file found.
                    if process_apk(apk_file, class_name):
                        # If the class is found, add the APK path to our list.
                        matched_apks.append(apk_file)
                        
    return matched_apks

def main():
    """
    Main function to handle command-line arguments and orchestrate the scan.
    """
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <directory_to_scan> <java_class_name>")
        print("Example: python search_java_class.py /path/to/apks com.example.VulnerableClass")
        sys.exit(1)
    
    scan_directory = sys.argv[1]
    java_class_to_find = sys.argv[2]

    print(f"--- Starting scan for class '{java_class_to_find}' in directory '{scan_directory}' ---")
    
    matched_files = scan_dir(scan_directory, java_class_to_find)
    
    print("--- Scan Complete ---")
    if matched_files:
        print(f"[+] Found the class '{java_class_to_find}' in the following files:")
        for apk_path in matched_files:
            print(f"  - {apk_path}")
    else:
        print(f"[-] The class '{java_class_to_find}' was not found in any APKs under the specified directory.")
    
if __name__ == '__main__':
    main()
