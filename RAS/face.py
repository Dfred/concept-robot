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
FACE MODULE

This module handles generic motion of the facial features.
The backend should poll for the values and perform actuation.
"""

import sys
import time
import random
import collections
import logging

import numpy

from utils import conf
from utils.comm import ASCIIRequestHandler
from supported import *
from RAS.au_pool import AUPool
from RAS.dynamics import INSTANCE as DYNAMICS
import RAS

LOG = logging.getLogger(__package__)


#XXX: ideally, inherit from a class with support for cmd_AU and cmd_commit
class FaceHandlerMixin(ASCIIRequestHandler):
  """Remote connection handler: protocol parser.
  Must inherit from comm.ASCIIRequestHandler or derivate.
  """

  def setup(self, *args):
    pass

  def cmd_sample(self, argline):
    """Receive wav speech samples"""
    try:
      size = argline.split()[0]
    except ValueError as e:
      LOG.error("[AU] wrong number of arguments (%s)",e)
      return
    #XXX: we return the number of immediately following bytes to be ignored
    return int(size)                                        # design limitation

  def cmd_raw(self, argline):
    """Call functions of server object (e.g: low-level access to backend)."""
    args = [ arg.strip() for arg in argline.split() ]
    if args:
      if args[0] == 'dir':
        ret = " ".join([ a for a in dir(self.server) if a[0].islower() ])
      else:
        try:
          ret = eval("self.server."+args[0]+"".join(args[1:]))
        except StandardError as e:
          ret = e
      if ret:
        self.send_msg(str(ret))


class FaceServerMixin(object):
  """Main facial feature animation module
  To be mixed with classes ARASServer and comm.BaseServer or a derivate.
  
  Also maintains consistent muscle activation.
  AU value is normalized: 0 -> AU not streched, 1 -> stretched to max
  Setting an AU target value overwrites previous target.
  On target overwrite, interpolation starts from current value.
  """

  MIN_ATTACK_TIME = 0.001     # in seconds.

  def __init__(self):
    self.AUs = AUPool('face', DYNAMICS, threaded=True)
    if not DEFAULTS.has_key(self.name):
      raise conf.ConfigError("lib_spine lacks entry for '%s'" % self.name)
    self.SW_limits = DEFAULTS[self.name]['axis_limits']

  def commit_AUs(self, fifo):
    """Checks and commits AU updates."""
    for i,(AU, val, duration) in enumerate(fifo):
      if duration < self.MIN_ATTACK_TIME:
        LOG.warning("%s attack time (%s) too short, setting at %s.",
                    AU, duration, self.MIN_ATTACK_TIME)
        fifo[i][2] = self.MIN_ATTACK_TIME
    try:
      self.AUs.update_targets(fifo)
#      self.AUs.update_targets(fifo.__copy__())                # thread safe
    except StandardError as e:                                 #TODO: FaceError
      LOG.warning("can't set facial expression %s (%s)", list(fifo), e)


  def set_available_AUs(self, available_AUs, init_values=None):
    """Define list of AUs available for a specific face.

    available_AUs: list of str.
    init_values: list of floats, ordered similar to available_AUs.
    Returns: True if no error detected, False otherwise.
    """
    check = set(self.AUs).intersection(set(available_AUs))
    if check:
      LOG.error("AU(s) already registered: %s", check)
      return False
    self.AUs.set_availables(available_AUs, init_values)
    return True


if __name__ == '__main__':
  from utils import comm
  comm.set_debug_logging(len(sys.argv) > 1 and sys.argv[1] == '-d')
  try:
    missing = conf.load(name='lighty')
    if missing:
      raise UserWarning("config file lacks settings %s" % missing)
    server = comm.session.create_server(FaceHandlerMixin,
                                        conf.CONFIG['addrPort'],
                                        (False,False), FaceServerMixin)
  except UserWarning as err:
      LOG.error("FATAL ERROR: %s (%s)", sys.argv[0], err)
      exit(-1)
  server.set_available_AUs([1., 3., 12., 15.])                      # dummy AUs
  server.serve_forever()
  LOG.debug("Face server done")
