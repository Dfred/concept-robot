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
    print "ERROR: unable to load any of these files: ", conf.build_candidates()
    print "ERROR:", e
    return False
  if missing:
    print "ERROR: %s lacks required entries:" % conf.get_loaded(), missing
    return None
  if hasattr(conf.CONFIG["addrPort"][1],'lower'):
    conf.CONFIG["addrPort"][1] = int(conf.CONFIG["addrPort"][1])
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
  LOG.info("--- server started %s ---", conf.CONFIG["addrPort"])
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
