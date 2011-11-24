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
"""

__author__ = "Frédéric Delaunay"
__copyright__ = "Copyright 2011, University of Plymouth, lightHead system"
__credits__ = [""]
__license__ = "GPL"
__version__ = "0.0.1"
__maintainer__ = "Frédéric Delaunay"
__email__ = "frederic.delaunay@plymouth.ac.uk"
__status__ = "Prototype" # , "Development" or "Production"

import time

from utils import conf, handle_exception
from utils.FSMs import SMFSM
from HMS.communication import ThreadedExpressionComm


def fatal(msg):
  print msg
  exit(1)


class Behaviour_Builder():
  """A generic framework for specifying behaviour through SMFSM objects.
  """

  def __init__(self, machine_defs, with_vision=True):
    """
    """
    try:
      conf.set_name('lightHead')
      missing = conf.load(required_entries=('ROBOT','expression_server'))
      if missing:
        print '\nmissing configuration entries: %s' % missing
        sys.exit(1)
    except conf.LoadException, e:
      print 'in file {0[0]}: {0[1]}'.format(e)
      sys.exit(2)

    # now that we're sure conf is ok, import other modules
    if with_vision:
      from RAS import vision

    for name, rules, parent_name in machine_defs:
      try:
        parent= parent_name and getattr(self,'fsm_'+parent_name) or None
      except AttributeError:
        raise ValueError("machine %s: parent machine '%s' not found,"
                         " check SMFSM definition." % (name, parent_name))
      fsm = SMFSM(name, rules, parent)
      setattr(self, 'fsm_'+fsm.name, fsm)
      if not hasattr(self, 'root_fsm'):
        self.root_fsm = fsm

    if with_vision:
      try:
        self.vision = vision.CamFaceFinder()
        self.vision.use_camera(conf.ROBOT['mod_vision']['camera'])
        #XXX: put that to conf for vision to read
        self.vision_frame = self.vision.camera.get_tolerance_frame(.1)  # 10%
        self.vision.gui_create()
        self.vision.update()
      except vision.VisionException, e:
        fatal(e)
    self.comm_expr = ThreadedExpressionComm(conf.expression_server, connection_succeded_function=self.connected)
    
    
  def connected(self):
    self.connected = True

  def cleanup(self):
    """
    """
    if hasattr(self,'vision'):
      self.vision.gui_destroy()
    self.comm_expr.done()

  def step_callback(self, machines):
    """Will die on disconnection with expression, also updates webcam.
    Return: None
    """
    if hasattr(self,'vision'):
      self.vision.update()
      self.vision.gui_show()
    if not self.comm_expr.connected:
      self.root_fsm.abort()

  def run(self):
    """
    """
    try:
      while not self.comm_expr.connected:
        time.sleep(1)
      self.root_fsm.run(self.step_callback)
    except KeyboardInterrupt:
      print 'aborting'
      self.root_fsm.abort()
    except StandardError, e:
      handle_exception(None)

if __name__ == '__main__':
  import sys
  print 'python path:', sys.path

  class TestBehaviour_Builder(Behaviour_Builder):
    """
    """
    def started(self):
      print 'test started'
      return 'TESTING'
    def testing(self):
      faces = self.vision.find_faces()
      if self.vision.gui:
        self.vision.mark_rects(faces)
        self.vision.gui.show_frame(self.vision.frame)
      return faces and SMFSM.STOPPED or None
    def stopped(self):
      print 'test stopped'
      return
    def __init__(self):
      rules = (
          (SMFSM.STARTED,self.started),
          ('TESTING',  self.testing),
          (SMFSM.STOPPED,self.stopped) )
      machine_def = [ ('test', rules, None) ]
      Behaviour_Builder.__init__(self, machine_def)

  player = TestBehaviour_Builder()
  player.run()
  player.cleanup()
