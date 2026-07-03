init = '/mnt/e/桌面/zd/floatmask_py/.buildozer/android/platform/python-for-android/pythonforandroid/recipes/python3/__init__.py'
with open(init) as f:
    content = f.read()

# Fix the broken line
bad = """            self.patches.append('patches/3.14_fix_remote_debug.patch'
        'patches/3.14_android_preadv.patch',)"""
good = """            self.patches.append('patches/3.14_fix_remote_debug.patch')
            self.patches.append('patches/3.14_android_preadv.patch')"""

content = content.replace(bad, good)
with open(init, 'w') as f:
    f.write(content)
print('Fixed')
