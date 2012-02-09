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

import random
import time

from HMS.expression_player import Behaviour_Builder, fatal
from utils.FSMs import SMFSM
from utils import vision, fps

# OUR STATES
ST_AWAKED       = 'awaked'
ST_SEARCH       = 'search'
ST_KEEPVIS_USR  = 'keep_user_visible'
ST_FOUND_USR    = 'user_visible'
ST_GOODBYE      = 'disengage'
#ST_  = ''


FEXPRS = {
  ST_SEARCH     : ('neutral', 'really_look', 'frown2', 'dummy_name4'),
  ST_FOUND_USR  : ('simple_smile_wide1', 'surprised1'),
}
GAZE_RANGES = {         # in meters
                # X (horiz) # Y (depth) # Z (vert)
  ST_SEARCH     : ( (-1,1), ( 2,5), (-1,.5) ),
  ST_FOUND_USR  : ( (), (), (), ),
}
NECK_RANGES = {         # in normalized angle
  ST_SEARCH     : ( (-.1,.1), (-.1,.1), (-.5,.5) ),
  ST_FOUND_USR  : ( (), (), (), ),
}
SPINE_RANGES = {        # in normalized angle
  ST_SEARCH     : ( (-.1,.1), (-.1,.1), (-.5,.5) ),
  ST_FOUND_USR  : ( (), (), (), ),
}


class Action(object):
  def __init__(self, period_range, init_time, data, fct):
    self.period_range = period_range    # min/max time between actions (in s.)
    self.time   = init_time
    self.data   = data
    self.fct    = fct

  def is_active(self, now):
    b = now - self.time > random.uniform(*self.period_range)
    if b:
      self.time = now
    return b

  def get_data(self, state):
    return self.fct(self.data[state])


class LightHead_Behaviour(Behaviour_Builder):
  """
  """
  
  def __init__(self, with_gui=True):
    rules = ( (SMFSM.STARTED,self.st_started),
              (ST_SEARCH,   self.st_search),
#          (ST_ENGAGE,   self.st_engage),
#          (ST_, self.),
              (SMFSM.STOPPED,self.st_stopped) )
    machine_def = [ ('test', rules, None) ]
    super(LightHead_Behaviour,self).__init__(machine_def)

    fct_rand_range = lambda x: [random.uniform(*a) for a in (x)]
    self.actions = {
      'fexpr': Action((.8, 20), time.time(), FEXPRS, random.choice),
      'gaze' : Action((1,5) , time.time(), GAZE_RANGES, fct_rand_range),
      'neck' : Action((5,15), time.time(), NECK_RANGES, fct_rand_range),
      'spine': Action((5,15), time.time(), SPINE_RANGES, fct_rand_range),
      }
    self.my_fps = fps.SimpleFPS(30)           # target: refresh every 30frames
    try:
      self.vision = vision.CamUtils()
      self.vision.use_camera(conf.ROBOT['mod_vision']['sensor'])
        #XXX: put that to conf for vision to read
      self.vision_frame = self.vision.camera.tolerance = .1   # 10%
      if with_gui:
        self.vision.gui_create()
      else:
        print '--- NOT USING CAMERA GUI ---'
      self.vision.update()
      self.vision.enable_face_detection()
    except vision.VisionException, e:
      fatal(e)

    # OVERRIDING MOTHER CLASS TO DO OUR JOB
  def step_callback(self, FSMs):
    super(LightHead_Behaviour,self).step_callback(FSMs)
    self.vision.update()
    self.vision.gui_show()
    self.my_fps.update()
    self.my_fps.show()

  def cleanUp(self):
    super(LightHead_Behaviour,self).cleanUp()
    self.vision.gui_destroy()

    # OUR STATE FUNCTIONS
  def st_started(self):
    print 'test started'
    return ST_SEARCH

  def st_search(self):
    now = time.time()
    fe, gz, nc, sp = (self.actions[k] for k in ('fexpr','gaze','neck','spine'))
    if fe.is_active(now):
      self.comm_expr.set_fExpression(fe.get_data('search'))
    if gz.is_active(now):
      self.comm_expr.set_gaze(gz.get_data('search'))
    if nc.is_active(now):
      self.comm_expr.set_neck(orientation=nc.get_data('search'))
    if any(self.comm_expr.datablock):
      self.comm_expr.send_datablock()

  def st_keep_usr_visible(self):
    faces = self.vision.find_faces()
    if self.vision.gui:
      self.vision.mark_rects(faces)
      self.vision.gui.show_frame(self.vision.frame)
    return faces and SMFSM.STOPPED or None

  def st_stopped(self, name):
    print 'test stopped'
    return


if __name__ == '__main__':
  import sys

  import logging
  from utils import comm, conf, LOGFORMATINFO
  logging.basicConfig(level=logging.DEBUG, **LOGFORMATINFO)
  conf.set_name('lightHead')

  player = LightHead_Behaviour(len(sys.argv) > 1 and sys.argv[1] == '-g')
  player.run()
  player.cleanup()
