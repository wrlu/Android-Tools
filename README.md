# Android-Tools
- Some tools when playing with Android

## Usage 
**dump_fs**: These scripts is used to dump target's filesystem (like apps or framework jars).
* dump_android.py: Dump script for Android

**on_device**: You should run these scripts on a real device or emulator via adb shell.
* cat_proc_maps.sh: Search anything in all processes memory maps.

**on_filesystem**: You should run these scripts on a dumped Android filesystem using dump_fs.
* dump_app_policy.sh: Dump human readable SELinux policy
* scan_all.py: Call some external binary to run with a whole folder (like /system/app).
* search_manifest.py: Search the AndroidManifest.xml
* search_symbol.sh: Search anything in all binaries.

**on_source**: You should run these scripts on AOSP source tree.
* git_pull_all.sh: Run `git pull` for all projects.
* repo_sync_all.sh: Run `repo sync` for all projects
