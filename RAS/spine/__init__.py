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

This module controls generic orientation/position of the robot torso and neck.
The backend (implemented in the module 'spine_backend') should inherit from
 SpineBase and implement the empty methods.

The API is limited to hardware implementation and indeed results are hardware-
 dependent. However as long as the hardware provides the required DOF and
 backend provides required functions, the end-result should be similar.
"""

#TODO: from abc import ABCMeta, abstractmethod

from utils import conf, get_logger
from utils.comm import ASCIIRequestHandler
import RAS

__all__ = [
  'SpineHW',
  'TorsoInfo',
  'NeckInfo',
  'SpineError']

conf.load()
LOG = get_logger(__package__, conf.DEBUG_MODE)            # assume valid config


class SpineError(StandardError):
  pass


class SpineElementInfo(object):
  """Capabilities and Information about an element of the spine"""

  def __init__(self):
    self.origin = [.0,]*3   # global coordinates of origin
    self.limits_rot = []    # min and max orientation values for each axis
    self.limits_pos = []    # min and max position values for each axis
    self.rot = [None,]*3
    self.pos = [None,]*3
class TorsoInfo(SpineElementInfo):
  pass
class NeckInfo(SpineElementInfo):
  pass


class Spine_Handler(ASCIIRequestHandler):
  """
  """

  def setup(self):
    self.xyz = [[.0, 0]] *3         # value , attack_time (TODO: torso)
    self.relative_rotators = { 'neck': self.server.rotate_neck,
                               'torso': self.server.rotate_torso }

  def cmd_switch(self, argline):
    args = argline.split()
    try:
      fct = getattr(self.server, 'switch_'+args[0])
    except AttributeError :
      LOG.debug('no switch_%s function available', args[0])
      return
    if len(args)>1:
      fct(int(args[1]))
    else:
      fct()

  # TODO: get rid of this and use a global AU pool
  def cmd_AU(self, argline):
    """Absolute rotation on 1 axis.
    Syntax is: AU_name, target_value, attack_time (in s.)"""
    args = argline.split()
    if len(args) != 3:
      LOG.warning('AU: expected 3 arguments (got %s)', args)
      return
    try:
      dim = ('53.5', '55.5', '51.5').index(args[0])
    except ValueError:
      LOG.warning('AU not known: %s', args[0])
      return
    self.xyz[dim] = [ float(v) for v in args[1:] ]

  def cmd_commit(self, argline):
    """from expr2"""
    self.server.animate(self.xyz, None)

  def cmd_rotate(self, argline):
    """relative rotation on 3 axis.
    Syntax is: neck|torso x y z [wait]"""
    if not argline:
      self.send_msg('rot_neck %s\nrot_torso %s' % (
                    SpineBase.round(self.server.get_neck_info().rot),
                    SpineBase.round(self.server.get_torso_info().rot) ) )
      return

    args = argline.split()
    if len(args) < 4:
      raise SpineError('rotate: 4 or 5 arguments required')
    wait = len(args) == 5 and args[4] == 'wait'
    xyz = [ round(float(arg),SpineBase.PRECISION) for arg in args[1:4] ]
    try:
      self.relative_rotators[args[0]](xyz, wait)
    except KeyError, e:
      raise SpineError("invalid body-part %s (%s)", args[0], e)

  def cmd_move(self, argline):
    """relative position on 3 axis"""
    if not argline:
#      self.send_msg('head_pos %s' % self.server.get_neck_info().pos)
      return
    args = [ float(arg) for arg in argline.split(',') ]
    self.server.set_neck_rot_pos(pos_xyz=tuple(args))


class SpineBase(object):
  """API for spine management (includes neck)."""

  PRECISION = 4       # number of digits for real part

  @staticmethod
  def round(iterable):
    """version for iterables, different signature from __builtins__.round"""
    return [ round(v, SpineBase.PRECISION) for v in iterable ]

  def __init__(self):
    """torso_info and neck_info are readonly properties"""
    self._torso_info = TorsoInfo()
    self._neck_info  = NeckInfo()
    self._speed = 0.0        # in radians/s
    self._accel = 0.0        # speed increment /s
    self._tolerance = 0.0    # in radians
    self._motors_on = False
    self._lock_handler = None
    self.FP = RAS.FeaturePool() # dict of { origin : numpy.array }

  # Note: property decorators are great but don't allow child class to define
  #       just the setter...

  def get_torso_info(self):
    """Returns TorsoInfo instance"""
    return self._torso_info

  def get_neck_info(self):
    """Returns NeckInfo instance"""
    return self._neck_info

  def get_tolerance(self):
    """In radians"""
    return self._tolerance

  def set_tolerance(self, value):
    """In radians"""
    self._tolerance = value

  def set_lock_handler(self, handler):
    """function to call upon collision detection locking"""
    self._lock_handler = handler

  def set_neck_orientation(self, axis3):
    """Absolute orientation:"""
    raise NotImplementedError()

  def set_torso_orientation(self, axis3):
    """Absolute orientation:"""
    raise NotImplementedError()

  def set_neck_rot_pos(self, axis3_rot=None, axis3_pos=None):
    """Set head orientation and optional position from neck reference point.
    axis3_rot: triplet of floats in radians
    axis3_pos: triplet of floats in meters
    """
    # to be overriden
    raise NotImplementedError()

  # TODO: poll AU values from the AU pool after each update
  def animate(self, neck_rot_attack, torso_rot_attack):
    """Set neck and torso's absolute orientation with timing information.
    neck_rot_attack:  X,Y,Z: (orientation_in_rads, attack_time_in_s)
    torso_rot_attack: X,Y,Z: (orientation_in_rads, attack_time_in_s)
    """
    # raise NotImplementedError()
    self.set_neck_orientation([ rad for rad, att in neck_rot_attack])

  def rotate_neck(self, xyz, wait=True):
    """Set neck's relative orientation."""
    ptp = self.get_neck_info().rot
    xyz_ = map(float.__add__, ptp, xyz)
    LOG.debug('neck %s + %s = %s', ptp, xyz, xyz_)
    self.set_neck_orientation(xyz_, wait)

  def rotate_torso(self, xyz, wait=True):
    """Set torso's relative orientation."""
    ptp = self.get_torso_info().rot
    xyz_ = map(float.__add__, ptp, xyz)
    LOG.debug('torso %s + %s = %s', ptp, xyz, xyz_)
    self.set_torso_orientation(xyz_, wait)

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


try:
  backend= __import__(conf.ROBOT['mod_spine']['backend'],fromlist=['RAS.spine'])
except ImportError, e:
  LOG.error("\n*** SPINE INITIALIZATION ERROR *** (%s)", e)
  LOG.error('check in your config file for mod_spine "backend" entry.')
  raise
Spine_Server = backend.SpineHW


if __name__ == '__main__':
  from utils import comm
  import sys
  try:
    comm.set_debug_logging(debug=True)
    server = comm.create_server(Spine_Server, Spine_Handler,
                                conf.mod_spine['conn'], (False,False))
  except (conf.LoadException, UserWarning), err:
    LOG.error("FATAL ERROR: %s (%s)", sys.argv[0], ':'.join(err))
    exit(-1)
  while server.running:
    try:
      server.serve_forever()
    except SpineError, e:
      print 'Error:', e
  LOG.debug("Spine server done")
