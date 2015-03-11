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

"""
comm package for python (versions >= 2.6)

Allows grouping servers in a single process.

TODO: complete doc
Overview:
* MetaServer
* MetaRequestHandler
"""

__author__    = "Frédéric Delaunay"
__license__   = "GPL"
__maintainer__= "Frédéric Delaunay"
__email__     = "delaunay.fr at gmail.com"
__credits__   = ["University of Plymouth and EPSRC"]

import types
import logging

from session import BaseServer, BaseRequestHandler

LOG = logging.getLogger(__package__)


class MetaRequestHandler(BaseRequestHandler):
  """Remote Client Handler.
  Represents a single remote client.
  """

  def __init__(self, server, sock, client_addr):
    super(MetaRequestHandler, self).__init__(server, sock, client_addr)
    self.curr_handler = None

  def create_subhandler(self, srv, subhandler_class):
    """Equivalent of create_subserver.
    Basically we emulate the basics of BaseRequestHandler
    """
    subhandler = subhandler_class(srv, self.socket, self.addr_port)
    subhandler.setup()
    return subhandler

  def set_current_subhandler(self, handler):
    self.curr_handler = handler

  def handle_notfound(self, cmd, argline):
    """Route cmd_ functions to the current handler.
    Return: result of current handler's function for cmd, otherwise None.
    """
    if not self.curr_handler:
      LOG.debug("unset current handler and no %s() in %s", cmd, self)
      return
    try:
      fct = getattr(self.curr_handler, cmd)
    except AttributeError:
      LOG.info("%s has no function '%s'", self.curr_handler, cmd)
    except :
      raise
    else:
      #
      #XXX: In the next call we're shifting from self to the current handler.
      # This is fine until the current handler needs to interfere with parsing
      # (eg. ASCIICommandProto.process allows to read ahead) as self and current
      # handler don't share state. So eventually this design need to be revised.
      #
      return fct(argline)

  def cmd_list(self, argline):
    """list all available commands"""
    cmds = []
    for obj in (self, self.curr_handler):
      cmds.append( [a[4:] for a in dir(obj) if a.startswith('cmd_')] )
    cmds[1] = filter(lambda x: x not in cmds[0], cmds[1])
    self.send_msg('commands:\t{0[0]}\nextra commands:\t{0[1]}'.format(cmds))

#XXX: useless now that handlers have a simple __init__(self).
#class MetaServerMixin(object):
#  """A mixin class to gathers other servers and their handlers.
#  Allows multiple protocols to be mixed together. Indeed you would need a
#   higher level protocol in order to switch from one sub-protocol to another.
#  """
#
#  def __init__(self):
#    self.servers_SHclasses = {}
#
#  def register(self, server, handler_class):
#    """Adds a server and its request handler class to the meta server .
#    On connection, self.clients adds an instance of request_handler_class .
#    """
#
#    #def meta_subhandler_init(self):
#    #  """Provides the handler with BaseComm.send_msg()"""
#    #  LOG.debug('initializing compound handler %s', self.__class__)
#    #  BaseComm.__init__(self)
#    #  handler_class.__init__(self)
#    #
#    #commHandler_class = type(handler_class.__name__+'BaseComm',
#    #                         (handler_class, BaseComm),
#    #                         {'__init__':meta_subhandler_init,'server':server} )
#    #self.servers_SHclasses[server] = commHandler_class
#    #return commHandler_class
#    self.servers_SHclasses[server] = handler_class
#    return handler_class
#
#  def unregister(self, server):
#    """Removes a registered server."""
#    try:
#      del self.servers_SHclasses[server]
#    except KeyError:
#      return False
#    return True
#
#  def create_subserver(self, server_class):
#    """Equivalent of create_server for a meta server. We need to respect
#    BaseServer's interface.
#    """
#    def meta_subserver_init(self):
#      LOG.debug('initializing compound server %s', self.__class__)
#      BaseServer.__init__(self)
#      server_class.__init__(self)
#
#    return type(server_class.__name__+'BaseServer',
#                (server_class, BaseServer),
#                {'__init__':meta_subserver_init} )()
