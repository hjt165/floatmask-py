[app]

# App title
title = FloatMask

# Package info
package.name = floatmask
package.domain = com.floatmask

# Source
source.dir = .
source.include_exts = py,png,jpg,kv,xml

# Version
version = 1.0

# Dependencies
requirements = python3,kivy,pyjnius,android

# Android config
android.permissions =
    SYSTEM_ALERT_WINDOW,
    FOREGROUND_SERVICE,
    WAKE_LOCK,
    RECEIVE_BOOT_COMPLETED
android.api = 33
android.minapi = 23
android.theme = Theme.Transparent
android.accept_sdk_license = True

# Foreground service
services = overlay_service:services/overlay_service.py:foreground:sticky:foregroundServiceType=specialUse

# Display
fullscreen = 0
orientation = portrait

# Build
android.arch = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 0
