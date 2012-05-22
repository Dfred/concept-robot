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
import RAS

LOG = get_logger(__package__)
VALID_AUS = ("01L","01R",                   # also easier to see (a)symetric AUs
             "02L","02R",
             "04L","04R",
             "05L","05R",
             "06L","06R",
             "07L","07R",
             "08L","08R",
             "09L","09R",
             "10L","10R",
             "11L","11R",
             "12L","12R",
             "13L","13R",
             "14L","14R",
             "15L","15R",
             "16L","16R",
             "17",
             "18L","18R",
             "20L","20R",
             "21L","21R",
             "22L","22R",
             "23L","23R",
             "24L","24R",
             "25","26","27",
             "28L","28R",
             "31",
             "32L","32R",
             "33L","33R",
             "38L","38R",
             "39L","39R",
             "51.5","53.5","55.5",              # Neck
             "61.5L","61.5R","63.5",            # Eyes orientation
             "6pd",                             # Pupil Dilatation
             "93X","93Y","93Z","93mZ","93bT",   # Tongue position
             "94","95",                         # Tongue shape
             "96","97","98",
             "SYL","SYR", "SZL","SZR",          # Shoulders
             "Th",
             "TX","TY","TZ",
             "Ebs","Esw",                       # Effects
             )


class Face_Handler(ASCIIRequestHandler):
  """Remote connection handler: protocol parser."""

  def setup(self, *args):
    self.fifo = collections.deque()

  def cmd_AU(self, argline):
    """if empty, returns current values. Otherwise, set them.
    argline: AU_name  target_value  duration.
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
    if duration < self.server.MIN_ATTACK_TIME:
      LOG.warning("attack time (%s) too short, setting at %s.",
                  duration, self.server.MIN_ATTACK_TIME)
      duration = self.server.MIN_ATTACK_TIME
    if self.server.AUs.has_key(au_name):
      self.fifo.append((au_name, value, duration))
    elif self.server.AUs.has_key(au_name+'R'):
      self.fifo.append((au_name+'R',value,duration))
      self.fifo.append((au_name+'L',value,duration))
    else:
      LOG.warning("[AU] invalid AU (%s)", au_name)
      return

  def cmd_commit(self, argline):
    """Commit buffered updates"""
    try:
      self.server.AUs.update_targets(self.fifo)
#      self.server.AUs.update_targets(self.fifo.__copy__())      # thread safe
    except StandardError, e:                                    #TODO: FaceError
      LOG.warning("can't set facial expression %s (%s)", list(self.fifo), e)
    self.fifo.clear()

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
    self.AUs = AUPool('face', DYNAMICS, threaded=True)
    self.SW_limits = conf.lib_spine['blender']['AXIS_LIMITS']

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
