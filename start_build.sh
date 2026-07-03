#!/bin/bash
export PIP_BREAK_SYSTEM_PACKAGES=1
cd /mnt/e/桌面/zd/floatmask_py
buildozer -v android debug > /mnt/e/桌面/zd/floatmask_py/build.log 2>&1
echo BUILD_EXIT_CODE=\True > /mnt/e/桌面/zd/floatmask_py/build_done
