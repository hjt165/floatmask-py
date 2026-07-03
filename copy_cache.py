import shutil
import os

src_base = '/root/.buildozer/android/android/platform/build-arm64-v8a_armeabi-v7a/packages'
dst_base = '/mnt/e/桌面/zd/floatmask_py/.buildozer/android/platform/build-arm64-v8a/packages'

pkgs = ['libffi', 'openssl', 'sdl2_image', 'sdl2_mixer', 'sdl2_ttf', 'sqlite3', 'python3', 'sdl2', 'pyjnius', 'kivy']

for pkg in pkgs:
    src = os.path.join(src_base, pkg)
    dst = os.path.join(dst_base, pkg)
    if os.path.isdir(src):
        os.makedirs(dst, exist_ok=True)
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isfile(s):
                shutil.copy2(s, d)
                print(f'copied {pkg}/{item}')
    else:
        print(f'missing {pkg}')
