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
import random
import time

from RAS.au_pool import VAL
from HMS.behaviour_builder import BehaviourBuilder, fatal
from HMS.communication import MTLightheadComm
from utils.FSMs import SPFSM, STARTED, STOPPED
from utils import vision, fps, conf

LOG = logging.getLogger(__package__)
_CERVICALS = ('53.5','55.5','51.5')
_THORACICS = ('TX','TY','TZ')
_SACCADES_PER_GAZE = 3


# OUR STATES
ST_AWAKED       = 'awaked'
ST_ACTUATE_RAND = 'actuate_random'
ST_SEARCH       = 'search'
ST_KEEP_USR_VIS = 'keep_user_visible'
ST_FOUND_USR    = 'user_visible'
ST_GOODBYE      = 'disengage'
#ST_  = ''

# CONTEXTUAL RANGES
AOI_RANGES = {           # in meters
                # X (horiz) # Y (depth) # Z (vert)
  ST_SEARCH     : ( (-5,1), (.5, 10), (-.5,.5) ),
}
REACH_RANGES = {        # 
}
GAZE_COMFORT = ( (-1,1), ( 3,5), (-.5,.5) )
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
  ST_SEARCH     : ( (-.1,.1), (0,0), (-.5,.5) ),
  ST_FOUND_USR  : ( (), (), (), ),
}

from numpy import array
from math import cos, sin, tan, pi


class AOI(object):
  """Area of Interest.
  """

  def __init__(self, location):
    """location: 3D Vector, Area Of Interest's position realtive to ready pose.
    """
    self.location = list(location)

  def get_Egaze(self, norm_orient):
    """Returns eye gaze 3D vector considering robot's orientation (head gaze).

    norm_orient: 3D Vector, normalized orientation relative to ready pose.
    """
    Cph,Cth,Cps = [cos(-pi*a) for a in norm_orient]
    Sph,Sth,Sps = [sin(-pi*a) for a in norm_orient]
    M = array([[Cth*Cps, -Cph*Sps+Sph*Sth*Cps,  Sph*Sps+Cph*Sth*Cps],
               [Cth*Sps,  Cph*Cps+Sph*Sth*Sps, -Sph*Cps+Cph*Sth*Sps],
               [-Sth,     Sph*Cth,              Cph*Cth]])
    print "aoi:", self.location, "O:", norm_orient, "EG:", M.dot(self.location)
    return M.dot(self.location)


class Action(object):
  """
  """

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
  
    # --- OUR STATE FUNCTIONS
  def st_started(self):
    print 'test started'
    str = 'starting non-interacting, non-verbal mode'
    self.comm_expr.sendDB_waitReply(";'%s';;;;"%str, 'START')
    return True

  def st_search(self):
    if self.actions['AOI'].is_active(time.time()):
        
      self.aoi[0] = AOI(self.actions['AOI'].get_data(ST_SEARCH))
      print "new AOI:", self.aoi[0].location
      self.gaze_reach_blink()
#      self.gaze_reach_pursuit()
#      random.choice((self.gaze_reach_blink, self.gaze_reach_pursuit))()
#      self.update_spine_orientations()
      return
    if self.aoi[0]:
      self.egaze[1] = (0,10,0)
      self.gaze_refine(factor=.9, steps=3) or self.gaze_around(1)
#      return st_detect_human()

  def st_detect_human(self):
    """Detects human and sets its location in the visual field.
    """
#    return self.vision.detect_face() and ST_HUMAN_FOUND or None

  def st_detect_face(self):
    if self.vision.detect_face():
      self.comm_expr.set_fExpression("surprised:.3")
      self.comm_expr.send_waitReply("")
      return True

  def st_keep_usr_vis(self):
    faces = self.vision.find_faces()
    if self.vision.gui:
      self.vision.mark_rects(faces)
      self.vision.gui.show_frame(self.vision.frame)
    return faces and STOPPED or None

  def st_actuate_random(self):
    now = time.time()
    fe, gz, nc, sp = (self.actions[k] for k in ('fexpr','gaze','neck','spine'))
    if fe.is_active(now):
      self.comm_expr.set_fExpression(fe.get_data(ST_SEARCH))
    if gz.is_active(now):
      self.comm_expr.set_gaze(gz.get_data(ST_SEARCH))
    if nc.is_active(now):
      self.comm_expr.set_neck(orientation=nc.get_data(ST_SEARCH))
    if any(self.comm_expr.datablock):
      self.comm_expr.send_datablock()

  def st_stopped(self, name):
    print 'test stopped'
    return

  # --- INSTANCE MANAGEMENT
  def __init__(self, with_gui=True):
    machines_def = [ 
      ('spine', ((STARTED,              self.st_started,        ST_SEARCH),
                 (ST_SEARCH,            self.st_search,         None),
                 (ST_KEEP_USR_VIS,      self.st_keep_usr_vis,   None)),
       None),
      ('vis', ((ST_SEARCH,              self.st_detect_human,   ST_FOUND_USR),
               (ST_FOUND_USR,           self.st_detect_face,    ST_KEEP_USR_VIS),
               (ST_KEEP_USR_VIS,        self.st_detect_human,   None),),
       'spine'),
      ]
    super(LightHead_Behaviour,self).__init__(machines_def)

    fct_rand_range = lambda x: [random.uniform(*a) for a in (x)]
    self.actions = {
      'AOI'     : Action(AOI_RANGES, fct_rand_range, (3, 10)),
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
    self.aoi = [ None, None ]                                   # prev / current
    self.egaze = [ None, None ]                                 # received/sent
    self.LH_connected = False
    self.comm_lightHead = MTLightheadComm(conf.lightHead_server,
                                          self.lighthead_connected)
    while not self.LH_connected:
      time.sleep(1)

    # --- OVERRIDING MOTHER CLASS TO DO OUR JOB
  def step_callback(self):
    super(LightHead_Behaviour,self).step_callback()
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

  def update_egaze_orientations(self):
    AUs = self.comm_lightHead.get_snapshot(('gaze',))['gaze']
    self.egaze[0] = (AUs['61.5L'],AUs['61.5R']), AUs['63.5']
    return self.egaze

  def update_spine_orientations(self):
    AUs = self.comm_lightHead.get_snapshot(('spine',))['spine']
    self.spine = ([AUs.has_key(au) and AUs[au][1] or None for au in _CERVICALS],
                  [AUs.has_key(au) and AUs[au][1] or None for au in _THORACICS])
    return self.spine

  def gaze_reach_blink(self):
    # 1/ gaze towards an AOI, capping eye-gaze to comfort zone (done by expr2:
    # fovea_control instinct, also rotates the rest of the body) closing eyes.
    # TODO: reduce e_gaze by 10% towards AOI.
    TAG = "TAG_RB"
    gaze_str = "%.5f, %.5f, %.5f"%tuple(self.aoi[0].location)
    self.comm_expr.sendDB_waitReply(";;%s;;enable:FC|blink:close;" %
                                    gaze_str, TAG)
    time.sleep(1)
    # 2/ open eyes before end of spine torsion, restore 
    self.comm_expr.send_my_datablock(";;;;disable:FC|blink:open;"+TAG)
    
  def gaze_reach_pursuit(self):
    # 1/ select a temporary AOI in eyes' "comfort zone" towards target AOI
    # 2/ keep focusing on temporary AOI (-error) while still in comfort zone
    # 3/ when out of comfort zone and not yet at target AOI, return to 1/
    TAG = "TAG_RP"
    self.comm_expr.set_gaze(self.aoi[0].location)
    self.comm_expr.sendDB_waitReply(";;;;disable:FC;", TAG)
#    self.update_egaze_orientations()
#    for i in range(_SACCADES_PER_GAZE):
#      self.comm_expr.set_gaze( val*i/_SACCADES_PER_GAZE for i in )
#      self.comm_expr.sendDB_waitReply()
    self.comm_expr.sendDB_waitReply(";;;;enable:FC;", TAG)

  def gaze_around(self, dist_range):
    """location: eye-gaze vector relative to center of eyes 
    """
    TAG = 'GA'
    self.comm_expr.sendDB_waitReply(";;;;disable:FC;", TAG)
    for i in range(3):
      self.comm_expr.set_gaze([ (v-dist_range/2)+random.random()*dist_range
                                for v in self.egaze[1] ])
      self.comm_expr.sendDB_waitReply()
      time.sleep(1)
    self.comm_expr.sendDB_waitReply(";;;;enable:FC;", TAG)
      

  def gaze_refine(self, factor, steps):
    """
    """
#    self.

  # def gaze_refine(self):
  #   """Considers AOI's location and refines eye-gaze through a few saccades.
  #   """
  #   raise NotImplementedError()
  #   self.comm_expr.set_gaze(self.aoi.get_)
  #   self.comm_expr.send_datablock()



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
#  import pdb; pdb.set_trace()
  print 'done'
