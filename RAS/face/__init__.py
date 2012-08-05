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

from utils import conf, get_logger
from utils.comm import ASCIIRequestHandler
from RAS.au_pool import AUPool
from RAS.dynamics import INSTANCE as DYNAMICS
from RAS.lightHead_server import VALID_AUS
import RAS

LOG = get_logger(__package__)


#XXX: ideally, inherit from a class with support for cmd_AU and cmd_commit
class Face_Handler(ASCIIRequestHandler):
  """Remote connection handler: protocol parser."""

  def setup(self, *args):
    pass

  def cmd_sample(self, argline):
    """Receive wav speech samples"""
    try:
      size = argline.split()[0]
    except ValueError, e:
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
        except StandardError, e:
          ret = e
      self.send_msg(str(ret))


class Face_Server(object):
  """Main facial feature animation module

  Also maintains consistent muscle activation.
  AU value is normalized: 0 -> AU not streched, 1 -> stretched to max
  Setting an AU target value overwrites previous target.
  On target overwrite, interpolation starts from current value.
  """

  MIN_ATTACK_TIME = 0.001     # in seconds.

  def __init__(self):
    #XXX: keep 'AUs' attribute name! see LightHeadHandler.__init__()
    self.AUs = AUPool('face', DYNAMICS, threaded=True)
    self.SW_limits = conf.lib_spine['blender']['AXIS_LIMITS']

  def commit_AUs(self, fifo):
    """Checks and commits AU updates."""
    for i,(AU, val, duration) in enumerate(fifo):
      if duration < self.MIN_ATTACK_TIME:
        LOG.warning("attack time (%s) too short, setting at %s.",
                    duration, self.MIN_ATTACK_TIME)
        fifo[i][2] = self.MIN_ATTACK_TIME
    try:
      self.AUs.update_targets(fifo)
#      self.AUs.update_targets(fifo.__copy__())                # thread safe
    except StandardError, e:                                    #TODO: FaceError
      LOG.warning("can't set facial expression %s (%s)", list(fifo), e)


  def set_available_AUs(self, available_AUs):
    """Define list of AUs available for a specific face.
    available_AUs: list of AUs (floats) OR list of tuples (AU, init_value)
    Returns: True if no error detected, False otherwise.
    """
    available_AUs.sort()
    if type(available_AUs[0]) == tuple:
      available_AUs, init_values = zip(*available_AUs)
    invalids = [ au for au in available_AUs if au not in VALID_AUS ]
    if invalids:
      LOG.error('invalid AU(s): %s' % ' '.join(invalids))
      return False
    self.AUs.set_availables(available_AUs, init_values)
    return True


def get_server_class():
  """Gets the server class (with backend implementation).
  """
  try:
    backend = __import__('RAS.face.'+conf.ROBOT['mod_face']['backend'],
                         fromlist=['RAS.face'])
  except ImportError, e:
    LOG.error("\n*** FACE INITIALIZATION ERROR *** (%s)", e)
    LOG.error('check in your config file for mod_face "backend" entry.')
    raise
  return backend.FaceHW


if __name__ == '__main__':
  from utils import comm
  comm.set_debug_logging(len(sys.argv) > 1 and sys.argv[1] == '-d')
  try:
    conf.load(name='lightHead')
    fconf = conf.ROBOT['mod_face']
    server = comm.session.create_server(Face_Handler, fconf['comm'],
                                        (False,False),Face_Server)
  except UserWarning, err:
      LOG.error("FATAL ERROR: %s (%s)", sys.argv[0], err)
      exit(-1)
  server.set_available_AUs([1., 3., 12., 15.])                      # dummy AUs
  server.serve_forever()
  LOG.debug("Face server done")
