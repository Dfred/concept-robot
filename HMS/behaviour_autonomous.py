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

PERIOD_RANGES = {               # min/max time between actions (in seconds)
  'fexpr': (.8, 20),
  'gaze' : (1,5),
  'neck' : (5,15),
}
FEXPRS = {
  'search' : ('neutral', 'really_look', 'frown2', 'dummy_name4'),
  'found'  : ('simple_smile_wide1', 'surprised1'),
}
SCAN_RANGE = {
  'gaze' : (            # in meters
    (-1,1),     # X (horiz)
    ( 2,5),     # Y (depth)
    (-1,.5)     # Z (vert)
    ),
  'neck' : (            # in normalized angle
    (-.1,.1),   # X (horiz)
    (-.1,.1),   # Y (depth)
    (-.5,.5)    # Z (vert)
    ),
}

# OUR STATES
ST_AWAKED       = 'awaked'
ST_SEARCH       = 'search'
ST_KEEPVIS_USR  = 'keep_user_visible'
ST_FOUND_USR    = 'user_visible'
ST_GOODBYE      = 'disengage'
#ST_  = ''


class LightHead_Behaviour(Behaviour_Builder):
  """
  """
  
  def __init__(self, with_gui=True):
      rules = (
          (SMFSM.STARTED,self.st_started),
          (ST_SEARCH,   self.st_search),
#          (ST_ENGAGE,   self.st_engage),
#          (ST_, self.),
          (SMFSM.STOPPED,self.st_stopped) )
      machine_def = [ ('test', rules, None) ]
      super(LightHead_Behaviour,self).__init__(machine_def)

      t = time.time()
      self.last_time = {'fexpr':t, 'gaze':t, 'neck':t}
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
    if now - self.last_time['fexpr'] > random.uniform(*PERIOD_RANGES['fexpr']):
      self.comm_expr.set_fExpression(random.choice(FEXPRS['search']))
      self.last_time['fexpr'] = now
    if now - self.last_time['gaze'] > random.uniform(*PERIOD_RANGES['gaze']):
      self.comm_expr.set_gaze([random.uniform(*a) for a in (SCAN_RANGE['gaze'])])
      self.last_time['gaze'] = now
    if now - self.last_time['neck'] > random.uniform(*PERIOD_RANGES['neck']):
      self.comm_expr.set_neck(orientation=[random.uniform(*a) for a
                                           in (SCAN_RANGE['neck']) ] )
      self.last_time['neck'] = now
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
