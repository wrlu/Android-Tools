# Android-Tools
- Some tools when playing with Android

## Usage 
- dump_fs: These scripts is used to dump target's filesystem or binaries (like apps or framework jars).
    - dump_apks.sh: Dump all apks (include third-party apks)
- on_device: You should run these scripts or binaries on a real device or emulator.
    - cat_proc_maps.sh: Search anything in all processes memory maps.
- on_filesystem: You should run these scripts or binaries in a dumped Android filesystem.
    - scan_all.py: Call some external binary to run with a whole folder (like /system/app).
    - search_symbol.sh: Search anything in all binaries.
- on_source: You should run these scripts or binaries on AOSP source tree.
    - git_pull_all.sh: Run `git pull` for all projects.
    - repo_sync_all.sh: Run `repo sync` for all projects