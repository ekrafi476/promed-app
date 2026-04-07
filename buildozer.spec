[app]
title = ProMed Aero
package.name = promedapp
package.domain = com.promed.enterprise
source.dir = .
source.include_exts = py,kv,db
version = 1.0
# Requirements fixed for M3 Material design
requirements = python3,kivy==2.3.0,kivymd==1.2.0,sqlite3
orientation = portrait
fullscreen = 0
android.api = 33
android.minapi = 21
android.accept_sdk_license = True
# Standard permissions
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
android.archs = arm64-v8a
p4a.branch = master
