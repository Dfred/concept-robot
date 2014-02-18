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
print "*** Lighty's ARAS python is:", \
  filter(lambda x: x not in "\r\n", sys.version)

import tempfile, os
import logging

from utils.comm import get_addrPort
from utils import (conf, LOGFORMATINFO, VFLAGS2LOGLVL, LOGLVL2VFLAGS,
                   EXIT_DEPEND, EXIT_CONFIG)

_TEMPPIDFILE = os.path.join(tempfile.gettempdir(), 'pid.ARAS')

REQUIRED_CONF_ENTRIES = ('addrPort', 'backends', 'verbosity',
                         ) #'lib_vision', 'lib_spine'

LOG = None

def loadnCheck_configuration(project_name):
  """Check configuration and print error messages.
  >project_name: "project_identifier"
  Return: False => config file found; None => wrong config file; True => OK
  """
  try:
    missing = conf.load(name=project_name,
                        required_entries=REQUIRED_CONF_ENTRIES)
  except conf.LoadingError as e:
    print "ERROR: unable to find any of these files: ", conf.build_candidates()
    print "ERROR:", e
    return False
  if missing:
    print "ERROR: %s lacks required entries:" % conf.get_loaded(), missing
    return None
  return True

def initialize(thread_info, project_name):
  """Initialize the system.
  thread_info: tuple of booleans setting threaded_server and threaded_clients
  """
  if not conf.get_loaded() and not loadnCheck_configuration(project_name):
    sys.exit(EXIT_CONFIG)
  if not conf.CONFIG.has_key("verbosity"):
    conf.CONFIG["verbosity"] = 0
  try:
    logging.basicConfig(level=VFLAGS2LOGLVL[conf.CONFIG["verbosity"]],
                        **LOGFORMATINFO)
  except KeyError as e:
    print "ERROR: bad verbosity '%s'" % conf.CONFIG["verbosity"]
    sys.exit(EXIT_CONFIG)
  LOG = logging.getLogger(__package__)
  LOG.info("ARAS verbosity level is now %s", 
           LOGLVL2VFLAGS[LOG.getEffectiveLevel()])

  # Initializes the system and do all critical imports now that conf is ok.
  from utils.comm import session
  from ARAS_server import ARASServer, ARASHandler
#  import pdb; pdb.set_trace()
  server = session.create_server(ARASHandler, 
                                 conf.CONFIG["addrPort"],
                                 threading_info=thread_info,
                                 server_mixin=ARASServer)
  server.create_protocol_handlers()       # inits face and all other subservers.
  try:
    with file(_TEMPPIDFILE, 'w') as f:
      f.write(str(os.getpid()))
  except StandardError as e:
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
  except StandardError as e:
    LOG.error("Couldn't remove PID file (%s), expect issues with the SDK.",e)
  print "LIGHTHEAD terminated"
