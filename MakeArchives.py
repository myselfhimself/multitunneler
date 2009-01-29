#!/usr/bin/env python
#unices & windows
from __future__ import with_statement
from contextlib import closing
from zipfile import ZipFile, ZIP_DEFLATED
import os
from os import system,listdir,getcwd
import sys

def zipdir(basedir, archivename):
	assert os.path.isdir(basedir)
	with closing(ZipFile(archivename, "w", ZIP_DEFLATED)) as z:
	        for root, dirs, files in os.walk(basedir):
	            #NOTE: ignore empty directories
	                for fn in files:
		                absfn = os.path.join(root, fn)
				print absfn
		                zfn = absfn[len(basedir)+len(os.sep):] #XXX: relative path
		                z.write(absfn, zfn)

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

print "====== conclusion ======="
print "done creating archives %s into folder %s." % (', '.join(archivesdone),outdir)
print "Contents of the %s folder:" % outdir
system("%s %s" % (("ls -l" if isunix else "dir"),outdir))

