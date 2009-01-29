#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2003-2007  Robey Pointer <robey@lag.net>
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paramiko is distrubuted in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA.

"""
Sample script showing how to do local port forwarding over paramiko.

This script connects to the requested SSH server and sets up local port
forwarding (the openssh -L option) from a local port through a tunneled
connection to a destination reachable from the SSH server machine.
"""

import getpass
import os
import socket
import select
import SocketServer
import sys,commands,thread,time
import tunnels_conf_reader #test to see if Py2Exe wants that
from tunnels_conf_reader import getJSONSettings

import paramiko #portable full ssh2 implementation based on sockets
import paramiko.pipe #for cx_freeze to work when packaging

successfullyMappedPorts = {}
g_verbose = True # global

#-------parameters parsing--------
ENABLE_UNIX_PORTUSER_KILLING = "-k" in sys.argv #global # provokes use of fuser -k to free local used ports before binding to them
if ENABLE_UNIX_PORTUSER_KILLING:
    import platform
    plat = platform.system().lower()
    l = ("linux","darwin","bsd","sunos","solaris")
    if not any([a in plat for a in l]):
	print "you don't seem to be on a unix-like system, the -k option may not work."
	answer = raw_input("(d)isable this option and continue? continue (w)ithout disabling? or (q)uit now? [d/w/Q]").lower().strip()
	if answer == "w":
	    pass
	elif answer == "d":
	    ENABLE_UNIX_PORTUSER_KILLING = False
	else: #q or whatever is entered
	    sys.exit(1)


if "-h" in sys.argv or "--help" in sys.argv:
    print "Usage: %s [-k]"
    print "Parses tunneling info from accompanying tunnelsSettings.json file and establishes the related tunnels."
    print
    print "  -k\tTry to kill other processes that have binded to the local ports to be used. For Unixes only with sudo/root rights."
    print "  -h/--help\tPrint this help."
    sys.exit(2)

class ForwardServer (SocketServer.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True
    

class Handler (SocketServer.BaseRequestHandler):

    def handle(self):
        try:
            chan = self.ssh_transport.open_channel('direct-tcpip',
                                                   (self.chain_host, self.chain_port),
                                                   self.request.getpeername())
        except Exception, e:
            verbose('Incoming request to %s:%d failed: %s' % (self.chain_host,
                                                              self.chain_port,
                                                              repr(e)))
            return
        if chan is None:
            verbose('Incoming request to %s:%d was rejected by the SSH server.' %
                    (self.chain_host, self.chain_port))
            return

        verbose('Connected!  Tunnel open %r -> %r -> %r' % (self.request.getpeername(),
                                                            chan.getpeername(), (self.chain_host, self.chain_port)))
        while True:
            r, w, x = select.select([self.request, chan], [], [])
            if self.request in r:
                data = self.request.recv(1024)
                if len(data) == 0:
                    break
                chan.send(data)
            if chan in r:
                data = chan.recv(1024)
                if len(data) == 0:
                    break
                self.request.send(data)
        chan.close()
        self.request.close()
        verbose('Tunnel closed from %r' % (self.request.getpeername(),))


def forward_tunnel(mapping_name,local_port, remote_host, remote_port, transport):
    global successfullyMappedPorts
    # this is a little convoluted, but lets me configure things for the Handler
    # object.  (SocketServer doesn't give Handlers any way to access the outer
    # server normally.)
    class SubHander (Handler):
        chain_host = remote_host
        chain_port = remote_port
        ssh_transport = transport
    mapping_descr_str = "%s:\tlocalhost:\t%d\t=>\t%s:%d" % (mapping_name,local_port,remote_host,remote_port)
    print "establishing connection through tunnel:",mapping_descr_str
    try:
	successfullyMappedPorts[mapping_name] = mapping_descr_str
	ForwardServer(('', local_port), SubHander).serve_forever()
    except Exception,e:
	print e,"your OS doesn't want you to bind to %s. All other ports should work though." % (local_port,)
	print "...Rerun this program as root/administrator user if you really need port %s." % (local_port,)
	if not ENABLE_UNIX_PORTUSER_KILLING and local_port >= 1024:
	    print "...This port is >= 1024, if you are on a Unix system, rerun with option -k."
	successfullyMappedPorts.pop(mapping_name)


def verbose(s):
    if g_verbose:
        print s

def makeThreads(destination,portmappings,transportObject):
    global ENABLE_UNIX_PORTUSER_KILLING
    parameters = []
    if ENABLE_UNIX_PORTUSER_KILLING:
	print "ports freeing is enabled."
	groups = commands.getoutput("groups").strip().split()
	isroot = "root" in groups
	runasroot = lambda aCommandString : commands.getoutput(("sudo" if not isroot else "")+ " "+aCommandString).strip()
	    
    for mapping in portmappings:
	if ENABLE_UNIX_PORTUSER_KILLING:
	    print "trying to see if port-freeing is needed for",mapping
	    l = runasroot("fuser %s/tcp" % (mapping["localport"],))
	    if l: #if there was some user of the the port
		print l+". Port",mapping["localport"],"is in use. Trying to free it."
		l = runasroot("fuser -k %s/tcp" % (mapping["localport"],))
		l = runasroot("fuser %s/tcp" % (mapping["localport"],))
		if not l:
		    print "Occupying programm was killed."
		else:
		    print l,"Couldn't kill occupying program."
	    else:
		print "Port",mapping["localport"],"was free. Not freeing."
        parameters.append((mapping["name"],mapping["localport"],destination,mapping["destinationport"],transportObject)) #adding fct paremeters to passed to forward_tunnel later in one shot
    #running all tunnels as threads in one shot
    for p in parameters:
	thread.start_new_thread(forward_tunnel,p) #returns a thread id or(?) handle but we don't care

    time.sleep(3)
    q = ""
    print '_________________________________________________________________'
    while q.strip() != "q":
	print "Ports tunneled and active are:"
	for l in successfullyMappedPorts.values(): print l
	q = raw_input("Press q to close all connections and kill this process: ") #daemon behaviour
    sys.exit(0)

def main():
    settings = getJSONSettings()
    gate,destination,portmappings = settings["gate"],settings["destination"],settings["portmappings"]

    #get username and password from user if not provided
    username = raw_input("Enter login for "+gate["hostname"]+":") if "login" not in gate else gate["login"]
    password = getpass.getpass('Enter SSH password: ') if "password" not in gate else gate["password"]

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.WarningPolicy())

    verbose('Connecting to ssh host %s:%d ...' % (gate["hostname"], gate["port"]))
    try:
	#print "client.connect(%s, %s, username=%s,password=%s)" % (gate["hostname"], gate["port"], username,password) #keep this as debug only
        client.connect(gate["hostname"], gate["port"], username=username,password=password)
    except Exception, e:
        print '*** Failed to connect to %s:%d: %r.' % (gate["hostname"], gate["port"], e)
	print "Is one of the provided login and password not correct?"
        sys.exit(1)

    #verbose('Now forwarding port %d to %s:%d ...' % (options.port, remote[0], remote[1]))
    verbose('Logged into %s:%d successfully.' % (gate["hostname"],gate["port"]))

    try:
	verbose('Will now try map ports from localhost through the latter server towards %s.' % (destination["hostname"],))
	makeThreads(destination["hostname"],portmappings,client.get_transport())
        #forward_tunnel(options.port, remote[0], remote[1], )
    except KeyboardInterrupt:
        print 'C-c: Port forwarding stopped.'
        sys.exit(0)

if __name__ == '__main__':
    main()
