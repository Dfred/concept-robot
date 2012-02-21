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

from RAS.au_pool import VAL
from HMS.behaviour_builder import BehaviourBuilder, fatal
from HMS.communication import ThreadedLightheadComm
from utils.FSMs import SMFSM
from utils import vision, fps, conf

# OUR STATES
ST_AWAKED       = 'awaked'
ST_ACTUATE_RAND = 'actuate_random'
ST_SEARCH       = 'search'
ST_KEEPVIS_USR  = 'keep_user_visible'
ST_FOUND_USR    = 'user_visible'
ST_GOODBYE      = 'disengage'
#ST_  = ''

AOI_RANGES = {           # in meters
                # X (horiz) # Y (depth) # Z (vert)
  ST_SEARCH     : ( (-3,3), (-3, 10), (-1,.5) ),
}
REACH_RANGES = {        # 
}
GAZE_COMFORT = ( (-1,1), ( 2,5), (-1,.5) )
F_EXPRS = {
  ST_SEARCH     : ('slow_neutral', 'really_look', 'frown2', 'dummy_name4'),
  ST_FOUND_USR  : ('simple_smile_wide1', 'surprised1'),
}
GAZE_RANGES = {         # in meters
                # X (horiz) # Y (depth) # Z (vert)
  ST_SEARCH     : GAZE_COMFORT,
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

from numpy import array
from math import cos, sin, tan, pi

def get_head_aRot(spineAUs):
  """Returns the absolute rotation of head"""
  AXIS = (('53.5','TX'), ('55.5','TY'), ('51.5','TZ'))
  return [spineAUs.setdefault(kH,0)+spineAUs.setdefault(kT,0) for kH,kT in AXIS]

def vector2angles(vector):
  """Returns gaze orientation (phi,theta,psi) needed to align gaze to vector"""
  return 
 
class AOI(object):
  """Area of Interest."""
  def __init__(self, location):
    """location: 3D Vector, Area Of Interest's position realtive to ready pose.
    """
    self.location = array(location)

  def get_Egaze(self, orientation):
    """Returns eye gaze 3D vector considering robot's orientation (head gaze).

    orientation: 3D Vector, robot's orientation relative to ready pose.
    """
    Cph,Cth,Cps = [cos(-pi*a) for a in orientation]
    Sph,Sth,Sps = [sin(-pi*a) for a in orientation]
    M = array([[Cth*Cps, -Cph*Sps+Sph*Sth*Cps,  Sph*Sps+Cph*Sth*Cps],
               [Cth*Sps,  Cph*Cps+Sph*Sth*Sps, -Sph*Cps+Cph*Sth*Sps],
               [-Sth,     Sph*Cth,              Cph*Cth]])
    return M.dot(self.location)


class Action(object):
  def __init__(self, data, data_fct, period_range, init_time=None):
    self.period_range = period_range    # min/max time between actions (in s.)
    self.time   = init_time != None and init_time or time.time()
    self.data   = data
    self.fct    = data_fct

  def is_active(self, now):
    """Returns True if now falls into action's period_range, else False.
    """
    if not self.time:
      return True
    b = now - self.time > random.uniform(*self.period_range)
    if b:
      self.time = now
    return b

  def get_data(self, state):
    """Returns data_function applied to data for current state, or False.
    """
    return self.data.has_key(state) and self.fct(self.data[state])


class LightHead_Behaviour(BehaviourBuilder):
  """
  """
  
  def __init__(self, with_gui=True):
    rules = ( (SMFSM.STARTED,self.st_started),
              (ST_SEARCH,   self.st_search),
#              (ST_SEARCH,   self.st_actuate_random),
#          (ST_ENGAGE,   self.st_engage),
#          (ST_, self.),
              (SMFSM.STOPPED,self.st_stopped) )
    machine_def = [ ('test', rules, None) ]
    super(LightHead_Behaviour,self).__init__(machine_def)

    fct_rand_range = lambda x: [random.uniform(*a) for a in (x)]
    self.actions = {
      'AOI'     : Action(AOI_RANGES, fct_rand_range, (5, 20)),
      'fexpr'   : Action(F_EXPRS, random.choice, (.8, 20)),
      'gaze'    : Action(GAZE_RANGES, fct_rand_range, (1,5)),
      'neck'    : Action(NECK_RANGES, fct_rand_range, (5,15)),
      'spine'   : Action(SPINE_RANGES, fct_rand_range, (5,15)),
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
    self.LH_connected = False
    self.comm_lightHead = ThreadedLightheadComm(conf.lightHead_server,
                                                self.lighthead_connected)
    while not self.LH_connected:
      time.sleep(1)

    # --- OVERRIDING MOTHER CLASS TO DO OUR JOB
  def step_callback(self, FSMs):
    super(LightHead_Behaviour,self).step_callback(FSMs)
    self.vision.update()
    self.vision.gui_show()
    self.my_fps.update()
    self.my_fps.show()

  def cleanUp(self):
    super(LightHead_Behaviour,self).cleanUp()
    self.vision.gui_destroy()
    
    # --- OUR UTILITY FUNCTIONS
  def lighthead_connected(self):
    self.LH_connected = True

  def gaze_reach_blink(self):
    # 1/ make a rough eye gaze towards an AOI
    sp_snapshot = self.comm_lightHead.get_snapshot(("spine",))['spine']
    spineAUs = dict(zip(sp_snapshot[0][1], sp_snapshot[1][:,VAL]))
    e_gaze = self.aoi.get_Egaze(get_head_aRot(spineAUs))
    # TODO: reduce e_gaze by 10% towards AOI.

    # 2/ cap gaze to comfort zone
    e_gaze = [ max(GAZE_COMFORT[i][0], min(val,GAZE_COMFORT[i][1])) for i,val
                  in enumerate(e_gaze) ]
    # 3/ close eyes + rotate head towards AOI
    str_EG = ','.join([str(f) for f in e_gaze])
    str_HG = "((%.5f, %.5f, %.5f))" % Vector2Angles(self.aoi.location)
    self.comm_expr.send_my_datablock('close_eyes:1;;%s;%s;disable:blink;TAG_RB'%
                                     (str_EG,str_HG) )
    # 4/ open eyes before end of spine torsion
    self.comm_expr.set_instinct('enable:blink')
    self.comm_expr.send_datablock()
    
  def gaze_reach_pursuit(self):
    # 1/ select a temporary AOI in eyes' "comfort zone" towards target AOI
    # 2/ keep focusing on temporary AOI (-error) while still in comfort zone
    # 3/ when out of comfort zone and not yet at target AOI, return to 1/
    pass

    # --- OUR STATE FUNCTIONS
  def st_started(self):
    print 'test started'
    return ST_SEARCH

  def st_search(self):
    self.aoi = AOI(self.actions['AOI'].is_active(time.time()))
    return random.choice((self.gaze_reach_blink, self.gaze_reach_pursuit))()

  def st_reachedAOI(self):
    spineAUs = self.comm_lightHead.get_snapshot('spine', binary=True)
    self.comm_expr.set_gaze( self.aoi.get_Egaze(get_head_aRot(spineAUs) +
                                                get_thorax_aRot(spineAUs)) )
    self.comm_expr.send_datablock()

  def st_detect_human(self):
    return self.vision.detect_face() and ST_HUMAN_FOUND or None

  def st_actuate_random(self):
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
  from utils import comm, LOGFORMATINFO
  logging.basicConfig(level=logging.DEBUG, **LOGFORMATINFO)
  conf.set_name('lightHead')
  missing = conf.load(required_entries=('lightHead_server',))
  if missing:
    print '\nMissing configuration entry: %s', missing
    sys.exit(2)

  player = LightHead_Behaviour(len(sys.argv) > 1 and sys.argv[1] == '-g')
  player.run()
  player.cleanup()
