#!/usr/bin/python

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
 FACE MODULE: blender backend

 This module uses the Blender Game Engine as a backend for animating LightHead.
 To make this work, you need to let the initialization routine list the AU you
  support: define a property per AU in your .blend. Also, for most AUs you need
  a Shape Action actuator which provides the relative basic facial animation.

 MODULES IO:
 -----------
 INPUT: - face

 A few things to remember for integration with Blender (2.49):
  * defining classes in toplevel scripts (like here) leads to scope problems
"""

import sys, time, atexit
from math import cos, sin, pi

import GameLogic as G

from RAS.face import Face_Server


class FaceHW(Face_Server):
  """Blender is our entry point, so make it simple letting blender take over.
  So this script fetches Face's data pool directly in update().
  
  No hardware implementation is actually needed in this case.
  """
  global G

  def cleanUp(self):
    shutdown(G.getCurrentController())

  def cam_proj(self, *args):
    m = G.getCurrentScene().active_camera.projection_matrix
    col = int(args[0])
    row = int(args[1])
    inc = float(args[2])
    m[row][col] += inc
    print m
    G.getCurrentScene().active_camera.setProjectionMatrix(m)

  def cam_mview(self, *args):
    m = G.getCurrentScene().active_camera.modelview_matrix
    col = int(args[0])
    row = int(args[1])
    inc = float(args[2])
    m[row][col] += inc
    print m
    G.getCurrentScene().active_camera.setModelViewMatrix(m)

# A word on threading:
# The server can run in its thread, handlers (connected clients) can also run in
#  their own. With standard python VM, no threading is supposedly faster.
# NOW READ THIS CAREFULLY:
# ------------------------
# If THREADED_CLIENTS is True, you need to use locking facilities properly (see
#  comm.BaseServer.threadsafe_start/stop).
# If THREADED_CLIENTS is False and THREADED_SERVER is True, ONLY ONE CLIENT can
#  connect and its handler will indeed run in the server thread.
THREADED_SERVER  = False
THREADED_CLIENTS = False
THREAD_INFO = (THREADED_SERVER, THREADED_CLIENTS)

OBJ_PREFIX = "OB"
CTR_SUFFIX = "#CONTR#"
SH_ACT_LEN = 50
MAX_FPS = 60
INFO_PERIOD = None
# Naming Convention: regular objects are lower case, bones are title-ized.
REQUIRED_OBJECTS = ('eye_L', 'eye_R', 'tongue', 'Skeleton')


def exiting():
  # server may not have been successfully created
  if hasattr(G, "server") and G.server.is_started():
    G.server.shutdown()

atexit.register(exiting)

def fatal(error):
  """Common function to gracefully quit."""
  print '   *** Fatal: %s ***' % error
  if sys.exc_info() != (None,None,None):
    from utils import handle_exception
    handle_exception(None,error)
  shutdown(G.getCurrentController())

def shutdown(cont):
  """Finish animation and let atexit do the cleaning job"""
  try:
    cont.activate(cont.actuators["- QUITTER"])
  except:
    pass
  sys.exit( not hasattr(G, 'server') and 1 or 0)            # see exiting()

def check_defects(owner, acts):
  """Check if actuators have their property set and are in proper mode ."""
  keys = [ act.name for act in acts] + ['61.5L', '61.5R', '63.5'] # add eyes

  for name in keys:
    if not owner.has_key('p'+name):
      raise StandardError('missing property p%s' % name)
  for act in acts :
    if act.mode != G.KX_ACTIONACT_PROPERTY:
      raise StandardError('Actuator %s shall use Shape Action Playback of'
                          'type property' % act.name)
  return False

def initialize(server):
  """Initialiazes and configures facial subsystem (blender specifics...)"""
  print "loaded module from", __path__[0]

  # get driven objects
  objs = G.getCurrentScene().objects
  for obj_name in REQUIRED_OBJECTS:
      if OBJ_PREFIX+obj_name not in objs:
          return fatal("Object '%s' not found in blender scene" % obj_name)
      setattr(G, obj_name, objs[OBJ_PREFIX+obj_name])

  # set available Action Units from the blender file (Blender Shape Actions)
  cont = G.getCurrentController()
  owner = cont.owner
  acts = [act for act in cont.actuators if
          not act.name.startswith('-') and act.action]
  check_defects(owner, acts)

  # properties must be set to 'head' and 'Skeleton'.
  # BEWARE to not set props to these objects before, they'll be included here.
  AUs = [ (pAU[1:], obj[pAU]/SH_ACT_LEN) for obj in (owner, G.Skeleton) for
          pAU in obj.getPropertyNames() ]
  if not server.set_available_AUs(AUs):
      return fatal('Check your .blend file for bad property names')

  # load axis limits for the Skeleton regardless of the configuration: if the
  # spine mod is loaded (origin head), no spine AU should be processed here.
  from utils import conf;                 #TODO: get values from blend file?
  # blender might issue a warning here, nvm as we add a member, not access it.
  G.Skeleton.limits = conf.lib_spine['blender']['AXIS_LIMITS']

  # ok, startup
  G.initialized = True
  G.info_duration = 0
  G.setLogicTicRate(MAX_FPS)
  G.setMaxLogicFrame(1)       # relative to rendering
  import Rasterizer
#    Rasterizer.enableMotionBlur( 0.65)
  print "Material mode:", ['TEXFACE_MATERIAL','MULTITEX_MATERIAL',
                           'GLSL_MATERIAL'][Rasterizer.getMaterialMode()]
  cam = G.getCurrentScene().active_camera
  print """camera: lens %s
view matrix: %s
proj matrix: %s
  """ % (cam.lens, cam.modelview_matrix, cam.projection_matrix)
  G.last_update_time = time.time()
  return cont


def update():
  """
  """
  global INFO_PERIOD

  def get_orientation_XZ(x,z):
    """Up is positive Z values and the model is supposed to look towards
    negative Y values.
    """
    return [ [cos(azL),        -sin(azL),         0],
             [cos(x)*sin(z), cos(ax)*cos(azL),-sin(ax)],
             [sin(x)*sin(z), sin(ax)*cos(azL), cos(ax)] ]

  srv = G.face_server
  cont = G.getCurrentController()
  eyes_done, spine_done = False, False
  time_diff = time.time() - G.last_update_time

  # threaded server is thread-safe
  face_map = srv.update(time_diff)

  for au, values in face_map.iteritems():
    # XXX: yes, 6 is an eye prefix (do better ?)
    if au.startswith('6'):
        if eyes_done:                   # all in one pass
            continue
        ax  = -face_map['63.5'][3]      # Eye_L is the character's left eye.
        azR =  face_map['61.5R'][3]
        azL =  face_map['61.5L'][3]
        G.eye_L.localOrientation = get_orientation_XZ(ax,azL)
        G.eye_R.localOrientation = get_orientation_XZ(ax,azR)
        eyes_done = True

    elif au.startswith('T'):
        if au[-1] == '0':
            cont.owner['p'+au] = SH_ACT_LEN * values[3]
            cont.activate(cont.actuators[au])
        else:
            a_min, a_max = G.Skeleton.limits[au]
            a_bound = values[3] < 0 and a_min or a_max
            G.Skeleton['p'+au] = (abs(values[3])/a_bound +1) * SH_ACT_LEN/2

    # XXX: yes, 9 is a tongue prefix (do better ?)
    elif au.startswith('9'):
        G.tongue[au] = SH_ACT_LEN * values[3]

    # XXX: yes, 5 is a head prefix (do better ?)
    elif au.startswith('5'):
        if float(au) <= 55.5:   # pan, tilt, roll
            a_min, a_max = G.Skeleton.limits[au]
            a_bound = values[3] < 0 and a_min or a_max
            G.Skeleton['p'+au] = (abs(values[3])/a_bound +1) * SH_ACT_LEN/2

    elif au == '26':
        # TODO: try with G.setChannel ?
        G.Skeleton['p26'] = SH_ACT_LEN * values[3]

    elif au[0].isdigit():
        cont.owner['p'+au] = SH_ACT_LEN * values[3]
        cont.activate(cont.actuators[au])

    else:
        a_min, a_max = G.Skeleton.limits[au]
        if values[3] >= 0:
            G.Skeleton['p'+au] = (values[3]/a_max + 1) * SH_ACT_LEN/2
        if values[3] < 0:
            G.Skeleton['p'+au] = (-values[3]/a_min +1) * SH_ACT_LEN/2

  G.last_update_time = time.time()

  G.info_duration += time_diff
  if INFO_PERIOD is not None and G.info_duration > INFO_PERIOD:
      print "--- RENDERING INFO ---"
      print "BGE logic running at", G.getLogicTicRate(), "fps."
#        print "BGE physics running at", G.getPhysicsTicRate(), "fps."
      print "BGE graphics currently at", G.getAverageFrameRate(), "fps."
      G.info_duration = 0


#
# Main loop
#

def main():
    if not hasattr(G, "initialized"):
        try:
            import RAS
            G.server = RAS.initialize(THREAD_INFO)
            G.face_server = G.server['face']

            cont = initialize(G.face_server)
            G.server.set_listen_timeout(0.001)      # tune it !
            G.server.start()
        except StandardError:
            fatal("initialization error")
        else:
            print '--- initialization OK ---'
    else:
        if not THREADED_SERVER:
            # server handles channels explicitly
            if not G.server.serve_once():
                print 'server returned an error'
                G.server.shutdown()
        try:
            # update blender with fresh face data
            update()
        except Exception,e:
            fatal("runtime error")
