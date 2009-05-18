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

import logging
import pprint
import time

import comm

# set logging verbosity
# TODO: set it for the module only
logging.basicConfig(level=logging.INFO, format=comm.FORMAT)


class Client(comm.BasicHandler):
    """Our connection to a target server"""

    def __init__(self, addr_port):
        print "I'm a Client !"
        comm.BasicHandler.__init__(self)

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
    """A client inheriting from Client, and printing anything read"""

    def __init__(self, addr_port):
        Client.__init__(self, addr_port)
        self.stay_connected = True

    # we define the process method that handles incoming data (line by line).
    def process(self, line):
        print "received:",line
        return len(line)


class ClientFoo(Client):
    """Our connection to a target server, pong-aware and
     shutting down the server """

    def __init__(self, addr_port):
        print "I'm a ClientFoo, strongly connecting and aware of your pongZ !"

        comm.BasicHandler.__init__(self)
        # another way of defining the process method
        self.process = comm.process

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

    def handle_close(self):
        self.send_msg("shutdown")
        comm.BasicHandler.handle_close(self)

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
                   "echo" : EchoClient,
                   "pong_shut": ClientFoo,
                   "do_not": ClientR    # this is stupid to do, so don't do it!
                   }
HEARTBEATS = 2

if __name__ == '__main__':
    print "###"
    print "### available remotes: "+str(REMOTE_MODULES.keys())
    import sys
    print "### argv: "+str(sys.argv)

    remains, clients, server = comm.create(sys.argv, REMOTE_MODULES, Server)
    print ""

    print "### remaining args: "+str(remains)
    print "### clients: \t"+str(clients)
    print "### server: \t"+str(server)
    print ""

    if server and clients:
        print "unlimited loop started"
        # the function will return when no more sockets are open
        comm.loop()

    elif server:     # (you *should* have only one)
        import pdb
        pdb.set_trace()
        while server.is_readable:           # a server is not writable
            comm.loop(5, count=1)       # block for 500ms or new data event

    elif clients:
        for client in clients:
            if not hasattr(client, "received_pong"):
                continue
            # generate a bit of traffic
            hb = HEARTBEATS
            print "sending %i heartbeats" % hb
            while client.connected and not client.received_pong and hb:
                print client.__repr__(), "heartbeat test #", hb
                comm.loop(1, count=1)
                client.send_msg("ping")
                hb -= 1
                time.sleep(1)

    if [ c for c in clients if isinstance(c, EchoClient) ]:
        print "running loop for persistent clients"
        comm.loop()

    for c in clients:
        c.close()

    print "ok, we're done"
