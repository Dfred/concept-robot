#!/usr/bin/python

# Lighty programm is a HRI PhD project at the University of Plymouth,
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

 This module uses the Blender Game Engine as a backend for animating Lighty.
 To make this work, you need to let the initialization routine list the AU you
  support: define a property per AU in your .blend. Also, for most AUs you need
  a Shape Action actuator which provides the relative basic facial animation.

 MODULES IO:
 -----------
 INPUT: - face

 A few things to remember for integration with Blender (2.49):
  * defining classes in toplevel scripts (like here) leads to scope problems
"""

import sys
import site, time
from math import cos, sin, pi

import GameLogic as G

PRE_NFO="*** INFO: "
PRE_WRN="*** WARNING: "
PRE_ERR="*** ERROR: "

if not hasattr(G,"initialized"):
  print "BlenderPlayer's python is:", filter(lambda x: x not in
                                                     "\r\n", sys.version) 

if sys.version_info[0] > 2:
  raise importError(PRE_ERR+"""this version is for python >= 2.5,
 use an alternate version supporting python3 series.""")
  sys.exit(2)

from RAS.au_pool import VAL
from RAS.face import FaceServerMixin, FaceHandlerMixin
from supported import VALID_AUs


def get_networking_classes():
  return (SrvMix_blender, FaceHandlerMixin)


class SrvMix_blender(FaceServerMixin):
  """Blender is our entry point, so make it simple letting blender take over.
  So this script fetches Face's data pool directly in update().
  
  Indeed, no hardware implementation is needed in this case.
  """

  def __init__(self):
    """Just sets this backend's name.
    """
    self.name = 'blender'
    super(SrvMix_blender,self).__init__()

#  def cleanUp(self):
#    shutdown(G.getCurrentController())

  def cam_projInc(self, *args):
    """Update projection matrix with relative values"""
    projMatrix = G.getCurrentScene().active_camera.projection_matrix
    if not len(args):
      return projMatrix
    projMatrix[ int(args[0]) ][ int(args[1]) ] += float(args[2])
    G.getCurrentScene().active_camera.projection_matrix = projMatrix
    print (PRE_NFO+"new projection matrix: %s" %
           G.getCurrentScene().active_camera.projection_matrix )

  def cam_proj(self, *args):
    """Update projection matrix with absolute values"""
    projMatrix = G.getCurrentScene().active_camera.projection_matrix
    if not len(args):
      return projMatrix
    projMatrix[ int(args[0]) ][ int(args[1]) ] = float(args[2])
    G.getCurrentScene().active_camera.projection_matrix = projMatrix
    print (PRE_NFO+"new projection matrix: %s" %
           G.getCurrentScene().active_camera.projection_matrix )

  def cam_mview(self, *args):
    viewMatrix = G.getCurrentScene().active_camera.modelview_matrix
    if not len(args):
	return viewMatrix
    viewMatrix[ int(args[0]) ][ int(args[1]) ] = float(args[2])
    G.getCurrentScene().active_camera.modelview_matrix = viewMatrix
    print (PRE_NFO+"new model view matrix: %s" %
           G.getCurrentScene().active_camera.modelview_matrix )


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
INFO_PERIOD = 10
# Naming Convention: regular objects are lower case, bones are title-ized.
REQUIRED_OBJECTS = ('eye_L', 'eye_R', 'tongue', 'Skeleton')


def exiting():                                  #TODO: any reliable way to this?
  # server may not have been successfully created
  if hasattr(G, "server") and G.server.is_started():
    G.server.shutdown()
try:
  import atexit
  atexit.register(exiting)
except ImportError:
  print PRE_NFO+"Couldn't import atexit"

def fatal(error):
  """Common function to gracefully quit."""
  print PRE_ERR+'--- Fatal: %s ---' % error
  if sys.exc_info() != (None,None,None) and (
    hasattr(G,'CONFIG') and G.CONFIG["verbosity"].startswith("DEBUG")):
    try: import pdb; pdb.post_mortem()
    except ValueError: pass
  shutdown(G.getCurrentController())

def shutdown(cont):
  """Finish animation and let atexit do the cleaning job"""
  try:
    cont.activate(cont.actuators["- QUITTER"])
  except:
    pass
  sys.exit( not hasattr(G, 'server') and 1 or 0)            # see exiting()

def check_defects(owner, acts):
  """Check if actuators have their property set and are in proper mode.
  Return True if any error found.
  """
  keys = [ act.name for act in acts] + ['61.5L', '61.5R', '63.5'] # add eyes
  errors = False
  PREFIX = PRE_ERR+"WITH BLENDER FILE: "
  for name in keys:
    if not owner.has_key('p'+name):
      print PREFIX+"object '{0}' has actuator '{1}' but no " \
        "property 'p{1}'".format(owner.name[2:], name)
      errors = True
  for act in acts :
    if act.mode != G.KX_ACTIONACT_PROPERTY:
      print PREFIX+"actuator %s need Shape Action Playback of type property" % \
          act.name
      errors = True
    if act.propName != 'p'+act.name:
      print PREFIX+"actuator %s need Shape Action property '%s' not '%s'" % (
        act.name, 'p'+act.name, act.propName)
      errors = True
  if owner.has_key('pskB') and not (
    G.getCurrentScene().lights.has_key('OBBlush_R') and
    G.getCurrentScene().lights.has_key('OBBlush_L') ):
    print PREFIX+"AU skB enabled, but Blush_R or Blush_L light(s) missing."
    errors = True
  return errors

def initialize(server):
  """Initialiazes and configures facial subsystem (blender specifics...)"""
  global INFO_PERIOD

  print "--- loaded blender backend from", __file__

  # get driven objects
  objs = G.getCurrentScene().objects
#  print "Blender file objects:"
  for obj_name in REQUIRED_OBJECTS:
    if OBJ_PREFIX+obj_name not in objs:
      return fatal("Object '%s' not found in blender scene" % obj_name)
#    print "%s, props: %s" % (obj_name, 
#                             objs[OBJ_PREFIX+obj_name].getPropertyNames())
    setattr(G, obj_name, objs[OBJ_PREFIX+obj_name])

  # set available Action Units from the blender file (Blender Shape Actions)
  cont = G.getCurrentController()
  owner = cont.owner
  acts = [act for act in cont.actuators if
          not act.name.startswith('-') and act.action]
  if check_defects(owner, acts):
    return fatal("Errors found in the .blend file must be addressed.")

  # properties must be set to 'head', 'tongue' and 'Skeleton'.
  # BEWARE to not set props to these objects before this line, or they will be
  # included here.
  objects = [owner] + [ getattr(G,name) for name in REQUIRED_OBJECTS ]
  aiov = [(pAU[1:], obj[pAU]/SH_ACT_LEN, obj.name[2:], pAU[1:] in VALID_AUs) for
          obj in objects for pAU in obj.getPropertyNames()]
  aiov.sort(key=lambda x: x[0])
  AUs, init_vals, objs, validated = zip(*aiov)
  invalids = [ "%s (object %s)" % (AUs[i],objs[i]) for i in range(len(AUs)) if
               not validated[i] ]
  if invalids:
    print (PRE_WRN+'\nthe following detected propert%s are invalid: %s' %
           (len(invalids)>1 and 'ies' or 'y', ', '.join(invalids)))
#    return False

  if not server.set_available_AUs(AUs):
    return fatal('Check your .blend file for bad property names.')

  # load axis limits for the Skeleton regardless of the configuration: if the
  # spine mod is loaded (origin head), no spine AU should be processed here.
  # blender might issue a warning here, nvm as we add a member, not access it.
  G.Skeleton['limits'] = server.SW_limits

  if owner.has_key('pskB'):
    G.BS = (G.getCurrentScene().lights[OBJ_PREFIX+'Blush_L'] ,
            G.getCurrentScene().lights[OBJ_PREFIX+'Blush_R'] )

  # ok, startup
  G.initialized = True
  G.info_duration = 0
  G.setLogicTicRate(MAX_FPS)
  G.setMaxLogicFrame(1)       # relative to rendering
  import Rasterizer
  print PRE_NFO+"Material mode:",['TEXFACE_MATERIAL','MULTITEX_MATERIAL',
                                  'GLSL_MATERIAL'][Rasterizer.getMaterialMode()]
  cam = G.getCurrentScene().active_camera
  if G.CONFIG["verbosity"].startswith("DEBUG"):
    INFO_PERIOD = None
  if (G.CONFIG.has_key('use_projMat') and G.CONFIG['use_projMat'] and
      G.CONFIG.has_key('proj_matrix')):
    try:
      cam.projection_matrix = G.CONFIG['proj_matrix']
    except StandardError as e:
      print PRE_ERR+"Couldn't set projection matrix (%s)" % e
  print PRE_NFO+"camera: lens %s\nview matrix: %s\nproj matrix: %s" % (
    cam.lens, cam.modelview_matrix, cam.projection_matrix)
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
    return [ [cos(z),        -sin(z),         0],
             [cos(x)*sin(z), cos(x)*cos(z),-sin(x)],
             [sin(x)*sin(z), sin(x)*cos(z), cos(x)] ]

  srv = G.face_server
  cont = G.getCurrentController()
  eyes_done, spine_done = False, False
  time_diff = time.time() - G.last_update_time

  srv.AUs.update_time(time_diff)
  for au, values in srv.AUs.iteritems():
    nval = values[VAL]

    #TODO: profiling, then figure out if we need a quicker switch method

    if au.startswith('6'):
      if eyes_done:                                     # all in one pass
        continue
      ax  = -srv.AUs['63.5'][VAL]               # Eye_L: character's left eye.
      G.eye_L.orientation = get_orientation_XZ(ax,srv.AUs['61.5L'][VAL])
      G.eye_R.orientation = get_orientation_XZ(ax,srv.AUs['61.5R'][VAL])
      eyes_done = True
    elif au == "ePS":
      G.eye_L['pePS'] = nval * SH_ACT_LEN
      G.eye_R['pePS'] = nval * SH_ACT_LEN 

    elif au.startswith('T'):
      pass
    #   if au[-1] == '0':
    #     cont.owner['p'+au] = SH_ACT_LEN * nval
    #     cont.activate(cont.actuators[au])
    #   else:
    #     a_min, a_max = G.Skeleton.limits[au]
    #     a_bound = nval < 0 and a_min or a_max
    #     G.Skeleton['p'+au] = (abs(nval)/a_bound +1) * SH_ACT_LEN/2

    elif au.startswith('9'):
      #TODO: negative nvals
      (au[-1] in 'XYZ' and G.Skeleton or G.tongue)['p'+au] = SH_ACT_LEN * nval

    elif au.startswith('5'):
      pass
    #   if float(au) <= 55.5:                             # pan, tilt, roll
    #     a_min, a_max = G.Skeleton.limits[au]
    #     a_bound = nval < 0 and a_min or a_max
    #     G.Skeleton['p'+au] = (abs(nval)/a_bound +1) * SH_ACT_LEN/2

    elif au == '26':
      # TODO: try with G.setChannel ?
      G.Skeleton['p26'] = SH_ACT_LEN * nval

    elif au[0].isdigit():
      cont.owner['p'+au] = SH_ACT_LEN * nval
      cont.activate(cont.actuators[au])

    elif au.startswith('sk'):
      if au.endswith('B'):
        G.BS[0].energy = nval * 3
        G.BS[1].energy = nval * 3

    else:
      a_min, a_max = G.Skeleton.limits[au]
      try:
        if nval >= 0:
          G.Skeleton['p'+au] = (nval/a_max + 1) * SH_ACT_LEN/2
        if nval < 0:
          G.Skeleton['p'+au] = (-nval/a_min +1) * SH_ACT_LEN/2
      except KeyError, e:
        print e

  G.last_update_time = time.time()
  G.info_duration += time_diff
  if INFO_PERIOD is not None and G.info_duration > INFO_PERIOD:
    print PRE_NFO+"BGE logic running at %sfps." % G.getLogicTicRate()
#    print "BGE physics running at %sfps." % G.getPhysicsTicRate()
    print PRE_NFO+"BGE graphics currently at %sfps." % G.getAverageFrameRate()
    G.info_duration = 0

#    print "------------------------ PROFILING --------------"
#    yappi.print_stats()


##
## Main loop: this bypasses ARAS.__init__.py as blender's executable or
##            blender-player is the entry point and calls this script itself.
##

#import yappi
def main():
  if not hasattr(G, "initialized"):
    try:
      import RAS
      if not RAS.loadnCheck_configuration("lighty"):
        exit(RAS.EXIT_CONFIG)
      G.CONFIG = RAS.conf.CONFIG
      G.server = RAS.initialize(THREAD_INFO, "lighty")
      G.face_server = G.server['face']

      cont = initialize(G.face_server)
      G.server.set_listen_timeout(0.001)      # tune it !
      G.server.start()
    except StandardError as e:
      fatal("initialization error: %s" % e)
    else:
      print '--- initialization OK ---'
      
#    yappi.start()

  else:
    # server handles channels explicitly
    try:
      if not THREADED_SERVER and not G.server.serve_once():
        raise StandardError('server returned an error')
      # update blender with fresh face data
      update()
    except KeyError, e:
      import logging
      logging.getLogger().warning("Unkown AU %s", e)
    except Exception,e:
      fatal("runtime error")
