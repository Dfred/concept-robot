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

"""Main package for Human-Robot Interaction subsystems of the lightHead Robotic
Animation System.
"""

__version__ = "0.0.2"
__date__ = ""
__author__ = "Frédéric Delaunay"
__email__ = "frederic.delaunay@plymouth.ac.uk"
__copyright__ = "Copyright 2011, University of Plymouth"
__license__ = "GPL"
__credits__ = ["Joachim De Greeff"]
__maintainer__ = "Frédéric Delaunay"
__status__ = "Prototype" # , "Development" or "Production"

import sys
import logging

_REQUIRED_CONF_ENTRIES = ('lightHead_server','expression_server',
                          'ROBOT', 'lib_vision', 'lib_spine')

LOG = logging.getLogger(__package__)                  # updated in initialize()


def initialize(thread_info):
  """Initialize the system.
  thread_info: tuple of booleans setting threaded_server and threaded_clients
  """
  print "LIGHTHEAD Animation System, python version:", sys.version_info
  # check configuration
  try:
    from utils import conf, LOGFORMATINFO, VFLAGS2LOGLVL
    conf.set_name('lightHead')
    missing = conf.load(required_entries=_REQUIRED_CONF_ENTRIES)
    if missing:
      print '\nmissing configuration entries: %s' % missing
      sys.exit(1)
  except conf.LoadException, e:
    print 'in file {0[0]}: {0[1]}'.format(e)
    sys.exit(2)
  if not hasattr(conf, 'VERBOSITY'):
    conf.VERBOSITY = 0
  print 'verbosity level is', conf.VERBOSITY
  LOG.setLevel(VFLAGS2LOGLVL[conf.VERBOSITY])
  logging.basicConfig(level=VFLAGS2LOGLVL[conf.VERBOSITY], **LOGFORMATINFO)

  # Initializes the system and do all critical imports now that conf is ok.
  from utils.comm import session
  from lightHead_server import LightHeadServer, LightHeadHandler
  server = session.create_server(LightHeadHandler, conf.lightHead_server,
                                 threading_info=thread_info,
                                 server_mixin=LightHeadServer)
  server.create_protocol_handlers()       # inits face and all other subservers.
  return server

def cleanUp(server):
  """Cleans up and shuts down the system.
  thread_info: tuple of booleans setting threaded_server and threaded_clients
  """
  server.cleanUp()
  server.shutdown()
  print "LIGHTHEAD terminated"
