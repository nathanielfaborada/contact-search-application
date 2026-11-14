[app]
title = Phonebook
package.name = phonebook
package.domain = org.personal.contactapp
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,csv
source.exclude_dirs = .git, .github, build, dist, scripts
version = 1.0.0
requirements = python3,kivy

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,CALL_PHONE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
