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
import time
import math
import numpy
import logging

from utils.conf import CONFIG, ConfigError
from utils.comm import ASCIIRequestHandler
from RAS.au_pool import AUPool
from RAS.dynamics import INSTANCE as DYNAMICS

import RAS

__all__ = [
  'SpineHW',
  'SpineError']

LOG = logging.getLogger(__package__)


class SpineError(StandardError):
  pass


class PoseManager(object):
  """Represents a pose in normalized values."""


  class Pose(dict):
    """Dictionnary of AU and associated normalized value."""
    def __init__(self, *args, **kwds):
      """A dict, but asserts keys are strings and values are floats."""
      super(PoseManager.Pose,self).__init__(*args, **kwds)
      assert isinstance(self.keys()[0], basestring), "AUs must be strings"
      assert isinstance(self.values()[0], float), "values must be floats"


  class Move(Pose):
    """Same as Pose but with duration information per axis."""
    def __init__(self, *args, **kwds):
      """Asserts each value is a 2-tuple of floats."""
      super(PoseManager.Pose,self).__init__(*args, **kwds)
      assert isinstance(self.values()[1], float), "duration must be a float"


  class AxisInfo():
    def __init__(self, act_id, smin, smax):
      self.axisID = act_id
      self.pif = None
      self.off = None
      self.softMin, self.softMax = smin, smax
      self.hardMin, self.hardMax = None, None


  def __init__(self, boundsNposes):
    """
    >boundsNposes: { AU_name : (
      act_ID,                           # (str) actuator identifier
      min_nor_value, max_nor_value,     # (float) soft bound normalized values
      HW_neutral,                       # (float) raw value for neutral pose
      HW_resting,                       # (float) raw value for resting pose
      ) }
    """
    self.infos = {}                             # { ID : AxisInfo object }
    self.ID2AU = {}
    self.poseN = None
    self.poseX = None
    self.__pX, self.__p0  = {}, {}

    infos_used = []
    for AU, infos in boundsNposes.iteritems():
      if infos[0] is None:
        LOG.warning("AU %s disabled (null actuator ID)", AU)
      else:
        infos_used.append((AU, infos))
    for AU,(ID,sm,sM,h0,hX) in infos_used:
      self.infos[AU] = self.AxisInfo(ID,sm,sM)
      self.ID2AU[ID] = AU
      self.__pX[AU], self.__p0[AU] = hX, h0

  def get_ID(self, AU):
    """Return: actuator ID from AU
    """
    return self.infos[AU].axisID

  def get_AU(self, ID):
    """Return: AU from actuator ID
    """
    return self.ID2AU[ID]

  def set_hardware_infos(self, hardware_infos):
    """
    >hardware_infos: { AU_name : (
      pi_factor,                        # pi_factor * nval + offset = raw value 
      offset,                           # ready pose hardware value
      hardW_Min, hardW_Max,             # RAW VALUES: foolproof checks.
      ) }
    """
    LOG.debug("Hardware infos:")
    for AU, (p_f, off, hMin, hMax) in hardware_infos.iteritems():
      infos = self.infos[AU]
      infos.pif, infos.off, infos.hardMin, infos.hardMax = p_f, off, hMin, hMax
      rmin = self.get_raw(AU, infos.softMin)
      rmax = self.get_raw(AU, infos.softMax)
      LOG.debug("AU %4s factor %8s offset %6s\n"
                "Hard[%6iraw<=>%+.5frad %6iraw<=>%+.5frad]\n"
                "Soft[%6iraw<=>%+.5frad %6iraw<=>%+.5frad]\n",
                AU, p_f, off,
                hMin, self.get_val(AU, hMin), hMax, self.get_val(AU, hMax),
                rmin, infos.softMin, rmax, infos.softMax)
      if ( not self.is_rvalWithinHWlimits(AU,rmin) or
           not self.is_rvalWithinHWlimits(AU,rmax) ):
        raise SpineError("AU %s: Software limits %s %s %s out of Hardware %s." %
                         (AU, infos.softMin, infos.softMax, (rmin, rmax),
                          (infos.hardMin, infos.hardMax)) )

    ## check poses are within boundaries
    for AU, h0 in self.__p0.items():
      if not self.is_rvalWithinHWlimits(AU, h0):
        raise ConfigError("Raw value %i out of bounds for Neutral pose (AU %s)"%
                          (h0, AU) )
    for AU, hX in self.__pX.items():
      if not self.is_rvalWithinHWlimits(AU, hX):
        LOG.warning("Raw value %i out of defined bounds for Rest pose (AU %s)",
                    hX, AU )
    self.poseN = self.Pose({ AU : self.get_val(AU,h0) for AU, h0 in
                             self.__p0.items() })
    self.poseX = self.Pose({ AU : self.get_val(AU,hX) for AU, hX in
                             self.__pX.items() })

  def get_raw(self, AU, norm_val):
    """Returns raw (hardware) value from normalized value."""
    return self.infos[AU].pif * norm_val + self.infos[AU].off

  def get_val(self, AU, raw_val):
    """Returns normalized value from raw (hardware) value."""
    return (raw_val - self.infos[AU].off) / self.infos[AU].pif

  def get_poseFromNval(self, map_or_iterable, check_SWlimits=True):
    """Create a pose from a mapping of AUs and normalized values.
    >map_or_iterable: {AU:normalized_value,} or ((AU,nvalue),) defining the pose
    >check_SWlimits: boolean, if True checks each axis'value is within
                     software-defined limits.
    Return: Pose instance
    """
    pose = self.Pose(map_or_iterable)
    if check_SWlimits:
      for AU, nval in pose.iteritems():
        self.is_nvalWithinSWlimits(AU, nval, _raise=True)
    return pose

  def get_poseFromPool(self, AUpool,
                       check_SWlimits=True, filter_fct=lambda x: True):
    """Create a pose from the AUpool target values.
    >AUpool: the AUpool to read AUs from.
    >check_SWlimits: boolean, if True checks each axis'value is within
                     software-defined limits.
    >filter_fct: function() -> boolean
    Raise: SpineError if values lead to out-of-bounds hardware pose.
    Return: Pose instance
    """
    assert hasattr(AUpool,'__getitem__'), "argument isn't an AUpool."
    # normalized target value = base normalized value + normalized distance
    return self.Pose( [(AU,infs[0]+infs[1]) for AU,infs in AUpool.iteritems()
                       if filter_fct(infs)], self, check_SWlimits )

  def get_poseFromHardware(self, check_SWlimits=False):
    """Returns a pose from Hardware.
    """
    raise NotImplementedError("Override this function (assign or inherit).")

  def get_rawFromPose(self, pose, check_SWlimits=True):
    """Returns the pose converted in raw units: { axisID : raw_value }

    Raises SpineError if check_SWlimits is True and value is off soft limits.
    """
    ret = { self.infos[AU].axisID : self.get_raw(AU,norm_val) for AU,norm_val in
            pose.iteritems() }
    if check_SWlimits:
      for AU, norm_val in pose.iteritems():
        self.is_nvalWithinSWlimits(AU, norm_val, _raise=True)
    return ret

  def get_rawNeutralPose(self):
    """
    Return: { axis_id : raw_val }
    """
    return { self.get_ID(AU) : raw for AU, raw in self.__p0.items() }

  def get_rawRestingPose(self):
    """
    Return: { axis_id : raw_val }
    """
    return { self.get_ID(AU) : raw for AU, raw in self.__pX.items() }

  def is_rvalWithinHWlimits(self, AU, rvalue, _raise=False):
    """rvalue: raw (hardware) value
    """
    LOG.debug("checking raw %s against %s", rvalue, (self.infos[AU].hardMin,
                                                     self.infos[AU].hardMax))
    test = self.infos[AU].hardMin <= rvalue <= self.infos[AU].hardMax
    if not test and _raise:
      raise SpineError("AU %s: raw value %s is off hard limits %s" %
                       (AU, rvalue, [self.infos[AU].hardMin,
                                    self.infos[AU].hardMax ] ) )
    return test

  def is_nvalWithinSWlimits(self, AU, nvalue, _raise=False):
    """nvalue: normalized value
    """
    test = self.infos[AU].softMin <= nvalue <= self.infos[AU].softMax
    if not test and _raise:
      raise SpineError("AU %s: normalized value %s is off soft limits %s" %
                       (AU, nvalue, [self.infos[AU].softMin,
                                    self.infos[AU].softMax ] ) )
    return test


class SpineHandlerMixin(ASCIIRequestHandler):
  """Implements additional commands. 
  Must inherit from comm.ASCIIRequestHandler or derivate.
  """

  def setup(self):
    pass

  def cmd_switch(self, argline):
    """Special function for test purposes (not documented - non official).
    """
    args = argline.split()
    try:
      fct = getattr(self.server, 'switch_'+args[0])
    except AttributeError:
      LOG.debug('no switch_%s function available', args[0])
      return
#    #TODO: implement and use the 'with' statement for threaded servers
#    self.server.threaded and self.server.threadsafe_start()
#    try:
    if len(args)>1:
      fct(int(args[1]))
    else:
      fct()
#    except StandardError as e:
#      LOG.critical('Exception in thread-protected section: %s', e)
#    self.server.threaded and self.server.threadsage_stop()


class SpineServerMixin(object):
  """Skeleton animation.
  To be mixed with classes ARASServer and comm.BaseServer or a derivate.
  """

  def __init__(self):
    self._motors_on = False
    self._lock_handler = None
    self._new_pt = None                         ## PoseManager.Move()
    self.pmanager = None                        ## _configure + backend update
    try:
      self.conf = CONFIG[self.name+"_HW_setup"]
      self._configure()
    except KeyError as e:
      raise ConfigError("Entry for %s backend: %s required." % (self.name, e))
    #XXX: keep 'AUs' attribute name! see LightHeadHandler.__init__()
    self.AUs = AUPool('spine', DYNAMICS, threaded=True)

  def _configure(self):
    """Load configuration settings all backends should need.

    The conf section relative to hardware shall be copied from the
    hardware library so that the local config can be modified at will.
    Return: None
    """
    self.pmanager = PoseManager(dict(
        zip(self.conf["AU"],
            zip(self.conf["ID"],
                [ float(HWval) for HWval in self.conf["Smin"] ],
                [ float(HWval) for HWval in self.conf["Smax"] ],
                [ float(HWval) for HWval in self.conf["pos0"] ],
                [ float(HWval) for HWval in self.conf["posX"] ] ) ) ))

  def commit_AUs(self, fifo):
    """Checks and commits AU updates."""
    try:
      self.set_targetTriplets(fifo.__copy__())                  # thread safe
    except (StandardError, SpineError) as e:
      LOG.warning("can't set triplet %s (%s)", list(fifo), e)

  # Note: property decorators are great but don't allow child class to define
  #       just the setter easily...

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

  def is_moving(self):
    """Returns True if moving"""
    raise NotImplementedError()

  def unlock(self):
    """Unlock spine after collision detection cause locking"""
    raise NotImplementedError()

  def set_targetTriplets(self, triplets, wait=False):
    """Sets the targets (a Move), the backend shall override this function.
    >triplets: iterable of triplet, i.e: ( (AU, target_nval, duration), ... )
    >wait: boolean, if True: wait for previous pose to be reached.
    Return: None
    """
    if wait:
      while self._new_pt != None:
        time.sleep(.05)
    AU__nval__dur = [(AU,(nval,att_d)) for AU,nval,att_d in triplets if
                     att_d > 0]
    # check attacks
    if len(AU__nval__dur) != len(triplets):
      raise SpineError("attack duration can't be <= 0")
    # check values
    self._new_pt = self.pmanager.Move(AU__nval__dur)

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
  except (conf.LoadingError, UserWarning) as err:
    import sys
    LOG.fatal("%s (%s)", sys.argv[0], ':'.join(err))
    exit(1)
  except SpineError as e:
    LOG.fatal("%s", e)
    exit(2)
  print 'Initialization OK'
  try:
    server.serve_forever()
  except KeyboardInterrupt:
    server.shutdown()
    server.stop_speedControl() # server.cleanUp()
  LOG.debug("Spine server done")
