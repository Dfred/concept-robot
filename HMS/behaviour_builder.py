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

import logging
import time

from HMS.communication import MTExpressionComm
from utils import conf, handle_exception
from utils.parallel_fsm import SPFSM, STARTED, STOPPED


LOG = logging.getLogger(__package__)


def fatal(msg):
  print 'fatal:',msg
  exit(1)


class BehaviourBuilder(object):
  """A generic framework for specifying behaviour through FSM objects.
  """

  def __init__(self, machine_defs, fsm_class=SPFSM):
    """machine_defs: iterable of (name, FSM rules, parent machine)
    fsm_class: allows you to change from SPFSM to any of its derivate, e.g:MPFSM.
    """
    missing = conf.load(required_entries=('ROBOT','expression_server'))
    if missing:
      LOG.warning('\nmissing configuration entries: %s', missing)
      sys.exit(1)

    assert len(machine_defs[0]) == 3, "bad machine(s) definition"
    for name, rules, parent_name in machine_defs:
      try:
        parent = parent_name and getattr(self,'fsm_'+parent_name) or None
      except AttributeError:
        raise ValueError("machine %s: parent machine '%s' not found,"
                         " check machine definition." % (name, parent_name))
      fsm = fsm_class(name, rules, parent)
      setattr(self, 'fsm_'+fsm.name, fsm)
      if not hasattr(self, 'root_fsm'):
        self.root_fsm = fsm
    self.comm_expr = MTExpressionComm(conf.expression_server,
                                      connection_succeded_fct=self.connected)
    
  def connected(self):
    LOG.debug('connected')

  def cleanUp(self):
    self.comm_expr.done()

  def step_callback(self):
    """Stops the machines upon disconnection from expression.
    """
    if not self.comm_expr.connected:
      self.root_fsm.abort()

  def run(self):
    """
    """
    try:
      while not self.comm_expr.connected:
        time.sleep(1)
        print '.',
      self.root_fsm.run(self.step_callback)
    except StandardError, e:
      handle_exception(None)
    except KeyboardInterrupt:
      LOG.fatal('aborting')
    self.root_fsm.abort()
    LOG.debug('FSM run done.')


if __name__ == '__main__':
  from utils import vision, fps

  class Test_BehaviourBuilder(BehaviourBuilder):
    # OUR STATE FUNCTIONS
    def started(self):
      print 'test started'
      return True

    def testing(self):
      faces = self.vision.find_faces()
      self.vision.mark_rects(faces)
      self.vision.gui.show_frame(self.vision.frame)
      return bool(faces)

    # SETTING UP
    def __init__(self):
      machine_def = [ ('test', ( ( STARTED ,self.started,'TESTING'),
                                 ('TESTING',self.testing, STOPPED ) ),
                       None) ]
      super(Test_BehaviourBuilder,self).__init__(machine_def)

      self.my_fps = fps.SimpleFPS(30)           # target: refresh every 30frames
      try:
        self.vision = vision.CamUtils()
        self.vision.use_camera(conf.ROBOT['mod_vision']['sensor'])
        #XXX: put that to conf for vision to read
        self.vision_frame = self.vision.camera.tolerance = .1   # 10%
        self.vision.gui_create()
        self.vision.update()
        self.vision.enable_face_detection()
      except vision.VisionException, e:
        self.comm_expr.done()
        fatal(e)

    # OVERRIDING MOTHER CLASS TO DO OUR JOB
    def step_callback(self):
      super(Test_BehaviourBuilder,self).step_callback()
      self.vision.update()
      self.vision.gui_show()
      self.my_fps.update()
      self.my_fps.show()

    def cleanUp(self):
      super(Test_BehaviourBuilder,self).cleanUp()
      self.vision.gui_destroy()

  import sys
  import logging
  from utils import comm, conf, LOGFORMATINFO
  logging.basicConfig(level=logging.DEBUG, **LOGFORMATINFO)
  conf.set_name('lightHead')

  player = Test_BehaviourBuilder()
  player.run()
  player.cleanUp()
