from distutils.core import setup
import py2exe
from os import system
import sys

#without login info

dir= "Win32multi_tunnelerEmbeddedLogin"
sys.path.append(os.path.join(os.getcwd(),"..")) #makes the build_tools/../ folder's modules available...
                    #for importing and embedding into the final .exe
setup(
    console=["multi_tunneler.py"],
    options={"py2exe":
             {"bundle_files":1,
              "dist_dir":dir}},
    zipfile=None)

system("copy tunnels_conf.json "+dir)

