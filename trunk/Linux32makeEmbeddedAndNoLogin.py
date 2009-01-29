#!/usr/bin/env python
# -*- coding: utf-8 -*-
from commands import getoutput
from os import path,system,getcwd
import sys

#prints a given command's string and run it
def run(txt):
    print txt
    if False:
	raw_input()
    #a = getoutput(txt)
    #print a
    a = system(txt)
    return a

#<==============VARIABLES TO CHANGE BY YOU ================>
#those path are made absolute so as
cwd = getcwd()
pyinstallerroot = path.join('%s' % path.abspath(cwd).replace(' ','\\ '),"pyinstaller-1.3")
sourceroot = '%s' % path.abspath(cwd).replace(' ','\\ ') #same path as the folder which contains this very script
#<===========================END==========================>

#global variables
EmbeddedLogin,NoLogin = (322,415) #targetConstant values
targetNames = {EmbeddedLogin:"EmbeddedLogin",NoLogin:"NoLogin"}
outputdirPrefix = path.join(sourceroot,"Linux32multi_tunneler") #note, path.join() doesn't add '/' at the end, which is what we want for outputdir generation in buildTarget()
loginfile = path.join(sourceroot,"provided_login_info.py") #used for EmbeddedLogin, unused for NoLogin
jsonfile = path.join(sourceroot,"tunnels_conf.json")
mainscriptfile = path.join(sourceroot,"multi_tunneler.py") #the script that contains our main and from which all modules dependencies will be scanned

#settings common to both build targets
def initBuild():
    global pyinstallerroot
    run("python %s -e" % (path.join(pyinstallerroot,"source/linux/Make.py"),)) #we want elf format hence the -e, because ELF allows to have one single file in an single executable, no .zip archive lying around.
    run("make %s" % (path.join(pyinstallerroot,"source/linux/Makefile"),))
    run("python %s" % (path.join(pyinstallerroot,"Configure.py"),))


def buildTarget(targetConstant):
    global EmbeddedLogin,NoLogin,targetNames,loginfile,mainscriptfile,jsonfile,outputdirPrefix,pyinstallerroot
    if targetConstant not in (EmbeddedLogin,NoLogin):
	print "targetConstant=",targetConstant,"should be one of",(EmbeddedLogin,NoLogin),"instead."
	print "Exiting."
	sys.exit(1)

    targetName = targetNames[targetConstant]
    print "<==========DOING TARGET %s==============>" % (targetName.upper(),)

    if targetConstant == NoLogin:
	run("rm %s" % (path.splitext(loginfile)[0]+'.pyc',)) #remove .pyc file for loginfile
	run("mv %s %sAA" % (loginfile,loginfile))

    outputdir = outputdirPrefix+targetName
    run("python %s --onefile %s -o %s" % (path.join(pyinstallerroot,"Makespec.py"),mainscriptfile,outputdir,))
    mainscriptfilePrefix = executablename = path.splitext(path.basename(mainscriptfile))[0]
    specfilename = mainscriptfilePrefix+".spec"
    specfile = path.join(outputdir,specfilename)
    run("python %s %s" % (path.join(pyinstallerroot,"Build.py"),specfile))
    run("cp %s %s" % (jsonfile,outputdir)) #add json file to folder
    run("rm -rf %s %s" % (path.join(outputdir,"build"+mainscriptfilePrefix),path.join(outputdir,"warn"+mainscriptfilePrefix+".txt"))) # clean folder for intermediary build files and "useless" warning file
    run("rm %s" % path.join(outputdir,mainscriptfilePrefix+".spec")) #remove useless .spec file

    if targetConstant == NoLogin:
	run("mv %sAA %s" % (loginfile,loginfile))

    print "<==========FINISHED TARGET %s==============>" % (targetName.upper(),)
    run("ls -l "+outputdir)
    yN = raw_input("run program %s now for a test [y/N*]?" % (executablename,)).strip().lower()
    if yN == "y":
	executablefile = path.join(outputdir,executablename)
	run("chmod +x "+executablefile)
	system("cd %s; ./%s ; cd %s" % (outputdir,executablename,pyinstallerroot)) #we're obliged to do cd here otherwise the executable will look for the jsonfile inside the directory we're calling from which will make an error.
    raw_input("Done working on target. Press any key to continue to next job or to program exit if no more job...")

if __name__=="__main__":
    initBuild()
    buildTarget(EmbeddedLogin)
    buildTarget(NoLogin)
    sys.exit(0)
