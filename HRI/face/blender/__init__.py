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

#
# FACE MODULE: blender backend
#
# This module uses the Blender Game Engine as a backend for animating LightHead.
# To make this work, you need to let the initialization routine list the AU you
#  support: define a property per AU in your .blend. Also, for most AUs you need
#  a Shape Action actuator which provides the relative basic facial animation.
#
# MODULES IO:
#===========
# INPUT: - face
#
# A few things to remember for integration with Blender (2.49):
#  * defining classes in toplevel scripts (like here) leads to scope problems
#
import sys, time, atexit
from math import cos, sin, pi

import GameLogic as G

MAX_FPS = 50

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
EXTRA_PROPS = ['61.5L', '61.5R', '63.5']        # eyes
RESET_ORIENTATION = ([1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0])
INFO_PERIOD = 0

def exiting():
    #We check if there is a valid "server" object because its possible that 
    #we were unable to create it, and therefore we are shutting down
    if hasattr(G, "server"):
      G.server.shutdown()

atexit.register(exiting)

def fatal(error):
    """Common function to gracefully quit."""
    print '*** Fatal Error ***', error
    import conf; conf.load()
    if hasattr(conf, 'DEBUG_MODE') and conf.DEBUG_MODE:
        import traceback; traceback.print_exc()
    shutdown(G.getCurrentController())

def shutdown(cont):
    """Finish animation and let atexit do the cleaning job"""
    cont.activate(cont.actuators["- QUITTER"])
    if hasattr(G, 'server'):
        sys.exit(0)
    sys.exit(1)
    # see exiting()

def check_defects(owner, acts):
    """Check if actuators have their property set and are in proper mode ."""
    keys = [ act.name for act in acts] + EXTRA_PROPS
    for name in keys:
        if not owner.has_key('p'+name):
            raise Exception('missing property p%s' % name)
    for act in acts :
        if act.mode != G.KX_ACTIONACT_PROPERTY:
            raise Exception('Actuator %s shall use Shape Action Playback of'
                            'type property' % act.name)
    return False

def initialize(server):
    """Initialiazes and configures facial subsystem (blender specifics...)"""
    print "loaded module from", __path__[0]

    # get driven objects
    objs = G.getCurrentScene().objects
    for obj_name in ('eye_L', 'eye_R', 'jaw', 'tongue'):
        try:
            setattr(G, obj_name, objs[OBJ_PREFIX+obj_name])
        except KeyError:
            try:
# WARNING: at least in python 2.6 capitalize and title docstrings are confused!
                setattr(G, obj_name, objs[OBJ_PREFIX+obj_name.title()])
            except KeyError, e:
                raise Exception('no object "%s" in blender file' % e[0][16:-18])

    # set available Action Units from the blender file (Blender Shape Actions)
    cont = G.getCurrentController()
    owner = cont.owner
    acts = [act for act in cont.actuators if
            not act.name.startswith('-') and act.action]
    check_defects(owner, acts)

    # all properties must be set to the face mesh.
    # TODO: p26 is copied on the 'jaw' bone too, use the one from face mesh.
    server.set_available_AUs([n[1:] for n in owner.getPropertyNames()])

    # ok, startup
    G.initialized = True	
    G.setMaxLogicFrame(1)       # relative to rendering
    G.setLogicTicRate(MAX_FPS)
    import Rasterizer
#    Rasterizer.enableMotionBlur( 0.65)
    Rasterizer.setBackgroundColor([.0, .0, .0, 1.0])
    print "Material mode:", ['TEXFACE_MATERIAL','MULTITEX_MATERIAL ','GLSL_MATERIAL '][Rasterizer.getMaterialMode()]
    G.last_update_time = time.time()    
    return cont


def update(faceServer, time_diff):
    """
    """
    global INFO_PERIOD
    from face import float_to_AUname

    cont = G.getCurrentController()
    eyes_done = False

    # threaded server is thread-safe
    for au, value in faceServer.update(time_diff):
        if int(abs(au/10)) == 6:# XXX: yes, 6 is an eye prefix (do better ?)
            if eyes_done:
                continue
            # The model is supposed to look towards negative Y values
            # Also Up is positive Z values
            ax  = -faceServer.get_AU( 63.5)[3]
            az0 =  faceServer.get_AU( 61.5)[3]
            az1 =  faceServer.get_AU(-61.5)[3]
            # No ACTION for eyes
            G.eye_L.localOrientation = [
                [cos(az0),        -sin(az0),         0],
                [cos(ax)*sin(az0), cos(ax)*cos(az0),-sin(ax)],
                [sin(ax)*sin(az0), sin(ax)*cos(az0), cos(ax)] ]
            G.eye_R.localOrientation = [
                [cos(az1),        -sin(az1),          0],
                [cos(ax)*sin(az1), cos(ax)*cos(az1),-sin(ax)],
                [sin(ax)*sin(az1), sin(ax)*cos(az1), cos(ax)] ]
            eyes_done = True
        elif au/10 == 9:        # XXX: yes, 9 is a tongue prefix (do better ?)
            G.tongue[au] = SH_ACT_LEN * value
        elif au == 26:
            # TODO: try with G.setChannel
            G.jaw['p26'] = SH_ACT_LEN * value    # see always sensor in .blend
        else:
            au = float_to_AUname[au]
            cont.owner['p'+au] = value * SH_ACT_LEN
            cont.activate(cont.actuators[au])

    INFO_PERIOD += time_diff
    if INFO_PERIOD > 5:
        print "--- RENDERING INFO ---"
        print "BGE logic running at", G.getLogicTicRate(), "fps."
#        print "BGE physics running at", G.getPhysicsTicRate(), "fps."
        print "BGE graphics currently at", G.getAverageFrameRate(), "fps."
        INFO_PERIOD = 0


#
# Main loop
#

def main():
    if not hasattr(G, "initialized"):
        try:
# standalone version:
#            import face, comm, conf; conf.load()
#            G.server = G.face_server = comm.create_server(face.Face_Server, face.Face_Handler, conf.mod_face, THREAD_INFO)
            import HRI
            G.server = HRI.initialize(THREAD_INFO)
            G.face_server = G.server['face']

            cont = initialize(G.face_server)
            G.server.set_listen_timeout(0.001)      # tune it !
            G.server.start()
        except:
            fatal("initialization error")
        cont.activate(cont.actuators["- wakeUp -"])
    else:
        if not THREADED_SERVER:
            # server handles channels explicitly
            if not G.server.serve_once():
                print 'server returned an error'
                G.server.shutdown()
        try:
            # update blender with fresh face data
            update(G.face_server, time.time() - G.last_update_time)
        except:
            import conf; conf.load()
            if hasattr(conf,'DEBUG') and conf.DEBUG:
                import pdb; pdb.post_mortem()
        G.last_update_time = time.time()
