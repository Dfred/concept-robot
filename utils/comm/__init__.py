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

A template server and associated handler + client:
* Provides socket-based communication (with logging support) and a convenient
  way for handling word-based (text) application protocols.
* Auto-selects base class from address family, port type and thread settings
  so not to require inheritance and ease encapsulation; see create_server's
  doc for more details.

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

from session import BaseClient, BaseRequestHandler, create_server
from presentation import (ASCIICommandProto, ASCIICommandProtoEx,
                          RequestHandlerCmdsMixIn)

__all__ = [
  'BaseServer',
  'BaseRequestHandler',
  'BaseClient',
  'ASCIICommandClient',
  'AsciiRequestHandler',
  'AsciiRequestHandlerCmds',
  'create_server',
  'get_addrPort',
  'set_logging_level',
  ]

LOG = logging.getLogger(__package__)                      # main package logger


class ASCIICommandClient(BaseClient,
                         ASCIICommandProto):
  """
  """
  pass

class ScriptCommandClient(BaseClient,
                          ASCIICommandProtoEx):
  """
  """
  pass

class ASCIIRequestHandler(BaseRequestHandler,
                          ASCIICommandProto):
  """
  """
  pass

class ASCIIRequestHandlerCmds(BaseRequestHandler,
                              ASCIICommandProto,
                              RequestHandlerCmdsMixIn):
  """
  """
  pass


def get_addrPort(addrPort, default_addr='localhost'):
  """Parses a network identifier. Uses default_addr if only the port is provided

  >addrPort: "IP:port" or "Unix_pipe"
  >default_addr: "fqdn_or_IP_address"
  Raises: ValueError on bogus string.
  Returns: ('host_IP',host_port) or ('Unix_pipe')
  """
  if not (0 <= addrPort.count(':') <= 1):
    raise ValueError("bogus server identifier: '%s'" % addrPort)
  addrPort = addrPort.split(':')
  if addrPort[-1].isdigit():
    addrPort[-1] = int(addrPort[-1])
  else:
    return tuple(addrPort[-1])
  return len(addrPort)>1 and tuple(addrPort) or (default_addr,addrPort[0])

def set_debug_logging(debug=True):
  """Sets this package's logging level to debug (ie: from logging module).
  Convienience function.

  Returns: None
  """
  LOG.setLevel(debug and logging.DEBUG or logging.WARNING)
