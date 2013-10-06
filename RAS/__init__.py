#!/usr/bin/python
# -*- coding: utf-8 -*-

# ARAS is a programm part of CONCEPT, a HRI PhD project at the University
#  of Plymouth. ARAS is a Robotic Animation System including face, eyes,
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

"""Main package for Human-Robot Interaction subsystems of the lighty Robotic
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
print "Lighty's Abstract Robotic Animation System, python version:", sys.version_info

import tempfile, os
import logging

_TEMPPIDFILE = os.path.join(tempfile.gettempdir(), 'pid.ARAS')
_REQUIRED_CONF_ENTRIES = ('ARAS_server', 'ROBOT', 'lib_vision', 'lib_spine')

#LOG = logging.getLogger(__package__)                  # updated in initialize()
LOG = None


def initialize(thread_info, project_name):
  """Initialize the system.
  thread_info: tuple of booleans setting threaded_server and threaded_clients
  """
  # check configuration
  try:
    from utils import conf, LOGFORMATINFO, VFLAGS2LOGLVL
    conf.set_name(project_name)
    missing = conf.load(required_entries=_REQUIRED_CONF_ENTRIES)
    if missing:
      print '\nmissing configuration entries: %s' % missing
      sys.exit(1)
  except conf.LoadException, e:
    filename, errmsg = e
    print (filename and 'in file %s:'%filename or ""), errmsg
    sys.exit(2)
  if not hasattr(conf, 'VERBOSITY'):
    conf.VERBOSITY = 0
  print 'verbosity level is', conf.VERBOSITY
  logging.basicConfig(level=VFLAGS2LOGLVL[conf.VERBOSITY], **LOGFORMATINFO)
  LOG = logging.getLogger()

  # Initializes the system and do all critical imports now that conf is ok.
  from utils.comm import session
  from ARAS_server import ARASServer, ARASHandler
  server = session.create_server(ARASHandler, conf.ARAS_server,
                                 threading_info=thread_info,
                                 server_mixin=ARASServer)
  server.create_protocol_handlers()       # inits face and all other subservers.
  try:
    with file(_TEMPPIDFILE, 'w') as f:
      f.write(str(os.getpid()))
  except StandardError,e:
    LOG.error("Couldn't write PID file (%s), expect issues with the SDK.",e)
  return server

def cleanUp(server):
  """Cleans up and shuts down the system.
  thread_info: tuple of booleans setting threaded_server and threaded_clients
  """
  server.cleanUp()
  server.shutdown()
  try:
    os.remove(_TEMPPIDFILE)
  except StandardError,e:
    LOG.error("Couldn't remove PID file (%s), expect issues with the SDK.",e)
  print "LIGHTHEAD terminated"
