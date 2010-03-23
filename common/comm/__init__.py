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
import SocketServer
import socket
import select

# save users from importing socket
error = socket.error

# create our logging object and set log format
LOG = logging.getLogger("comm")
FORMAT = "%(filename)s[%(lineno)d] -%(levelname)s-\t%(message)s"

# Set basic config of logger for client modules not dealing with logging.
logging.basicConfig(format=FORMAT, level=logging.WARNING)


class NullHandler(logging.Handler):
    """A dummy Handler.
    Set package's logger handler with this class before importing this package,
     you can also set handlers per module.
    """
    def emit(self, record):
        pass

class CmdError(Exception):
    """Base Exception class for error in command processing.
    Failed commands shall raise Exceptions inherting from this class.
    """
    pass


# now our specifics
RE_NAME   = r'(?P<NAME>\w+)'
RE_IPADDR = r'(\d{1,3}\.){3}\d{1,3}'
RE_ADDR   = r'(?P<ADDR>'+RE_IPADDR+'|[\w-]+)'
RE_PORT   = r'(?P<PORT>\d{2,5}|[\w/\.]+[^/])'

# these are case insensitive
CRE_CMDLINE_ARG = re.compile('('+RE_NAME+'=)?'+RE_ADDR+':'+RE_PORT)
CRE_PROTOCOL_SYNTAX = re.compile("\s*\w+(\s+\w+)*")



def createBaseServer(addr_port, cnx_handler):
    """Creates the appropriate server (from SocketServer) according to addr_port"""

    addr, port = addr_port
    if type(port) == type(42):
        server_class = SocketServer.ThreadingTCPServer
    elif type(port) == type("") and addr in ["127.0.0.1", "localhost"]:
        if hasattr(SocketServer, "ThreadingUnixStreamServer"):
            server_class = SocketServer.ThreadingUnixStreamServer
        else:
            raise Exception("TODO: named pipes for windows")
    else:
        raise Exception("Could not get server type from addr_port info")
    return server_class(addr_port, cnx_handler)


#XXX: so far, creation from commandline is used only by comm_example
def create(cmdline, remoteClient_class, server_class, cnx_handler):
    """Parses cmdline and instanciates given classes.
    Note that any matching argument will be swallowed whether a successful
     instanciation has been made or not.

     cmdline: user command line checked for arguments
     remoteClient_class: { "module_name" : client_class, ... }
     server_class: last instance returned only (see _parse_args())
    Returns (unused arguments, [client_class objects], server_class object)
    """

    def parse_args(args):    
        """Parses arguments of the form: name=ip_address_or_fqdn:port
         'name' indentifies 'ip_address' as a remote server to connect to,
         if 'name=' is ommited 'ip_address' identifies a local interface used to
         listen to remote connections.

         args: an array of strings (as returned by sys.argv).
        Returns (unused arguments, [(name, addr, port), ...] )
        """
        unused, infos = [], []
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

    clients = []
    server = None
    unused, infos = parse_args(cmdline)
    for name, address, port in infos:
        if name == None:
            server = server_class((address, port), cnx_handler)
        else:
            try:
                clients.append(remoteClient_class[name]((address, port)))
            except KeyError:
                print "warning: found unmatched name '"+name+"' in cmdline"
    return (unused, clients, server)

        

class BaseComm:
    """Basic protocol handling and command-to-function resolver.
       Not to be instancied"""
    
    def handle_notfound(self, cmd):
        """When a method (a command) is not found in self. See process()."""
        pass

    def process(self, command):
        """Command dispatcher function common to client and handler."""
        """Tokenize command and calls 'cmd_ + 1st_token' function defined in self.
         Remaining tokens are given as argument in an array. self.handle_notfound is
         called if the built function name doesn't exist in self. Simultaneous
         commands (called within the same step) can be issued linking them with '&&'.

        command: string of text to be matched with CRE_PROTOCOL_SYNTAX
        Returns the number of bytes read.
        """
        length = len(command)
        LOG.debug("%s> command [%iB]: '%s'", self.cnx.fileno(), length, command)
        if not length or command.startswith('#'):
            return length

        for cmdline in command.split('&&'):
            if not CRE_PROTOCOL_SYNTAX.match(cmdline):
                LOG.info("%s> syntax error : '%s'", self.cnx.fileno(), cmdline)
                return length
            
        cmd_tokens = cmdline.split(None,1) # keep 1
        cmd, args = "cmd_"+cmd_tokens[0], cmd_tokens[1:]
        try:
            ret = None
            if cmd in dir(self):
                exec("ret = self."+cmd+"(args)")
            else:
                LOG.info("%s> command not found '%s'", self.cnx.fileno(), command)
                self.handle_notfound(cmd)
        except CmdError, e:
            LOG.warning("%s> unsuccessful command '%s' [%s]", self.cnx.fileno(), cmdline, e)
        return length

    def send_msg(self, msg):
        """Sends msg with a trailing \\n as required by the protocol."""
        LOG.debug("sending %s\n", msg)
        self.cnx.send(msg+'\n')

    def cmd_bye(self, args):
        """Disconnects that client."""
        self.running = False
    cmd_EOF = cmd_bye
        

class RequestHandler(BaseComm, SocketServer.StreamRequestHandler, object):
    """Instancied on successful connection to the server: a remote client."""
    """Adds support for general syntax checking, and default functions :
     cmd_shutdown, cmd_clients and cmd_verb.
    """
    def setup(self):
        super(RequestHandler,self).setup()
        if not hasattr(self.server, "clients"):
            self.server.clients = []
        self.server.clients.append(self)

    def finish(self):
        super(RequestHandler,self).setup()
        self.server.clients.remove(self)

    def handle(self):
        """entry point for processing client commands.
        self.rfile and self.wfile are streams and use standard file interface.
        read is buffered, write is not.
        """
        self.cnx = self.request # for process()
        LOG.info("%i> connection accepted from %s on "+str(self.client_address[1]),
                                        self.cnx.fileno(), self.client_address[0])
        self.running = True
        command = ""
        while self.running:
            try:
                command += self.rfile.readline().strip()
                LOG.debug("readline().strip(): [%i] %s", len(command), command)
            except socket.error, e:
                LOG.error(e)
                LOG.error("comm channel broken, pruning client %s", self.client_address[0])
                return
            if command.endswith('\\'):
                command = command[:-1]
            command = command[self.process(command):]
        LOG.info("%i> connection terminated : %s on "+str(self.client_address[1]),
                                         self.cnx.fileno(), self.client_address[0])

    def cmd_shutdown(self, args):
        """Disconnects all clients and terminate the server process"""
        if self.server == None:
            raise CmdError("cannot shutdown server")
        LOG.info("%s> stopping server", self.cnx.fileno())
        self.server.shutdown()
        self.running = False

    def cmd_clients(self, args):
        """Lists clients currently connected.
        We want other clients to be able to inquiry so server holds the info.
        """
        LOG.info("%s> listing %i clients.", self.cnx.fileno(), len(self.server.clients))
        clients_infos = []
        for cl in self.server.clients:
            clients_infos.append( type(cl.client_address) == type("") and
                                  (cl.cnx.fileno(), "UNIX", "localhost") or
                                  (cl.cnx.fileno(), cl.client_address[1],
                                                    cl.client_address[0]) )
        clients_infos.sort()
        obuffer = "clients : %i connected: (ID, PORT, ADDR)" % (len(clients_infos))
        for client_info in clients_infos:
            obuffer += "\\\n> %s:  %5s  %s" % client_info
        self.send_msg(obuffer)
        
    def cmd_verb(self, args):
        """Changes LOG verbosity level."""
        if not args:
            self.send_msg("CRITICAL 50\nERROR	 40\nWARNING  30\n"
                          "INFO     20\nDEBUG	 10\nNOTSET    0")
        else:
            LOG.warning("changing log level to %s", args[0])
            LOG.setLevel(args[0])
        self.send_msg("verb is %s now" % LOG.getEffectiveLevel())


class BaseClient(BaseComm):
    """Client creating a connection to a (remote) server.
       Remember it's impossible to use the file interface of the socket while
        setting a socket timeout.
    """
    def __init__(self, addr_port):
        self.target_addr = addr_port
        self.cnx = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False

    def set_timeout(self, timeout):
        self.cnx.settimeout(self.timeout)

    def connect_and_run(self):
        try:
            self.cnx.connect(self.target_addr)
        except socket.error, e:
            self.handle_error(e)
            self.cnx.close()
            return
        self.connected = True
        self.handle_connect()

        self.read_until_done()

        self.cnx.close()
        self.connected = False
        self.handle_disconnect()

    def read_until_done(self):
        """Wait, read and process data, calling self.handle_timeout when self.timeout elapsed."""

        def abort(self):
            LOG.debug("communication with server has been interrupted")
            self.running = False

        self.running = True
        line = ""
        while self.running:
            fd_sets = select.select([self.cnx], [], [], self.cnx.gettimeout())
            if not fd_sets[0]:
                self.handle_timeout()
            if fd_sets[2]:
                abort(self)
                self.handle_error()
            else:
                try:
                    buff = self.cnx.recv(1024)
                except socket.error, e:
                    self.handle_error(e)
                    return
                if not buff:
                    abort(self)
            line += buff
            line = line[self.process(line):]

    def handle_connect(self):
        pass

    def handle_error(self, e):
        raise e
        pass

    def handle_disconnect(self):
        pass

    def handle_notfound(self, cmd):
        pass
