from distutils.core import setup
import py2exe
from os import system,path,getcwd
import sys

#without login info
dir="Win32multi_tunnelerNoLogin"
sys.path.append(path.normpath(path.join(sys.path[0],".."))) #makes the build_tools/../ folder's modules available...
                    #for importing and embedding into the final .exe

setup(
    console=["multi_tunneler.py"],
    options={"py2exe":
             {"bundle_files":1,
              "dist_dir":dir,
              "excludes":["provided_login_info"]}},
    zipfile=None)

system("copy tunnels_conf.json "+dir)
