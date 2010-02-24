#!/usr/bin/python

#
# Copyright 2008 Frederic Delaunay, f dot d at chx-labs dot org
#
#  This file is part of the comm module for the concept project: 
#   http://www.tech.plym.ac.uk/SoCCE/CONCEPT/
#
#  comm module is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  comm module is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
"""
comm package for python.
versions >= 2.5
Copyright (C) 2009 frederic DELAUNAY, University of Plymouth (UK).
"""
"""
A fully functional template server and associated client talking ASCII:
Provides async socket-based communication layer for modules + logging support.
Look at exemple.py for an overview.

recognized module communication arguments:
client mode: [module_id=ip_address:port]
server mode: [interface_address:port]
"""

__author__  = "frederic Delaunay f dot d at chx-labs dot org"
__status__  = "beta"
__version__ = "0.3"
__date__    = "$$"

import re
import os
import logging
import asyncore

# importing our modules. They look at logging basic configuration
from basic_server import BasicHandler, BasicServer


# deal with logging 1st
LOG = logging.getLogger("comm")
FORMAT = "%(filename)s[%(lineno)d] -%(levelname)s- %(message)s"

# Set basic config of logger for client modules not dealing with logging.
logging.basicConfig(level=logging.WARNING, format=FORMAT)



class NullHandler(logging.Handler):
    """A dummy Handler.
    Set package's logger handler with this class before importing this package,
     you can also set handlers per module.
    """
    def emit(self, record):
        pass



# now our specifics
RE_NAME   = r'(?P<NAME>\w+)'
RE_IPADDR = r'(\d{1,3}\.){3}\d{1,3}'
RE_ADDR   = r'(?P<ADDR>'+RE_IPADDR+'|[\w-]+)'
RE_PORT   = r'(?P<PORT>\d{2,5}|[\w/\.]+[^/])'

# these are case insensitive
CRE_CMDLINE_ARG = re.compile('('+RE_NAME+'=)?'+RE_ADDR+':'+RE_PORT)
CRE_PROTOCOL_SYNTAX = re.compile("\s*\w+(\s+\w+)*")

# just a way to get rid of the asyncore module.
loop = asyncore.loop


class CmdError(Exception):
    """Base Exception class for error in command processing.
    Failed commands shall raise Exceptions inherting from this class.
    """
    pass

def create(cmdline, remotes, server_class):
    """Parses cmdline and instanciates given classes.
    Note that any matching argument will be swallowed wether or not a
     successful instanciation has been made

     cmdline: user command line checked for arguments
     remotes: { "module_name" : client_class, ... }
     server_class: last instance returned only (see _parse_args())
    Returns (unused arguments, [client_class objects], server_class object)
    """
    clients = []
    server = None
    unused, infos = parse_args(cmdline)
    for name, address, port in infos:
        if name == None:
            server = server_class((address, port))
        else:
            try:
                clients.append(remotes[name]((address, port)))
            except KeyError:
                print "warning: found unmatched name '"+name+"' in cmdline"
    return (unused, clients, server)


def parse_args(args):    
    """Parses arguments of the form: name=ip_address_or_fqdn:port
     'name' indentifies 'ip_address' as a remote server to connect to,
     if 'name=' is ommited 'ip_address' identifies a local interface used to
     listen to remote connections.

     args: an array of strings (as returned by sys.argv).
    Returns (unused arguments, [(name, addr, port), ...] )
    """
    unused = []
    infos = []
    for arg in args:
        m = CRE_CMDLINE_ARG.match(arg)
        if m == None:
            unused.append(arg)
        else:
            port = m.group("PORT")
            if port.isdigit():
                port = int(port)
            infos.append((m.group("NAME"), m.group("ADDR"), port))
    return (unused, infos)
        

def process(self, command):
    """Main function: command dispatcher for incoming commands.
    If available, calls the cmd_ function defined in self according to command.
    Simultaneous commands (same step) can be linked with '&&'.

    command: string of text to be matched with CRE_PROTOCOL_SYNTAX
    Returns the number of bytes read.
    """
    length = len(command)
    command = command.strip()
    LOG.debug("%s> command (%iB): '%s'", self.id, len(command), command)
    if len(command) == 0 or command[0] == '#':
        return length
    
    for cmdline in command.split('&&'):
        if not CRE_PROTOCOL_SYNTAX.match(cmdline):
            LOG.info("%s> syntax error : '%s'", self.id, cmdline)
            return length
        
    cmd_tokens = cmdline.split(None,1) # keep 1
    cmd, args = ("cmd_"+cmd_tokens[0],
                 len(cmd_tokens)>1 and cmd_tokens[1] or "")
    try:
        ret = None
        if cmd in dir(self):
            exec("ret = self."+cmd+"(args)")
        else:
            LOG.info("%s> command not found '%s'", self.id, command)
    except CmdError, e:
        LOG.warning("%s> unsuccessful command '%s' [%s]", self.id, cmdline, e)
    return length


class RemoteClient(BasicHandler):
    """BasicHandler objects are instancied by BasicServer itself.
    Adds support for general syntax checking, cmd_ functions, 
     default cmd_clients and cmd_shutdown functions
    """

    def __init__(self):
        BasicHandler.__init__(self)

    def process(self, command):
        return process(self, command)
        
    def cmd_clients(self, args):
        """Lists clients currently connected"""
        LOG.debug("%s> listing %i clients", self.id, len(asyncore.socket_map)-1)
        clients_infos = []
        for cl in asyncore.socket_map.values():
            if not cl.connected:
                continue
            clients_infos.append( type(cl.addr) == type("") and
                                  (cl.id, "UNIX", "localhost") or
                                  (cl.id, cl.addr[1], cl.addr[0]) )
        clients_infos.sort()
        self.obuffer += "connected_clients %i: (ID, PORT, ADDR)" % (
            len(clients_infos))
        for client_info in clients_infos:
            self.obuffer += "\\\n> %s:  %5s  %s" % client_info
        self.send_msg("")
        
    def cmd_shutdown(self, args):
        """Disconnects all clients and terminate the server process"""
        if self.server == None:
            raise CmdError("cannot shutdown server")
        LOG.debug("%s> stopping server", self.id)
        self.server.shutdown("shutdown from server: disconnecting all clients")

