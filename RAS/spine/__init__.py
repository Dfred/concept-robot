#!/usr/bin/python
# -*- coding: utf-8 -*-

# LightHead programm is a HRI PhD project at the University of Plymouth,
#  a Robotic Animation System including face, eyes, head and other
#  supporting algorithms for vision and basic emotions.
# Copyright (C) 2010 Frederic Delaunay, frederic.delaunay@plymouth.ac.uk

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
SPINE MODULE

 This module controls the robot's skeleton. The backend (implemented in the
module 'spine_backend') should inherit from Spine_Server and implement the empty
methods.

 The API is limited to hardware implementation and indeed results are hardware-
dependent. However as long as the hardware provides the required DOF and
backend provides required functions, the end-result should be similar.
"""

#TODO: from abc import ABCMeta, abstractmethod
from collections import deque

import numpy

from utils import conf, get_logger
from utils.comm import ASCIIRequestHandler
from RAS.dynamics import INSTANCE as DYNAMICS

import RAS

__all__ = [
  'SpineHW',
  'SpineError']

LOG = get_logger(__package__)


class SpineError(StandardError):
  pass


class SpineElementInfo(object):
  """Information about a spine's element. An element is not a direct
  representation of the skeleton (eg: the thorax can be physically made of many
  sections).
  """
  def __init__(self):
    self.limits_rot = []                                # orientation
    self.limits_pos = []                                # position
    self.pivot_coords = [.0,]*3                         # in world coordinates


class Spine_Handler(ASCIIRequestHandler):
  """
  """

  def setup(self):
    self.fifo = deque()

  def cmd_AU(self, argline):
    """Absolute rotation on 1 axis.
    Syntax is: AU_name, target_value, attack_time (in s.)"""
    try:
      au_name, value, duration = argline.split()[:3]
    except ValueError:
      LOG.error("[AU] wrong number of arguments (%s)", argline)
      return
    try:
      value, duration = float(value), float(duration)
    except ValueError,e:
      LOG.error("[AU] invalid float (%s)", e)
      return
    if self.server.AUs.has_key(au_name):
      self.fifo.append((au_name, value, duration))
    else:
      LOG.warning("[AU] invalid AU (%s)", au_name)
      return

  def cmd_commit(self, argline):
    """Commit valid buffered updates"""
    try:
      self.server.get_pose(use=dict([(AU, nval) for AU,nval,dur in self.fifo]))
    except ValueError, e:
      LOG.warning("update out of boundaries: %s", e)
      return
    self.server.AUs.update_targets(self.fifo)
    self.fifo.clear()

  def cmd_switch(self, argline):
    """Special function for test purposes (not documented - non official).
    """
    args = argline.split()
    try:
      fct = getattr(self.server, 'switch_'+args[0])
    except AttributeError :
      LOG.debug('no switch_%s function available', args[0])
      return

#    #TODO: implement and use the 'with' statement for threaded servers
#    self.server.threaded and self.server.threadsafe_start()
#    try:
    if len(args)>1:
      fct(int(args[1]))
    else:
      fct()
#    except StandardError, e:
#      LOG.critical('Exception in thread-protected section: %s', e)
#    self.server.threaded and self.server.threadsage_stop()


class Spine_Server(object):
  """Skeleton animation module.
  """

  def __init__(self):
    super(Spine_Server, self).__init__()
    self._motors_on = False
    self._lock_handler = None
    self.AUs = RAS.AUPool('spine', DYNAMICS, threaded=True)
    self.poses = {}
    self.configure()

  def configure(self):
    """
    """
    spine_conf = conf.ROBOT['mod_spine']
    try:
      self.hardware_name = spine_conf['backend']
    except:
      raise conf.LoadException("mod_spine has no 'backend' key")
    try:
      self.KNI_address = spine_conf['hardware_addr']
    except:
      raise conf.LoadException("mod_spine has no 'hardware_addr' key")

    try:
      hardware = conf.lib_spine[self.hardware_name]
    except:
      raise conf.LoadException("missing['%s'] in lib_spine"% self.hardware_name)
    try:
      self.SW_limits = list(hardware['AXIS_LIMITS'])    # may contain angles
    except:
      raise conf.LoadException("lib_spine['%s'] has no 'AXIS_LIMITS' key"%
                                self.hardware_name)
    try:
      self.poses['rest'] = list(hardware['POSE_REST'])
      self.poses['ready'] = list(hardware['POSE_READY_NEUTRAL'])
    except:
      raise conf.LoadException("lib_spine['%s'] need 'POSE_REST' and "
                               "'POSE_READY_NEUTRAL'" % self.hardware_name)
    self.poses['SW_zero'] = [0]*len(self.SW_limits)
    self.poses['SW_avrg'] = [int((mn+mx)/2) for mn,mx in self.SW_limits]

  def is_moving(self):
    """Returns True if moving"""

  # Note: property decorators are great but don't allow child class to define
  #       just the setter...

  def get_tolerance(self):
    """In radians"""
    return self._tolerance

  def set_tolerance(self, value):
    """In radians"""
    self._tolerance = value

  def get_speedLimit(self):
    """In rad/s"""
    return self._speedLimit

  def set_speedLimit(self, value):
    """In rad/s"""
    self._speedLimit = value

  def set_lock_handler(self, handler):
    """function to call upon collision detection locking"""
    self._lock_handler = handler

  def reach_pose(self, pose):
    """
    """
    raise NotImplementedError()

  def switch_on(self):
    """Mandatory 1st call after hardware is switched on.
    Starts calibration if needed.
    """
    raise NotImplementedError()

  def switch_off(self):
    """Set the robot's pose for safe hardware switch off."""
    raise NotImplementedError()

  def unlock(self):
    """Unlock spine after collision detection cause locking"""
    raise NotImplementedError()


def get_server_class():
  """Gets the server class (with backend implementation).
  """
  try:
    backend= __import__('RAS.spine.'+conf.ROBOT['mod_spine']['backend'],
                        fromlist=['RAS.spine'])
  except ImportError, e:
    LOG.error("\n*** SPINE INITIALIZATION ERROR *** (%s)", e)
    LOG.error('check in your config file for mod_spine "backend" entry.\n')
    from RAS.spine import katHD400s_6M as backend
  return backend.SpineHW


if __name__ == '__main__':
  import logging
  from utils import comm, conf, LOGFORMATINFO
  logging.basicConfig(level=logging.DEBUG, **LOGFORMATINFO)
  conf.load(name='lightHead')
  try:
    LOG.info("initializing %s", get_server_class())
    server = comm.create_server(Spine_Handler, conf.ROBOT['mod_spine']['comm'],
                                (False,False), get_server_class())
  except (conf.LoadException, UserWarning), err:
    import sys
    LOG.fatal("%s (%s)", sys.argv[0], ':'.join(err))
    exit(1)
  except SpineError, e:
    LOG.fatal("%s", e)
    exit(2)
  print 'Initialization OK'
  server.serve_forever()
  LOG.debug("Spine server done")
