#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pprint import pprint
import sys, urllib
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
TUNNELS_CONFIG_FILE = "tunnels_conf.json"

def getJSONSettings():
    global TUNNELS_CONFIG_FILE

    OVERRIDING_CONF = False
    try:
	from dict_additions import add_dicts_in_place
    except Exception,e:
	print e,"configuration overriding will not be possible"
    else:
	try:
	    from tunnels_overriding_conf import overriding_conf #TODO FINISH THIS
	except Exception,e:
	    print e
	    print "using %s file for login+password (or command-line if either of those is not written in it)" % (TUNNELS_CONFIG_FILE,)
	    print "but not using any overriding configuration file."
	    OVERRIDING_CONF = False
	else:
	    OVERRIDING_CONF = True
	    print "using tunnels_overriding_conf.py file for forced settings"

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
    try:
	settings = json.loads(settingsStr)
    except Exception,e:
	print e
	print "Couldn't load %s correctly." % TUNNELS_CONFIG_FILE
	print "Exiting."
	sys.exit(1)
    if OVERRIDING_CONF:
	try:
	    add_dicts_in_place(settings,overriding_conf,True)
	except Exception,e:
	    print e
	    print "Your tunnels_overriding_conf.py file's overriding_conf dictionary cannot override the %s dictionary properly." % TUNNELS_CONFIG_FILE
	    print "Make sure the structure of the former matches at the of the latter."
	    print "Exiting."
	    sys.exit(1)
	else:
	    print "managed to import overriding configuration from tunnels_overriding_conf.py"

    #interpret "fromweb" field if presentfor server IP retrieval
    #	the settings["destination"]["hostname"] field is replaced with an IP address/hostname
    destHostname = settings["destination"]["hostname"]
    if type(destHostname) is dict: 
    	if destHostname.has_key("fromweb"):
		try: 
		    u = destHostname["fromweb"]
		    up = urllib.urlopen(u)
		except Exception,e:
		    print e,"could connect to:",u
		    sys.exit(1)
		settings["destination"]["hostname"] = up.readlines()[0].strip()
		up.close()
	else:
		print "ok destination.hostname is a dictionary, though I can't find any \"fromweb\" key-value pair in it.\nExiting."
		sys.exit(1)
    else: #if destHostname is not a dict
	    try:
		    destHostname = str(destHostname)
	    except:
		    print "destination.hostname must be some kind of a string.\nExiting."
		    sys.exit(1)
	    else:
		    pass #it's ok we have a string for the host, that's what we want in the end
	
    if "port" not in settings["gate"]:
	settings["gate"]["port"] = 22
	
    return settings

if __name__ == "__main__":
    print "this script is not meant to be run standalone... you're doing debugging supposedly."
    print getJSONSettings()
