from os import path,system
import sys

#check we are on windows to continue
p = sys.platform.lower()
if not p.startswith("win"):
    yN=raw_input("you are not on Windows (os.platform=%s). Continue ? [y/N*]" % (p,)).strip().lower()
    if yN == 'y':
        sys.exit(2)

#check we have py2exe to continue
try:
    import py2exe
    print "You have pyexe installed. That's good."
except:
    print "You don't have py2exe. You must install it first"
    print "Exiting."
    raw_input()
    sys.exit(1)

#find absolute paths for the folders around
directoryContainingThisScript = path.abspath(sys.path[0])
build_tools_path = path.join(directoryContainingThisScript,"build_tools")

#get the path to the python.exe executable on this system (Python24?25?26? where ?)
for possiblePythonInstDir in sys.path:
    if "\\\\Python2" in possiblePythonInstDir:
        break
possiblePythonInstDir = possiblePythonInstDir.replace("\\\\","\\") #replace double backslashes with single ones
possiblePythonInstDir = possiblePythonInstDir[:possiblePythonInstDir.find('\\',possiblePythonInstDir.find("Python"))]
#after this line, we have possiblePythonInstDir like "C:\Python26"
python = path.join(possiblePythonInstDir,"python.exe") # like "C:\Python26\python.exe"
setupEmbedded = '"'+path.join(build_tools_path,"Win32setupEmbeddedLogin.py")+'"'
setupNoLogin = '"'+path.join(build_tools_path,"Win32setupNoLogin.py")+'"'
executableName = "multi_tunneler.exe"
dirEmbedded = "Win32multi_tunnelerEmbeddedLogin"
dirNoLogin = "Win32multi_tunnelerNoLogin"
system("%s %s py2exe" % (python,setupEmbedded))
system("rm -rf build") #remove the build/ folder where all intermediate built files are stored
print "done building executable for Win32multi_tunnelerEmbeddedLogin target."
yN=raw_input("do you want to test run the executable now? [y/N*]").strip().lower()
print "cd %s; %s; cd .." % (dirEmbedded,executableName)
if yN == 'y': system("cd %s & %s & cd .." % (dirEmbedded,executableName))
system("%s %s py2exe" % (python,setupNoLogin))
system("rm -rf build") #remove the build/ folder where all intermediate built files are stored
print "done building executable for Win32multi_tunnelerNoLogin target."
yN=raw_input("do you want to test run the executable now? [y/N*]").strip().lower()
if yN == 'y': system("cd %s & %s & cd .." % (dirNoLogin,executableName))
raw_input("Building done, press any key to continue...")