#!/bin/sh
rm -rf build/
rm -rf Archives/
rm -r *.pyc
find -type d -name "Linux32*" | xargs rm -rf
find -type d -name "Win32*" | xargs rm -rf
