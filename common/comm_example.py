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


class PrintClient(comm.BaseClient):
    """A client printing anything read."""
    """As process() is overriden, no cmd_ functions are defined here."""

    def __init__(self, addr_port):
        """This constructor exists just to show what's happening in runtime"""
        print "I'm connecting and printing out incoming server data!"
        comm.BaseClient.__init__(self, addr_port)

    # we define the process method that handles incoming data (line by line).
    def process(self, line):
        print "received:",line
        return len(line)

    # e is an exception (socket.error)
    def handle_error(self, e):
        print "ERROR", e


class ClientFoo(comm.BaseClient):
    """Our connection to a target server, pong-aware and
     shutting down the server """

    def __init__(self, addr_port):
        print "I'm connecting and aware of your pongZ !"
        comm.BaseClient.__init__(self, addr_port)

    def connect_and_run(self):
        """Connect to host and enter self loop."""
        """Function returns on disconnection."""
        try:
            comm.BaseClient.connect_and_run(self)
        except comm.error, e:
            print e

    def handle_connect(self):
        self.send_msg("hello")
        hb = 3
        print "sending %i heartbeats" % hb
        while hb:
            t = time.time()
            print client, "heartbeat test #", hb, t
            client.send_msg("ping %i" % t)
            hb -= 1
            time.sleep(1)
        self.send_msg("clients")
        print "sending shutdown"
        self.send_msg("shutdown")

    def handle_disconnected(self):
        """On disconnection, for clean-up purposes"""
        print "Oh! we've been disconnected :("

    def cmd_pong(self, args):
        """On pong reception, we could update a counter.."""
        print "PONG from server"

    def cmd_clients(self, args):
        """Answer for the 'clients' command is pretty-printed."""
        print args[0]+" connected client(s):"
        pprint.pprint(args.split('>')[1:])


class ClientR(comm.RequestHandler):
    """A remote client, spawn by server so already connected to our server. 
    Features support for cmd_ functions, interaction.. and ping!"""

    def __init__(self, cnx, client_addr, server):
        print "server accepted connection from %s (%s)" % client_addr
        comm.RequestHandler.__init__(self, cnx, client_addr, server)

    def cmd_hello(self, args):
        print "SERVER> a polite client !"
        self.send_msg("hello you...")

    def cmd_ping(self, args):
        """On ping reception, just reply politely"""
        print "SERVER> ping received", args
        self.send_msg("pong %i" % time.time())

class Server(object):
    """A dummy server. inheritance from object is mandatory"""
    pass


REMOTE_MODULES = { "bc": comm.BaseClient,
                   "print" : PrintClient,
                   "pong_shut": ClientFoo,
                   "do_not": ClientR    # this is stupid to do, so don't do it!
                   }

if __name__ == '__main__':
    import sys
    print "###"
    print "### available remotes: "+str(REMOTE_MODULES.keys())
    print "### argv: "+str(sys.argv)
    remains, clients, server = comm.create(sys.argv,
                                           REMOTE_MODULES,
                                           DummyServer,   # a server and
                                           ClientR)       # its handler
    print "### remaining args: "+str(remains)
    print "### clients: \t"+str(clients)
    print "### server: \t"+str(server)
    print ""

    if clients:
        import threading
        for client in clients:
            threading.Thread(target=client.connect_and_run).start()
    if server:     # (you *should* have only one)
        server.serve_forever()
