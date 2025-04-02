# Android-Tools
- Some tools when playing with Android

## Usage 
**dump_fs**: These scripts is used to dump target's filesystem (like apps or framework jars).
* `dump_android.py`: Binary dump script for Android

**on_device**: You should run these scripts on a real device or emulator via adb shell.
* `adb_root.sh`
* `cat_proc_maps.sh`: Search anything in all processes memory maps.

**on_filesystem**: You should run these scripts on a dumped Android filesystem using `dump_android.py`.
* `vulscan/get_accessible_components.py`: Get accessible Android components in system apps.
* `vulscan/get_accessible_services.py`: Get accessible Android binder services in system.
* `vulscan/search_deeplink.py`: Search `android.intent.category.BROWSABLE` intent filter in system.
* `dump_app_policy.sh`: Dump human readable SELinux policy
* `gen_jadx_project.py`: Generate jadx project files for packages folder (`dump_android.py` will do this task when use `-j/--jadx` parameter.).
* `install_all.sh`: Install many Android applications.
* `search_symbol.py`: Search anything in all binaries (Python version).
* `search_symbol.sh`: Search anything in all binaries (Shell version).

**on_source**: You should run these scripts on AOSP source tree.
* `git_pull_all.sh`: Run `git pull` for all projects.
* `repo_sync_all.sh`: Run `repo sync` for all projects

**poc**: PoC of some vulnerabilities.
* `CVE-2017-13156.py`: PoC of Jauns vulnerability CVE-2017-13156
