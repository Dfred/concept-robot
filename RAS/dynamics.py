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
DYNAMICS MODULE

 This module controls the robot's motion/speed using bijective functions and
their derivative. Currently a single instance of the dynamics module exists
across the whole system as other modules simply access this module's . This
could be later changed if need.

 With this module, the HMS can update the dynamics of the robot in realtime,
without changing initial and target states.

 Updating the dynamics function is totally transparent for the RAS modules, but
there may be obvious visual side-effects if the functions are very different.
"""

import logging

from utils.comm import ASCIIRequestHandler
from utils.dynamics import Profile, ENTRIES

import RAS

__all__ = ['Dynamics']

LOG = logging.getLogger(__package__)
INSTANCE = None


class DynamicsError(StandardError):
  pass


class Dynamics_Server(object):
  """
  """
  def __init__(self):
    super(Dynamics_Server, self).__init__()
    self.callbacks = []
    self.profiles = None
    self.change_profile('smooth_step1')

  def get_profiles_expression(self):
    return self.profiles.fct_expr, self.profiles.drv_expr

  def register(self, function):
    """Registers a callback to be called upon profile changes.
    """
    self.callbacks.append(function)

  def unregister(self, fct):
    """Unregisters a profile-change callback.
    """
    try:
      self.callbacks.pop(self.callbacks.index(function))
    except (IndexError, ValueError):
      raise DynamicsError("callback not registered: %s", fct)

  def change_profile(self, profile):
    """
    """
    if profile not in ENTRIES.keys():
      LOG.warning("dynamic function '%s' doesn't exist", profile)
      return False
    self.profiles = ENTRIES[profile]
    for fct in self.callbacks:
      fct()


INSTANCE = Dynamics_Server()


class Dynamics_Handler(ASCIIRequestHandler):
  """
  """

  def setup(self):
    self.fifo = deque()

  def cmd_list(self, argline):
    """Reply with names of available dynamics.
    """
    self.send_msg(', '.join(ENTRIES.iterkeys()))

  def cmd_use(self, argline):
    """Set a specific function to be used.
    """
    if self.server.change_to(argline.strip()):
      LOG.debug("changed dynamics to '%s'", argline.strip())

