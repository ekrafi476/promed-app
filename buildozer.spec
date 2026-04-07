[app]
title = ProMed Aero
package.name = promed
package.domain = com.promed.enterprise
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy==2.3.0,kivymd==1.2.0,sqlite3,pillow
orientation = portrait
android.api = 33
android.minapi = 21
android.permissions = WRITE_EXTERNAL_STORAGE, CAMERA, READ_EXTERNAL_STORAGE
icon.filename = promed.png
android.archs = arm64-v8a
