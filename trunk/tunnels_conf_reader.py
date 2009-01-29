#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pprint import pprint
import sys, urllib,os
try:
    from encodings import hex_codec,ascii,idna #to avoid the error "unknown encoding: hex" on importing of simplejson, or "unknown encoding: ASCII"
    import simplejson as json#becomes json in python2.6 (not yet shipped on ubuntu intrepid)
except Exception,e:
    print e
    try:
	import json
    except Exception,e:
	print e,"impossible to import either simplejson or json modules."
	print "exiting"
	sys.exit(1)


#default settings
TUNNELS_CONFIG_FILE = os.path.join(os.path.abspath(os.getcwd()),"tunnels_conf.json")

def getJSONSettings():
    global TUNNELS_CONFIG_FILE

    FORCED_LOGIN_INFO = False
    try:
	from provided_login_info import username,password
	FORCED_LOGIN_INFO = True
	print "using provided_login_info.py file for login+password"
    except:
	FORCED_LOGIN_INFO = False
	print "using %s file for login+password (or command-line if either of those is not written in it)" % (TUNNELS_CONFIG_FILE,)
    
	#get json file's contents
    try: 
	fp = open(TUNNELS_CONFIG_FILE)
    	settingsStr = fp.read()
    	fp.close()
    except IOError,e:
    	print e,TUNNELS_CONFIG_FILE,"doesn't exist."
	print "Exiting."
	sys.exit(1)

    #parse json => python data types
    settings = json.loads(settingsStr)

    #interpret "fromweb" field if presentfor server IP retrieval
    #	the settings["destination"]["hostname"] field is replaced with an IP address/hostname
    destHostname = settings["destination"]["hostname"]
    if type(destHostname) is dict and destHostname.has_key("fromweb"):
	try:
	    u = destHostname["fromweb"]
	    up = urllib.urlopen(u)
	except Exception,e:
	    print e,"couldn't connect to:",u
	    sys.exit(1)
	settings["destination"]["hostname"] = up.readlines()[0].strip()
	up.close()
    else:
	print "if destination.hostname is a dictionary, it must have \"fromweb\" key-value pair. None found."
	print "Exiting."
	sys.exit(1)
	
    if "port" not in settings["gate"]:
	settings["gate"]["port"] = 22
	
    if FORCED_LOGIN_INFO:
	settings["gate"]["login"] = username
	settings["gate"]["password"] = password
	
    return settings
