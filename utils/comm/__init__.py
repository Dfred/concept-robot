#!/usr/bin/python
# -*- coding: utf-8 -*-

# LightHead is a programm part of CONCEPT, a HRI PhD project at the University
#  of Plymouth. LightHead is a Robotic Animation System including face, eyes,
#   head and other supporting algorithms for vision and basic emotions.
# Copyright (C) 2010-2011 Frederic Delaunay, frederic.delaunay@plymouth.ac.uk

#  This program is free software: you can redistribute it and/or
#   modify it under the terms of the GNU General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.

#  This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   General Public License for more details.

#  You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""
comm package for python (versions >= 2.6)

A template server and associated handler + client:
Provides socket-based communication (with logging support) and a convenient
way for handling word-based (text) application protocols.
Auto-selection of base classes from address family, port type and threading
information doesn't require child classes to use inheritance; see doc of
create_server() for more details

Overview:
* session.py, holds server classes connecting processes,
* presentation.py, holds application protocol classes,
* meta_session.py, allows grouping servers in a single process,
* __init__.py, interesting classes and logging management function.

TODO: document all use-cases.
"""

__author__    = "Frédéric Delaunay"
__license__   = "GPL"
__version__   = "0.5b"
__status__    = "Prototype"
__date__      = "Thu. 17 Feb 2011"
__maintainer__= "Frédéric Delaunay"
__email__     = "delaunay.fr at gmail.com"
__credits__   = ["University of Plymouth and EPSRC"]

import logging

from session import BaseClient, BaseRequestHandler, ThreadingInfo, create_server
from presentation import ASCIICommandProto,RequestHandlerCmdsMixIn,ProtocolError

__all__ = ['create_server',
           'ThreadingInfo',
           'BaseServer',
           'BaseRequestHandler',
           'BaseClient',
           'ASCIICommandClient',
           'AsciiRequestHandler',
           'AsciiRequestHandlerCmds',
           'set_default_logging',
           'ProtocolError'
           'LOGFORMAT',
           ]

# let users set log format themselves (see set_default_logging)
LOGFORMAT="%(asctime)s %(filename).21s:%(lineno)-4d-%(levelname)s-\t%(message)s"
LOG = logging.getLogger(__package__)


class ASCIICommandClient(ASCIICommandProto,
                         BaseClient):
  """
  """
  pass

class ASCIIRequestHandler(ASCIICommandProto,
                          BaseRequestHandler):
  """
  """
  pass

class ASCIIRequestHandlerCmds(ASCIICommandProto,
                              BaseRequestHandler,
                              RequestHandlerCmdsMixIn):
  """
  """
  pass


# TODO: remove parameter and let us use __debug__ instead
def set_default_logging(debug=False):
  """This function does nothing if the root logger already has
  handlers configured.
  """
  log_lvl = (debug and logging.DEBUG or logging.INFO)
  logging.basicConfig(level=log_lvl, format=LOGFORMAT)
  LOG.setLevel(log_lvl)
  LOG.debug('Logger[%s] set log level to %s', LOG.name,
            debug and 'DEBUG' or 'INFO')


if __name__ == '__main__':
  import sys
  from threading import Thread

  if len(sys.argv) < 2:
    print "usage: %s port" % sys.argv[0]
    print "If port is a number use tcp mode, if a path use udp."
    exit(1)
  addr_port = ['localhost',sys.argv[1]]
  if sys.argv[1].isdigit():
    addr_port[1] = int(addr_port[1])

  # SERVER_HAS_OWN_THREAD, CLIENTS_HAVE_OWN_THREAD
  info = ThreadingInfo(False, False)
  set_default_logging(debug=False)#True)

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

    server = create_server(TestHandler, addr_port, threading_info=info)
    server.start()
    if not server.is_threaded():     # threaded servers start serving in start()
      server.serve_forever()
  except KeyboardInterrupt:
    print "user abort!"
    server.shutdown()
  c.join()
  print "server and client exited."
