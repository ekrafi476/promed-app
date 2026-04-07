[app]
title = ProMed Aero
package.name = promed
package.domain = com.promed.enterprise
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy==2.2.1,kivymd==1.1.1,sqlite3,pillow
orientation = portrait
android.api = 31
android.minapi = 21
android.permissions = WRITE_EXTERNAL_STORAGE, CAMERA, READ_EXTERNAL_STORAGE
icon.filename = promed.png
# Splash Screen
presplash.filename = promed.png
android.archs = arm64-v8a
