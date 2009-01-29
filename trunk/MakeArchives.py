#!/usr/bin/env python
#unices & windows
from __future__ import with_statement
from contextlib import closing
from zipfile import ZipFile, ZIP_DEFLATED
import os
from os import system,listdir,getcwd
import sys

def zipdir(basedir, archivename=None,giveZObjectToUse=None,excludeSvnFolders=True):
	assert os.path.isdir(basedir)
	if not giveZObjectToUse:
		Z=ZipFile(archivename, "w", ZIP_DEFLATED)
	with Z as z:
	        for root, dirs, files in os.walk(basedir):
	            #NOTE: ignore empty directories
	                for fn in files:
		                absfn = os.path.join(root, fn)
				print absfn
				if ".svn" in os.path.split(absfn): continue #don't write .svn/ folders and .svn/* files
		                zfn = absfn[len(basedir)+len(os.sep):] #XXX: relative path
		                z.write(absfn, zfn)
	if not giveZObjectToUse:
		Z.close()

if sys.platform.startswith("win"): isunix=False
else: isunix=True

#system("sh cleanCompiledObjectsNow.sh")
#system("python Linux32makeEmbeddedAndNoLogin.py")
folderPrefs=("Win32","Linux32")
folderSufs=("multi_tunnelerEmbeddedLogin","multi_tunnelerNoLogin")
#create folder to store archives into it, if it doesn't exist yet
outdir="Archives"
if outdir not in listdir(getcwd()):
	system("%s %s" % (("mkdir" if isunix else "MD"),outdir))

#compress each build folder into a single tar.gz archive
archivesdone=[]
for folderPref in folderPrefs:
	print "========== %s archives ==========" % (folderPref)
	mustzip = not(isunix) or "Win" in folderPref
	for folderSuf in folderSufs:
		srcrep=folderPref+folderSuf
		ext=(".zip" if mustzip else ".tar.gz")
		if srcrep in os.listdir(getcwd()):
			arch = srcrep+ext
			if mustzip: zipdir(srcrep,arch)
			else: system("tar czvf %s %s" % (arch,srcrep)) #the -C option does not seem to work...
			system("%s %s %s" % (("mv" if isunix else "move"),arch,outdir))
			archivesdone.append(arch)

#make source archive
def makeSourceArchive(filelist,dirlist,fileprefix):
	global archivesdone,outdir,isunix
	name = fileprefix + (".zip" if not isunix else ".tar.gz")
	if not isunix:
		Z = zipfile.ZipFile(name,mode="w",compression=zipfile.DEFLATED)
		for f in filelist:
			Z.write(f)
		for d in dirlist:
			zipdir(d,None,Z)
		Z.close()
	else:
		system("tar czvf %s --exclude=*.svn %s %s" % (name,' '.join(filelist),' '.join(dirlist)))
	system("%s %s %s" % ("mv" if isunix else "move",name,outdir))
	archivesdone.append(name)

print "========== simple source archive without libraries =========="
filelist = ("multi_tunneler.py","tunnels_conf.json","tunnels_conf_reader.py","provided_login_info.py")
dirlist= () 
fileprefix = "multi_tunnelerSource"
makeSourceArchive(filelist,dirlist,fileprefix)

print "========== source archive with libraries =========="
filelist = ("multi_tunneler.py","tunnels_conf.json","tunnels_conf_reader.py","provided_login_info.py")
dirlist= ("simplejson","paramiko")
fileprefix = "multi_tunnelerSourceWithLibs"
makeSourceArchive(filelist,dirlist,fileprefix)

print "========== source archive with libraries and build tools =========="
filelist = ("*.py","*.sh","*.json")
dirlist= ("simplejson","paramiko","build_tools","pyinstaller-1.3") #will build on Unices without any additional dependencies, and on Windows with py2exe installed (we have chosen pyinstaller-1.3 to take py2exe's place on linux)
fileprefix = "multi_tunnelerSourceWithLibsAndBuildTools"
makeSourceArchive(filelist,dirlist,fileprefix)

print "====== conclusion ======="
print "done creating archives %s into folder %s." % (', '.join(archivesdone),outdir)
print "Contents of the %s folder:" % outdir
system("%s %s" % (("ls -l" if isunix else "dir"),outdir))

