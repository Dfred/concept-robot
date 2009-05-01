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
"""This is an almost full example of using the comm module.

Basically, all commands are asynchroneous (commands return before completion),
 so you'll rely on handle_ functions to be noticed of most events.

The communication protocol is ASCII based. The protocol parser relies on the
 presence of cmd_ functions in the (inherited) class.
"""

import asyncore
import time
import pprint

import comm 


class Client(comm.BasicHandler):
    """Our connection to a target server"""
    def __init__(self, addr_port):
        comm.BasicHandler.__init__(self)
        print "I'm a Client !"
        # we're asking for our client to connect to server, but we don't know
        # when this will happen, so rely on handle_connect to be noticed.
        self.connect_to(addr_port)

    def handle_connect(self):
        """Called when the client has just connected successfully"""
        if comm.BasicHandler.handle_connect(self):
            print self.__repr__(), "now connected to", self.addr
        else:
            print self.__repr__(), "failed to connect to", self.addr


class EchoClient(Client):
    def __init__(self, addr_port):
        Client.__init__(self, addr_port)
        self.stay_connected = True

    def process(self, line):
        print "received:",line
        return len(line)


class ClientFoo(Client):
    """Our connection to a target server, pong-aware"""
    def __init__(self, addr_port):
        comm.BasicHandler.__init__(self)
        print "I'm a ClientFoo, strongly connecting and aware of your pongZ !"
        self.received_pong = False
        # we want a synchronous connect without waiting more than 500ms,
        # timeout allows us to retry to connect in case of connection failure.
        for retry in xrange(3):
            if self.connect_to(addr_port, 0.5):
                break
            time.sleep(1)       # let some time to startup remote components

        # self.connected is reliable since connect_to() was synchronous
        if not self.connected:
            print "failed to connect. Aborting."
            self.close()
        self.send_msg("clients")

    def process(self, command):
        return comm.process(self, command)

    def cmd_pong(self, args):
        """On pong reception, we could update a counter.."""
        self.received_pong = True

    def cmd_connected_clients(self, args):
        """Answer for the 'clients' command is pretty-printed."""
        print args[0]+" connected client(s):"
        pprint.pprint(args.split('>')[1:])
        

class Server(comm.BasicServer):
    """The server itself, listening for incoming connections and spawning new
     instances of ClientR (argument to comm.BasicServer's constructor).
    """
    # Here we have to match comm.BasicServer constructor
    def __init__(self, addr_port):
        """Look, that's where you tell the server to spawn ClientR instances"""
        comm.BasicServer.__init__(self, ClientR)
        try:
            self.listen_to(addr_port)
        except UserWarning, err:        # ok ok it's slightly dirty
            print err
            exit(-1)            # because we consider serving is important

    def handle_accept(self):
        print "SERVER> a remote client is trying to connect to our server."
        comm.BasicServer.handle_accept(self)


class ClientR(comm.RemoteClient):
    """A remote client, spawn by server so already connected to our server. 
    Features support for cmd_ functions, interaction.. and ping!"""

    def handle_connect(self):
        print "I'm a new Remote client connected to our server ! \\o/"
        comm.RemoteClient.handle_connect(self)

    def cmd_hello(self, args):
        print "SERVER> a polite client !"
        self.send_msg("hello you...")

    def cmd_ping(self, args):
        """On ping reception, just reply politely"""
        self.send_msg("pong")


REMOTE_MODULES = { "c": Client,
                   "ce" : EchoClient,
                   "cfoo": ClientFoo,
                   "idiot": ClientR    # this is stupid to do, so don't do it!
          }
HEARTBEATS = 2

print ""
print "available remotes: "+str(REMOTE_MODULES.keys())
import sys
print "argv: "+str(sys.argv)

remains, clients, server = comm.create(sys.argv, REMOTE_MODULES, Server)
print ""

print "remaining args: "+str(remains)
print "clients: \t"+str(clients)
print "server: \t"+str(server)
print ""

if server and clients:
    print "unlimited loop started"
    # the function will return when no more sockets are open
    asyncore.loop()

elif server:     # (you *should* have only one)
    while server.is_readable or server.is_writable:
        asyncore.loop(0.5, count=1)   # wait 500ms or new data before returning

elif clients:
    print "sending heartbeats"
    for client in clients:
        if not hasattr(client, "received_pong"):
            print "not a heartbeat aware client ;)"
            continue
        # generate a bit of traffic
        hb = HEARTBEATS
        while client.connected and not client.received_pong and hb:
            print client.__repr__(), "heartbeat test #", HEARTBEATS
            asyncore.loop(1, count=1)
            client.send_msg("ping")
            hb -= 1
            time.sleep(1)

if [ c for c in clients if isinstance(c, EchoClient) ]:
    print "running loop for persistent clients"
    asyncore.loop()

print "ok, we're done"
