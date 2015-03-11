#!/usr/bin/python
# -*- coding: utf-8 -*-

################################################################################
# This software is provided for academic research only: it is OSS but not GPL!
# In such a case, you can redistribute this software and/or modify it,
# provided you do not modify this license. Any other use is not permitted.

# ARAS is the open source software (OSS) version of the basic component of
# LightHead's software suite. 

# ARAS stands for Abstract Robotic Animation System, and features actuator,
# sensor, animation and remote management high-level interfaces.
# In particular, ARAS helps animating a head (virtual or physical), provides
# supporting algorithms for vision and hearing, as well as contributions from
# other scholars.
# Copyright 2009 - Frédéric Delaunay: dr.frederic.delaunay@gmail.com

# This software is the low-level Human-Robot-Interaction part of the CONCEPT
# project, which took place at the University of Plymouth (UK).
# The project stemed from by Frédéric Delaunay's PhD, himself under the
# supervision of professor Tony Belpaeme. The PhD project started in late 2008
# and ended in late 2011 but this part of the software is still maintained.
# Visit http://www.tech.plym.ac.uk/SoCCE/CONCEPT/ for more information.

# This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  General Public License for more details.
################################################################################

  import sys
  import logging
  from threading import Thread

  from utils import LOGFORMATINFO
  from utils.comm import (ASCIICommandClient, ASCIIRequestHandlerCmds,
                          create_server)

  if len(sys.argv) < 2:
    print "usage: %s port" % sys.argv[0]
    print "If port is a number use tcp mode, if a path use udp."
    exit(1)
  addr_port = ['localhost',sys.argv[1]]
  if sys.argv[1].isdigit():
    addr_port[1] = int(addr_port[1])

  logging.basicConfig(level=logging.DEBUG,**LOGFORMATINFO)
  LOG = logging.getLogger()

  # Create a test thread that connects to the server.
  class TestClient(ASCIICommandClient):
    def handle_connect(self):
      LOG.info("%s connected", self.__class__.__name__)
      self.send_msg('ping my other args')
    def cmd_pong(self, args):
      LOG.info("sending shutdown")
      self.send_msg('shutdown')
      self.abort()

  class TestHandler(ASCIIRequestHandlerCmds):
    def cmd_ping(self, args):
      LOG.info("got ping '%s'", args)
      self.send_msg('pong')

  try:
    client = TestClient(addr_port)
    c = Thread(target=client.connect_and_run)
    LOG.info("created client thread for test")
    c.start()

    # Reminder for threading_info: server thread, clients threaded
    server = create_server(TestHandler, addr_port, threading_info=(False,False))
    server.start()
    if not server.is_threaded():     # threaded servers start serving in start()
      server.serve_forever()
  except KeyboardInterrupt:
    print "user abort!"
    server.shutdown()
  c.join()
  print "server and client exited."
