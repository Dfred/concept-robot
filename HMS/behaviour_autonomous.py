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
from utils.parallel_fsm import STARTED, STOPPED, MPFSM as FSM
from utils import vision, audio, conf

LOG = logging.getLogger(__package__)
_CERVICALS = ('53.5','55.5','51.5')
_THORACICS = ('TX','TY','TZ')
_SACCADES_PER_GAZE = 3

MAX_STABLE_DURATION = 30

# OUR STATES
ST_ACTUATE_RAND = 'actuate_random'
ST_AWAKED       = 'awaked'
ST_SEARCH       = 'search'
ST_KEEP_USRVIS  = 'keep_user_visible'
ST_FOUND_USR    = 'user_visible'
ST_GOODBYE      = 'disengage'
ST_BORED        = 'bored'
ST_ACTIVE       = 'active'
ST_SND_EVENT  = 'sound'

BORED_TEXTS = ("wellll....","hello?","anybody here?","pop podommm.")

# CONTEXTUAL RANGES
F_EXPRS = {
  ST_SEARCH     : ('neutral', 'really_look', 'frown2', 'dummy_name4'),
  ST_FOUND_USR  : ('simple_smile_wide1', 'surprised'),
}
AOI_RANGES = {           # in meters
                # X (horiz) # Y (depth) # Z (vert)
  ST_SEARCH     : ( (-5,1), (.5, 10), (-.5,.5) ),
}
GAZE_RANGES = {         # in meters
                # X (horiz) # Y (depth) # Z (vert)
  ST_SEARCH     : ( (-1,1), ( 3,5), (-.5,.5) ),
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


# --- SIMPLE TIME-BASED SELECTION OF ACTION
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

  def wait_active(self):
    """Blocks until action reaches its active state and returns None.
    """
    dt = random.uniform(*self.period_range)
    time.sleep(time.time() - self.time + dt)

  def get_data(self, state):
    """Returns data_function applied to data for current state, or False.
    """
    return self.data.has_key(state) and self.fct(self.data[state])

_fct_rand_range = lambda x: [random.uniform(*a) for a in (x)]
ACTIONS = {
  'AOI'     : Action(AOI_RANGES,        _fct_rand_range, (3, 10)),
  'fexpr'   : Action(F_EXPRS,           random.choice, (2.2, 20)),
  'gaze'    : Action(GAZE_RANGES,       _fct_rand_range, (1,5)),
  'spine'   : Action(SPINE_RANGES,      _fct_rand_range, (5,15)),
      }


class LightHead_Behaviour(BehaviourBuilder):
  """
  """
  # --- OUR STATE FUNCTIONS

  def st_actuate_random(self):
    now = time.time()
    fe, gz, sp = ( ACTIONS[k] for k in ('fexpr','gaze','spine') )
    if fe.is_active(now):
      self.comm_expr.set_fExpression(fe.get_data(ST_SEARCH), duration=1.5)
    if gz.is_active(now):
      self.comm_expr.set_gaze(gz.get_data(ST_SEARCH))
    if any(self.comm_expr.datablock):
      self.comm_expr.sendDB_waitReply()

  def st_search(self):
    ACTIONS['AOI'].wait_active()
    self.aoi[0] = AOI(ACTIONS['AOI'].get_data(ST_SEARCH))
    self.gaze_reach_blink(self.aoi[0])
#      self.gaze_reach_pursuit()
#      random.choice((self.gaze_reach_blink, self.gaze_reach_pursuit))()
#    self.gaze_refine(factor=.9, steps=3) or self.gaze_around(1)
    return True

  def st_detect_faces(self):
    """Detects faces and sets them to self.faces . State transition if detected.
    """
    self.update_vision()
    self.faces = self.vision.find_faces()
    if self.faces and self.vision.gui:
      self.vision.mark_rects(self.faces)
      self.vision.gui.show_frame(self.vision.frame)
    return len(self.faces)

  def st_detect_eyes(self):
    """Detects eyes and sets them to self.eyes . State transition if detected.
    """
    eyes = self.vision.find_eyes(self.faces)
    if eyes:
      self.eyes = eyes
      self.vision.mark_points(eyes[0][1:])
      self.vision.gui.show_frame(self.vision.frame)
    return len(eyes)

  def st_make_eyeContact(self):
    if not self.eyes:
      return None
    self.comm_expr.set_gaze(self.vision.get_face_3Dfocus(self.faces[0])[0])
    self.comm_expr.sendDB_waitReply()
    return True

  def st_engage(self):
    self.comm_expr.set_fExpression("smiling", intensity=.3)
    self.comm_expr.set_instinct("coactuate:attention=1")
    self.comm_expr.set_text("ohoh!")
    self.comm_expr.sendDB_waitReply()
    self.interacting = True
    return True
  
  def st_disengage(self):
    self.comm_expr.set_fExpression("neutral", intensity=.8)
    self.comm_expr.sendDB_waitReply()    
    text = random.choice(BORED_TEXTS)
    self.comm_expr.set_text(text)
    self.comm_expr.set_fExpression("sad", intensity=.5)
    self.comm_expr.set_gaze((0,10,0))
    self.comm_expr.set_instinct("coactuate:attention=.3")
    self.comm_expr.sendDB_waitReply()
    self.comm_expr.set_fExpression("sad", intensity=-.5)
    self.interacting = False
    return True

  def st_keep_usr_vis(self):
    if not self.faces:
      return None
    target = self.vision.get_face_3Dfocus(self.faces)[0]
    self.comm_expr.set_instinct("gaze-control:target=%s" % 
                                ((target[0]/50., 20, target[2]/50.),) )
#                                self.comm_expr.get_transform(target,'r'))
    self.comm_expr.sendDB_waitReply(tag='KUV')
    return True

  def st_gaze(self):
    self.gaze_around(1, (0,10,0))

  def st_check_boredom(self):
    """Detects boredom.
    """
    self.st_gaze()
    if time.time() - self.last_st_change_t > MAX_STABLE_DURATION and not self.interacting:
      self.on_state_update()
      return True
    time.sleep(.1)
    return False

  def st_check_activity(self):
    """Detects activity.
    """
    if time.time() - self.last_st_change_t < MAX_STABLE_DURATION:
      self.on_state_update()
      return True
    time.sleep(.1)
    return False

  def st_start(self):
    self.last_st_change_t = time.time()
    self.comm_expr.set_fExpression('neutral', intensity=1)
    self.comm_expr.set_text("Starting...")
    self.comm_expr.set_gaze((0,10,0))
    self.comm_expr.set_instinct("gaze-control:target=%s" % 
                                self.comm_expr.get_transform([0,0,0],'p'))
    self.comm_expr.sendDB_waitReply()
    return True

  def st_stopped(self, name):
    print 'test stopped'
    return


  # --- INSTANCE MANAGEMENT
  def __init__(self, with_gui=True):
    machines_def = [
#      ('cog', ((STARTED, self.st_actuate_random, None),), None)
      ('cog',   (
          (STARTED,             self.st_start,          ST_SEARCH),
#          (ST_SEARCH,           self.st_gaze,           None),
          (ST_FOUND_USR,        self.st_engage,         ST_KEEP_USRVIS),
          (ST_BORED,            self.st_disengage,      ST_SEARCH),
        ), None),
      ('att',   (
          ((ST_SEARCH,
            ST_ACTIVE),         self.st_check_boredom,  ST_BORED),
          (ST_BORED,            self.st_check_activity, ST_ACTIVE),
        ), 'cog'),
      ('vis',   (
          ((ST_SEARCH,
            ST_SND_EVENT),      self.st_detect_faces,   ST_FOUND_USR),
          (ST_KEEP_USRVIS,      self.st_detect_faces,   None),
        ), 'cog'),
      ('spine', (
          (ST_SEARCH,           self.st_search,         None),
#          (ST_SND_EVENT,        self.st_gaze_sound,     None),
          (ST_KEEP_USRVIS,      self.st_keep_usr_vis,   None),
        ), 'cog'),
 #     ('audio', (
 #         (ST_SEARCH,           self.st_check_sound,    ST_SND_EVENT),
#        ), 'cog'),
      ]
    super(LightHead_Behaviour,self).__init__(machines_def, FSM)
    # install boredom detection
    for fsm_name, r,p in machines_def:
      getattr(self, 'fsm_'+fsm_name).set_onStateChange(self.on_state_update)

    self.comm_lightHead = MTLightheadComm(conf.lightHead_server)
    self.aoi = [ None, None ]                                   # prev / current
    self.egaze = [ None, None ]                                 # received/sent
    self.faces = None                                           # detected faces
    self.last_st_change_t = None
    self.interacting = False

    try:
      self.vision = vision.CamUtils(conf.ROBOT['mod_vision']['sensor'])
      self.vision.update()
      LOG.info('--- %sDISPLAYING CAMERA ---', '' if with_gui else 'NOT ') 
      if with_gui:
        self.vision.gui_create()
        self.update_vision()
      self.vision.enable_face_detection()
    except vision.VisionException, e:
      fatal(e)

#    try:
#    self.audio = audio.Audio(conf.ROBOT['audition'])
#    except 

    # --- OVERRIDING MOTHER CLASS TO DO OUR JOB
#  def step_callback(self):
#    super(LightHead_Behaviour,self).step_callback()

  def cleanUp(self):
    LOG.debug('--- cleaning up ---')
    self.vision.gui_destroy()
    self.comm_lightHead.done()
    super(LightHead_Behaviour,self).cleanUp()
    
    # --- OUR UTILITY FUNCTIONS
  def on_state_update(self, *args):
    self.last_st_change_t = time.time()

  def update_vision(self):
    self.vision.update()
    self.vision.gui_show()

  def update_egaze_orientations(self):
    AUs = self.comm_lightHead.get_snapshot(('gaze',))['gaze']
    self.egaze[0] = (AUs['61.5L'],AUs['61.5R']), AUs['63.5']
    return self.egaze

  def update_spine_orientations(self):
    AUs = self.comm_lightHead.get_snapshot(('spine',))['spine']
    self.spine = ([AUs.has_key(au) and AUs[au][1] or None for au in _CERVICALS],
                  [AUs.has_key(au) and AUs[au][1] or None for au in _THORACICS])
    return self.spine

  def gaze_reach_blink(self, aoi):
    # 1/ gaze towards an AOI, capping eye-gaze to comfort zone (done by expr2:
    # fovea_control instinct, also rotates the rest of the body) closing eyes.
    # TODO: reduce e_gaze by 10% towards AOI.
    TAG, dur = "TAG_RB", 3
    gazeC_str = "[[%.5f, %.5f, %.5f]]" % tuple(aoi.location)
    self.comm_expr.sendDB_waitReply(";;;;blink:close|gaze-control:%s/%i;" %
                                    (gazeC_str, dur), TAG)
    # 2/ open eyes before end of spine torsion, restore 
    self.comm_expr.send_my_datablock(";;;;blink:open;"+TAG)
    
  def gaze_reach_pursuit(self, aoi):
    # 1/ select a temporary AOI in eyes' "comfort zone" towards target AOI
    # 2/ keep focusing on temporary AOI (-error) while still in comfort zone
    # 3/ when out of comfort zone and not yet at target AOI, return to 1/
    TAG = "TAG_RP"
    self.comm_expr.set_gaze(aoi.location)
    self.comm_expr.sendDB_waitReply(";;;;;", TAG)
#    self.update_egaze_orientations()
#    for i in range(_SACCADES_PER_GAZE):
#      self.comm_expr.set_gaze( val*i/_SACCADES_PER_GAZE for i in )
#      self.comm_expr.sendDB_waitReply()
    self.comm_expr.sendDB_waitReply(";;;;;", TAG)

  def gaze_around(self, dist_range, focus):
    """location: eye-gaze vector relative to center of eyes 
    """
    TAG = 'GA'
    for i in range(3):
      self.comm_expr.set_gaze([ (v-dist_range/2.0)+random.random()*dist_range
                                for v in focus ])
      self.comm_expr.sendDB_waitReply()
      time.sleep(1)

  # def gaze_refine(self):
  #   """Considers AOI's location and refines eye-gaze through a few saccades.
  #   """
  #   raise NotImplementedError()
  #   self.comm_expr.set_gaze(self.aoi.get_)
  #   self.comm_expr.send_datablock()



if __name__ == '__main__':
  import sys, threading

  import logging
  from utils import comm, LOGFORMATINFO
  LOGFORMATINFO['format'] = '%(threadName)s '+LOGFORMATINFO['format']
  logging.basicConfig(level=logging.DEBUG, **LOGFORMATINFO)
  conf.set_name('lightHead')
  missing = conf.load(required_entries=('lightHead_server',))
  if missing:
    print '\nMissing configuration entry: %s', missing
    sys.exit(2)

  player = LightHead_Behaviour(len(sys.argv) > 1 and sys.argv[1] == '-g')
  player.run()
  player.cleanUp()
#  import pdb; pdb.set_trace()
  print 'done', threading.enumerate()
