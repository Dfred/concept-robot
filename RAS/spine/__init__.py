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
import time
import math
import numpy

from utils import conf, get_logger
from utils.comm import ASCIIRequestHandler
from RAS.au_pool import AUPool
from RAS.dynamics import INSTANCE as DYNAMICS

import RAS

__all__ = [
  'SpineHW',
  'SpineError']

LOG = get_logger(__package__)


class SpineError(StandardError):
  pass


class Pose(dict):
  def __init__(self, map_or_iterable, pose_manager, check_SWlimits=True):
    """
    map_or_iterable: {AU:normalized_value,} or ((AU,nvalue),) defining the pose
    pose_manager: instance of PoseManager associated to that pose.
    """
    super(Pose,self).__init__(map_or_iterable)
    assert isinstance(self.keys()[0], basestring), "AUs must be strings"
    self.manager = pose_manager
    if check_SWlimits:
      for AU,nval in self.iteritems():
        if not pose_manager.is_inSWlimits(AU, nval):
          raise SpineError("AU %s: nvalue %s is off soft limits [%s]" % (
              AU, nval, pose_manager.infos[AU][-2:]))

  def to_raw(self, check_SWlimits=True):
    return self.manager.get_rawFromPose(self, check_SWlimits)


class PoseManager(object):
  """Represents a pose in normalized values."""

  def __init__(self, hardware_infos):
    """Initializes a PoseManager with hardware infos.

    hardware_infos: {AU_name : (
                        pi_factor,      # pi_factor * nval + offset = raw value 
                        offset,         # ready pose hardware value
                        HWmin, HWmax,   # RAW VALUES: foolproof for weird values
                        SWmin, SWmax    # normalized values
                                )}
    """
    self.infos = hardware_infos
    LOG.debug("Hardware infos:")
    for AU, infos in hardware_infos.iteritems():
      LOG.debug("AU %4s factor %8s offset %6s, Hard[%6s %6s] Soft[%+.5f %+.5f]",
                AU,*infos)
      rmin, rmax = [ self.get_rawFromNval(AU,i) for i in infos[4:6] ]
      if ( not self.is_inHWlimits(AU,rmin) or not self.is_inHWlimits(AU,rmax) ):
        raise SpineError("AU %s: Software %s %s out of Hardware %s."%
                         (AU, infos[4:6], (rmin, rmax), infos[2:4]))

  def get_poseFromPool(self, AUpool,
                       check_SWlimits=True, filter_fct=lambda x: True):
    """Returns a Pose instance from the AUpool target values.

    Raises SpineError if values lead to out-of-bounds hardware pose.
    """
    assert hasattr(AUpool,'__getitem__'), "argument isn't an AUpool."
    # normalized target value = base normalized value + normalized distance
    return Pose( [(AU,infs[0]+infs[1]) for AU,infs in AUpool.iteritems()
                  if filter_fct(infs)], self, check_SWlimits )

  def get_poseFromHardware(self, check_SWlimits=False):
    """Returns a pose from Hardware.
    """
    raise NotImplementedError("Override this function (assign or inherit).")

  def get_rawFromPose(self, pose, check_SWlimits=True):
    """Returns the pose converted in raw units: { AU : raw_value }

    Raises SpineError if check_SWlimits is True and value is off soft limits.
    """
    ret = {}
    for AU,norm_val in pose.iteritems():
      if check_SWlimits and not self.is_inSWlimits(AU, norm_val):
        raise SpineError("AU %s: nvalue %s is off soft limits" % (AU, norm_val))
      ret[AU] = self.infos[AU][0]*norm_val + self.infos[AU][1]
    return ret

  def get_rawFromNval(self, AU, norm_val):
    """Returns raw (hardware) value from normalized value."""
    return self.infos[AU][0]*norm_val + self.infos[AU][1]

  def is_inHWlimits(self, AU, rvalue):
    """rvalue: raw (hardware) value
    """
    LOG.debug("checking raw %s against %s", rvalue, self.infos[AU][2:4])
    return self.infos[AU][2] <= rvalue <= self.infos[AU][3]

  def is_inSWlimits(self, AU, nvalue):
    """nvalue: normalized value
    """
    return self.infos[AU][4] <= nvalue <= self.infos[AU][5]


class Spine_Handler(ASCIIRequestHandler):
  """
  """

  def setup(self):
    self.fifo = deque()

  def cmd_AU(self, argline):
    """Absolute rotations. arg: AU(name), target_value(rad), attack_duration(s).
    """
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
      self.fifo.append((au_name, value/math.pi, duration))
    else:
      LOG.warning("[AU] invalid AU (%s)", au_name)
      return

  def cmd_commit(self, argline):
    """Commit valid buffered updates"""
    try:
      self.server.set_targetTriplets(self.fifo.__copy__())      # thread safe
    except StandardError, e:                                    #TODO:SpineError
      LOG.warning("can't set pose %s (%s)", list(self.fifo), e)
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
    self._new_pt = None                                 # pose and triplets
    self.AUs = AUPool('spine', DYNAMICS, threaded=True)
    self.HWready  = None                                # Hardware action ready
    self.HWrest   = None                                # Hardware switch-off ok
    self.configure()
    self.pmanager = None                                # to be set by backend

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

  def set_lockHandler(self, handler):
    """function to call upon collision detection locking"""
    self._lock_handler = handler

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
      self.SW_limits = hardware['AXIS_LIMITS']          # may contain angles
    except:
      raise conf.LoadException("lib_spine['%s'] has no 'AXIS_LIMITS' key"%
                                self.hardware_name)
    try:
      self.HWrest = list(hardware['POSE_REST'])
      self.HWready = list(hardware['POSE_READY_NEUTRAL'])
    except:
      raise conf.LoadException("lib_spine['%s'] need 'POSE_REST' and "
                               "'POSE_READY_NEUTRAL'" % self.hardware_name)

  def is_moving(self):
    """Returns True if moving"""

  def unlock(self):
    """Unlock spine after collision detection cause locking"""
    raise NotImplementedError()

  def set_targetTriplets(self, triplets):
    """Sets the targets, waiting until the previous are processed by backend."""
    while self._new_pt != None:
      time.sleep(.05)
    AU_nval = [ (AU,nval) for AU,nval,att_dur in triplets if att_dur >= 0 ]
    # check attacks
    if len(AU_nval) != len(triplets):
      raise SpineError("attack duration can't be <= 0")
    # check values
    self._new_pt = Pose(AU_nval,self.pmanager) , triplets

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


def get_server_class():
  """Gets the server class (with backend implementation).
  """
  try:
    backend= __import__('RAS.spine.'+conf.ROBOT['mod_spine']['backend'],
                        fromlist=['RAS.spine'])
  except ImportError, e:
    LOG.error("\n*** SPINE INITIALIZATION ERROR *** (%s)", e)
    LOG.error('check in your config file for mod_spine "backend" entry.\n')
    from RAS.spine import katHD400s_6M as backend       #TODO: return None
  return backend.SpineHW


if __name__ == '__main__':
  """starts the arm in standalone server mode.
  """
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
  try:
    server.serve_forever()
  except KeyboardInterrupt:
    server.shutdown()
    server.stop_speedControl() # server.cleanUp()
  LOG.debug("Spine server done")
