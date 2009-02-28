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
import platform
import socket
import select
import SocketServer
import sys,commands,thread,time
from tunnels_conf_reader import getJSONSettings
from subprocess import Popen
import signal #for SIGTERM constant in atexit callback
from copy import copy

import paramiko #portable full ssh2 implementation based on sockets
import paramiko.pipe #for cx_freeze to work when packaging

successfullyMappedPorts = {}
g_verbose = True # global
socatProcesses = [] #global

def isUnixPlatform():
    plat = platform.system().lower()
    l = ("linux","darwin","bsd","sunos","solaris")
    return any([a in plat for a in l])

#-------parameters parsing--------
ENABLE_UNIX_PORTUSER_KILLING = "-k" in sys.argv #global # provokes use of fuser -k to free local used ports before binding to them
if ENABLE_UNIX_PORTUSER_KILLING:
    if not isUnixPlatform():
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

#returns True/False on socat running success/failure
def udp_to_tcp_realtime_conversion(udp_listen_port,tcp_redirect_port,canRetry=True):
    global socatProcesses
    global ENABLE_UNIX_PORTUSER_KILLING
    print "starting udp=>tcp conversion daemon(socat) for localhost:%d/udp to localhost:%d/tcp" % (udp_listen_port,tcp_redirect_port)
    from commands import getoutput
    success = False
    if isUnixPlatform(): #unix
	socatCmd = getoutput("which socat").strip()
	if not socatCmd:
	    print "socat isn't installed on this platform or which cannot find it. Please install it first."
	    success = False
	else:
	    success = True
    else: #windows
	socatCmd = "socat.exe"
	if not os.path.exists(socatCmd):
	    print socatCmd,"is not in the executable's path:",os.getcwd()
	    success = False
	else:
	    success = True
    if success:
	print "socat executable found on this computer at %s. Running it." % socatCmd
	a,b = copy(udp_listen_port),copy(tcp_redirect_port) #there's race issue here maybe
	args = ("%s udp4-listen:%s,reuseaddr,fork tcp:localhost:%s" % (socatCmd,a,b)).split()
	i = Popen(args)
	#if socat has stopped right away, there must have been a problem
	time.sleep(1)
	if i.poll() is not None:
	    success = False #anyway socat will have printed something to stdout
	else:
	    socatProcesses.append(i)
    return success

def forward_tunnel(mapping_name,local_port, remote_host, remote_port, transport,udp_listen_port=None):
    global successfullyMappedPorts
    doUdp = udp_listen_port is not None
    success = udpSuccess = False
    # this is a little convoluted, but lets me configure things for the Handler
    # object.  (SocketServer doesn't give Handlers any way to access the outer
    # server normally.)
    class SubHander (Handler):
        chain_host = remote_host
        chain_port = remote_port
        ssh_transport = transport
    mapping_descr_str = "%-13slocalhost:%d/tcp\t=>\t%s:%d/tcp" % (mapping_name+":",local_port,remote_host,remote_port) + ((" & localhost:%d/udp\t=>\tlocalhost:%d/tcp" % (udp_listen_port,local_port)) if doUdp else "")
    print "establishing connection through tunnel:",mapping_descr_str
    try:
	FS = ForwardServer(('', local_port), SubHander)
	thread.start_new_thread(FS.serve_forever,())
	success = True
    except Exception,e:
	print e,"your OS doesn't want you to bind to %s. All other ports should work though." % (local_port,)
	print "...Rerun this program as root/administrator user if you really need port %s." % (local_port,)
	if not ENABLE_UNIX_PORTUSER_KILLING and local_port >= 1024:
	    print "...This port is already in use or is >= 1024, if you are on a Unix system, rerun with option -k."
	success = False
    else: #if no problem in the first FS.serve_forever <=> SSH channel just run raised no exception
	#then run udp conversion if requested
	if success and doUdp:
	    if type(udp_listen_port) is int and udp_listen_port > 0:
		try:
		    udpSuccess = udp_to_tcp_realtime_conversion(udp_listen_port,local_port)
		except Exception,e:
		    udpSuccess = False
		if not udpSuccess:
		    print "couldn't start udp conversion for udp/localhost:%s to tcp/localhost:%s" % (udp_listen_port,local_port)
		    print "Kill a process listening to port %s or change your configuration file's UDP settings, and rerun this program." % udp_listen_port
	    else:
		print "udp_listen_port:",udp_listen_port,"must be an int > 0. Not doing UDP packets conversion..."
		print "Another process (another socat?) is running and listening to the same port %s that we want. Kill that process or change your configuration file's UDP port settings and rerun this program." % udp_listen_port
		udpSuccess = False
    if success:
	successfullyMappedPorts[mapping_name] = mapping_descr_str if ((doUdp and udpSuccess) or not doUdp) else (mapping_descr_str.split('&')[0].strip()+ "\t<- Could not start UDP=>TCP converter daemon !")

def verbose(s):
    if g_verbose:
        print s

def freePort(port,tcpOrUdpStr="tcp"):
    groups = commands.getoutput("groups").strip().split()
    isroot = "root" in groups
    runasroot = lambda aCommandString : commands.getoutput(("sudo" if not isroot else "")+ " "+aCommandString).strip()
    print "trying to see if port-freeing is needed for %s/%s." % (port,tcpOrUdpStr)
    l = runasroot("fuser %s/%s" % (port,tcpOrUdpStr))
    if l: #if there was some user of the the port
	print l+". Port",port,"is in use. Trying to free it."
	l = runasroot("fuser -k %s/%s" % (port,tcpOrUdpStr))
	l = runasroot("fuser %s/%s" % (port,tcpOrUdpStr))
	if not l:
	    print "Occupying programm was killed."
	else:
	    print l,"Couldn't kill occupying program."
    else:
	print "Port %s/%s was free. Not freeing." % (port,tcpOrUdpStr)

def makeThreads(destination,portmappings,transportObject):
    global ENABLE_UNIX_PORTUSER_KILLING
    parameters = []
    if ENABLE_UNIX_PORTUSER_KILLING:
	print "ports freeing is enabled."
    for mappingName,mapping in zip(portmappings,portmappings.values()):
	if ENABLE_UNIX_PORTUSER_KILLING:
	    freePort(mapping["localport"])
	    if "udplocalport" in mapping:
		freePort(mapping["udplocalport"],"udp")
        parameters.append((mappingName,mapping["localport"],destination,mapping["destinationport"],transportObject)+ ((mapping["udplocalport"],) if "udplocalport" in mapping else ())) #adding fct paremeters to passed to forward_tunnel later in one shot
    #running all tunnels as threads in one shot
    for p in parameters:
	thread.start_new_thread(forward_tunnel,p) #returns a thread id or(?) handle but we don't care

    time.sleep(3)
    q = ""
    print '_________________________________________________________________'
    while q.strip() != "q":
	print "Ports tunneled and active are:"
	for l in successfullyMappedPorts.values(): print l
	q = raw_input("Press q to close all connections and kill this process:\n>") #daemon behaviour
    sys.exit(0)

def main():
    settings = getJSONSettings()
    gate,destination,portmappings = settings["gate"],settings["destination"],settings["portmappings"]

    #get username and password from user if not provided
    username = raw_input("Enter username for "+gate["hostname"]+":") if "username" not in gate else gate["username"]
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
	print "Maybe your either of the provided username or password is not correct?"
        sys.exit(1)

    #verbose('Now forwarding port %d to %s:%d ...' % (options.port, remote[0], remote[1]))
    verbose('Logged into %s:%d successfully.' % (gate["hostname"],gate["port"]))

    try:
	verbose('Will now try map ports from localhost through the latter server towards %s.' % (destination["hostname"],))
	makeThreads(destination["hostname"],portmappings,client.get_transport())
        #forward_tunnel(options.port, remote[0], remote[1], )
    except KeyboardInterrupt:
        print 'Control-C: Port forwarding stopped.'
        sys.exit(0)

def py25kill(popenObject):
    pid = popenObject.pid
    if isUnixPlatform():
	#unix only:
	
	os.kill(popenObject.pid,signal.SIGTERM)
	return pid
    else:
	try:
	    import win32api
	except:
	    print "don't know how to kill processes with python2.5 on windows without using win32api which you don't see to have installed. Take Python2.6+ !"
	    return False
	else:
	    win32api.TerminateProcess(pid,0)
	    return pid
	

def py26kill(popenObject):
    pid = popenObject.pid
    popenObject.terminate() # windows & unix
    return pid

def killSubProcesses():
    global socatProcesses
    print ("killing %s socat processes:" % len(socatProcesses)) if socatProcesses else "no children socat processes to kill."
    version = float(sys.version[:3])
    killFct = py25kill if version < 2.6 else py26kill
    for popenObject in socatProcesses:
	pid = killFct(popenObject)
	if pid:
	    print " - killed socat with pid: "+str(pid) if pid else " - couldn't kill one children socat instance due to python limitation on this platform."
    print "Done."

if __name__ == '__main__':
    import atexit
    atexit.register(killSubProcesses)
    main()
    