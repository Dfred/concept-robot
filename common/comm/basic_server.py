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

"""
2 classes: server and client, with noticeable differences from asynchat:
 - if possible creates UNIX sockets (named pipe)
 - on EOT, clients are closed
 - command segmentation provided
 - filter out non-printable characters
 - interactivity with telnet client (support for backspace, + see TODO)
 - uses log module for debugging and stuff...

Other specifications:
 - commands are NOT echoed (windows users may not use HyperTerminal (tm)(c))
 - no thread
 - handle as much clients as possible
 - clients are expected to talk ASCII, processes commands after EOL is read.

 TODO: use readline to support history and such for more interaction.
 TODO: check support for UTF8 clients ? (I don't feel like it)
"""

import logging
import asyncore
import socket
import os, sys

LOG = logging.getLogger(__name__)

SOCKET_TYPE = socket.SOCK_STREAM
NAMED_PIPE_ADDRS = ["127.0.0.1", "localhost"]


def get_socket_family(addr_port):
    """Switch to Unix sockets if available (then issuing a new addr_port).
     addr_port: tuple (address of inet interface to use, port number).
    Returns: (socket_family , addr_port).
    """
    sock_family = (socket.AF_INET, "INET")
    if hasattr(socket, "AF_UNIX") and addr_port[0] in NAMED_PIPE_ADDRS:
        sock_family = (socket.AF_UNIX, "UNIX")
        addr_port = str(addr_port[1])
    return sock_family, addr_port


class BasicHandler(asyncore.dispatcher):
    """Represents a connection, either:
     - a remote client when instancied by BasicServer on new connection
     - a connection to a remote server when using connect_to()
    Incoming printable characters are buffered (as output)
    Commands are processed on detection of EOL
    EOL escaping support for multiline commands
    Backspace support (simple interactive session)
    """

    ACCEPTED_CHARS = range(32,127)+[9,10,13]
    READ_SIZE = 1024
    IBUFF_MAX_LEN = READ_SIZE * 4

    def __init__(self):
        """Create a connected client instance.
        To bind an existing socket, use asyncore interface,
         otherwise use connect_to() which uses TCP.
        """
        self.ibuffer    = ""
        self.obuffer    = ""
        self.EOL        = "\n"                  # override with set_eof
        self.id         = "?"

        # no socket is bound yet
        self.is_writable        = False
        self.is_readable        = False

        # asyncore.socket_map is updated there.
        asyncore.dispatcher.__init__(self)

    def readable(self):
        """Predicate for readability for asyncore.dispatcher"""
        overload = len(self.ibuffer) > self.IBUFF_MAX_LEN
        if overload:
            LOG.warning("%s> Input buffer hit max load, delaying read..",
                        self.id)
        return self.is_readable and not overload

    def writable(self):
        """Predicate for writability for asyncore.dispatcher"""
        return self.is_writable    # things to send are context dependant

    def handle_read(self):
        """Called on data reception. This server version expects ascii data."""

        try:
            data = self.recv(self.READ_SIZE)
        except socket.error, err:
            LOG.error("read failed: %s", err)
            return
            
        if not data:
            return 

        LOG.debug("%s> got %i byte(s): "+data.__repr__(), self.id, len(data))
        for char in data:
            val = ord(char)
            if val in self.ACCEPTED_CHARS:
                self.ibuffer += char;
            elif val == 4:         # End Of Transmission
                self.close()
            elif val in [8,127]:   # support for backspace
                self.ibuffer = self.ibuffer[:-1]
            else:                  # forget these chars
                LOG.debug("%s> skipping: unknown char: (%i or %s)",
                          self.id, val, char.__repr__())
                return
        self.ibuffer = self.ibuffer.replace('\r',self.EOL)
        self.ibuffer = self.ibuffer.replace(self.EOL*2,self.EOL)
        self.ibuffer = self.ibuffer.replace('\\'+self.EOL,'')
        read_bytes = 0
        for line in self.ibuffer.split(self.EOL)[:-1]:
            read_bytes += self.process(line)+1
#            LOG.debug("read %iB / %i", read_bytes, len(self.ibuffer))
        self.ibuffer = self.ibuffer[read_bytes:]
#        LOG.debug("%iB remaining: '%s'", len(self.ibuffer), self.ibuffer)

    def handle_write(self):
        """Manage output buffers to write to remote client"""
        if self.obuffer:
            sent = self.send(self.obuffer)
            if LOG.getEffectiveLevel() == logging.DEBUG: # be kind to logs ?
                msg = "%s> sent %iB: '%s'" % (self.id, sent, self.obuffer[:42])
                LOG.debug(sent < 42 and msg or msg+"...")
            self.obuffer = self.obuffer[sent:]
        if not self.obuffer:
            self.is_writable = False

    def handle_close(self):
        """Handle client disconnection"""
        LOG.info("%s> closing client connection", self.id)
        self.close()                # asyncore.socket_map is updated there.

    def handle_connect(self):
        """self.connected is always True here (also for disconnected socket)."""
        self.id = self._fileno
        LOG.debug("%s> handle_connect, connected: %s", self.id, self.connected)
        return self.addr is not None

    def connect_to(self, addr_port, timeout=0.0):
        """Try to connect to remote server.
         addr_port: tuple (address of inet interface to use, port number)
         timeout: see socket.settimeout. If set, call is blocking.
        """
        if self.socket and self.connected:
            raise UserWarning("Already connected!: "+ self.socket.__repr__())

        sock_family, addr_port = get_socket_family(addr_port)
        LOG.debug("connecting to AF=%s, %s", sock_family[1], addr_port)
        self.create_socket(sock_family[0], SOCKET_TYPE)
        if timeout:
            old_timeout = self.socket.gettimeout()
            self.socket.settimeout(timeout)
        try:
            self.connect(addr_port)
        except socket.error, err: # TODO: handle windows (WSAECONNREFUSED)
            LOG.warning("connection error to %s : %s", addr_port, err)
            self.del_channel()
            return False
        finally:
            if timeout: self.socket.settimeout(old_timeout)

        self.is_readable = True
        return True

    def send_msg(self, msg):
        """Handle client EndOfLine (TODO: check for unsupported terminals)"""
        if not self.connected:
            return False
        self.obuffer += msg+self.EOL;
        self.is_writable = True;

    def set_eol(self, eol):
        """Sets End Of Line. TODO: detect it automatically"""
        self.EOL = eol

    def process(self, line):
        """Child classes *shall* override this function.
         line: whole line command received from remote end.
        """
        LOG.debug("process() needs to be overrinden. "
                  "Consider using class comm.RemoteClient")
        return len(line)


#  The server class
class BasicServer(asyncore.dispatcher):
    """This class creates a TCPserver opening a single port."""

    MAX_QUEUED_CONNECTIONS = 5
    SERVER_ID = "server"

    def __init__(self, handlerClass=BasicHandler):
        """Create server and specify class to be spawn on accepted connection.
         handlerClass: called to spawn a dedicated client instance.
        """
        self.handlerClass       = handlerClass
        self.id                 = self.SERVER_ID
        self.is_readable        = False
        asyncore.dispatcher.__init__(self)

    def readable(self):
        return self.is_readable

    def writable(self):
        return False

    def listen_to(self, addr_port):
        """Open the port for incoming connections.
         addr_port: tuple (address of inet interface to use, port number).
        """
        socket_family, addr_port = get_socket_family(addr_port)
        self.create_socket(socket_family[0], SOCKET_TYPE)
        self.set_reuse_addr()
        
        LOG.debug("binding: AF=%s %s", socket_family[1], addr_port)
        if type(addr_port[1]) is type(""):
            if os.path.exists(addr_port[1]):
                LOG.warning("UNIX socket '%s' already present!", addr_port[1])
            if sys.platform.startswith('win32'):
                LOG.error("your OS (%s) has no support for UNIX socket. Check conf!"%sys.platform)
        try:
            self.bind(addr_port)        # sets self.addr
        except socket.error, err: # TODO: handle more errors
            # dirty raise not to confuse between create_socket, bind and listen
            raise UserWarning(err)

        self.listen(self.MAX_QUEUED_CONNECTIONS)
        self.is_readable = True
        LOG.info("server listening (max queued clients :%d)" %
                 self.MAX_QUEUED_CONNECTIONS)

    def shutdown(self, msg="server_shutdown"):
        """Disconnects all clients and terminates the server."""        
        clients = sorted(asyncore.socket_map.values())
        LOG.debug("server disconnecting %i clients", len(clients)-1)

        for client in clients:
            LOG.debug("%s> closing connection.", client.id)
            if hasattr(client, "send_msg"):
                client.send_msg(msg)
            client.is_readable = False
            client.close()

        if type(self.addr) == type(""):
            os.remove(self.addr)
        LOG.info("server shutdown complete")

    def handle_accept(self):
        """Handles incoming connections: creates an instance of the
         handler class (set at server creation) if verify_request returns True.
        """
        conn_sock, client_addr_port = self.accept()
        LOG.info("new connection from %s", client_addr_port or "local")
        if self.verify_request(conn_sock, client_addr_port):
            client = self.handlerClass()
            client.set_socket(conn_sock)
            client.addr = client_addr_port
            client.is_readable = True
            client.is_writable = True
            client.server = self
            LOG.debug("client socket set; waiting for events")

    def handle_close(self):
        """Called by asyncore on recv() failure, not by calling close() ?"""
        self.close()
        LOG.debug("%s> recv() failure ? => closed", self.id)

    def verify_request(self, conn_sock, client_addr_port):
        """TODO: Implements policy for incoming connections..."""
        LOG.info("For production use, remember to set a connexion policy for security reasons")
        return True

    def get_clients(self):
        """Return connected clients"""
        return (cl for cl in asyncore.socket_map.values() if 
                cl.id != self.SERVER_ID)
