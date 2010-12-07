#!/usr/bin/python

# Lighthead-bot programm is a HRI PhD project at the University of Plymouth,
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
import sys, time
from math import cos, sin, pi
import GameLogic as G

DEBUG_MODE = False #True
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

FACE = 'face'

OBJ_PREFIX = "OB"
CTR_SUFFIX = "#CONTR#"
SH_ACT_LEN = 50
EXTRA_PROPS = ['61.5L', '61.5R', '63.5']        # eyes
RESET_ORIENTATION = ([1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0])
INFO_PERIOD = 0

def fatal(error):
    print '*** Fatal Error ***'
    import traceback; traceback.print_exc()
    shutdown(G.getCurrentController())


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


def shutdown(cont):
    """Shutdown server and other clean-ups"""
    cont.activate(cont.actuators["- QUITTER"])
    #We check if there is a valid "server" object because its possible that 
    #we were unable to create it, and therefore we are shutting down
    if hasattr(G, "server"):
      G.server.shutdown()
    else:
      sys.exit(1)
    sys.exit(0)


def initialize():
    """Initialize connections and configures facial subsystem"""
    import sys

    # for init, imports are done on demand
    print "LIGHTHEAD Facial Animation System, python version:", sys.version
    print "loaded module from", __path__[0]

    # look for and load a file called lightHead.conf
    # set indirection with environment variable conf.NAME (eg. LIGHTHEAD_CONF)
    import conf
    conf.NAME='lightHead.conf'
    missing = conf.load()

    import comm
    if DEBUG_MODE:
        print 'setting debug mode'
        # set system-wide logging level
        comm.logging.basicConfig(level=comm.logging.DEBUG,format=comm.LOGFORMAT)
    else:
        comm.set_default_logging()

    from lightHead_server import lightHeadServer, lightHeadHandler
    G.server = comm.create_server(lightHeadServer, lightHeadHandler,
                                  conf.conn_face, THREAD_INFO)
    G.server.create_protocol_handlers()

    # for eye orientation.
    objs = G.getCurrentScene().objects
    G.eyes = (objs[OBJ_PREFIX+"eye-R"], objs[OBJ_PREFIX+"eye-L"])

    # for jaw opening
    G.jaw = objs[OBJ_PREFIX+"jaw"]

    # set available Action Units from the blender file (Blender Shape Actions)
    cont = G.getCurrentController()
    owner = cont.owner
    acts = [act for act in cont.actuators if
            not act.name.startswith('-') and act.action]
    try:
        check_defects(owner, acts)
    except Exception, e:
        fatal(e)
    # all properties must be set to the face mesh.
    # TODO: p26 is copied on the 'jaw' bone too, use the one from face mesh.
    G.server[FACE].set_available_AUs([n[1:] for n in owner.getPropertyNames()])

    # ok, startup
    G.initialized = True	
    G.setMaxLogicFrame(1)       # relative to rendering
    G.setLogicTicRate(MAX_FPS)
    import Rasterizer
#    Rasterizer.enableMotionBlur( 0.65)
    Rasterizer.setBackgroundColor([.0, .0, .0, 1.0])
    print "Material mode:", ['TEXFACE_MATERIAL','MULTITEX_MATERIAL ','GLSL_MATERIAL '][Rasterizer.getMaterialMode()]

    cont.activate(cont.actuators["- wakeUp -"])
    G.last_update_time = time.time()    


def update(faceServer, eyes, time_diff):
    """
    """
    global INFO_PERIOD

    cont = G.getCurrentController()
    eyes_done = False

    # threaded server is thread-safe
    for au, value in faceServer.update(time_diff):
        if au[0] == '6':        # yes, 6 is an eye prefix !
            if eyes_done:
                continue
            # The model is supposed to look towards negative Y values
            # Also Up is positive Z values
            ax  = -faceServer.get_AU('63.5')[3]
            az0 = faceServer.get_AU('61.5R')[3]
            az1 = faceServer.get_AU('61.5L')[3]
            eyes[0].localOrientation = [
                [cos(az0),        -sin(az0),         0],
                [cos(ax)*sin(az0), cos(ax)*cos(az0),-sin(ax)],
                [sin(ax)*sin(az0), sin(ax)*cos(az0), cos(ax)] ]
            eyes[1].localOrientation = [
                [cos(az1),        -sin(az1),          0],
                [cos(ax)*sin(az1), cos(ax)*cos(az1),-sin(ax)],
                [sin(ax)*sin(az1), sin(ax)*cos(az1), cos(ax)] ]
            eyes_done = True
        elif au == '26':
            # TODO: try with G.setChannel
            G.jaw['p26'] = SH_ACT_LEN*value    # see always sensor in .blend
        else:
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
import select

def main():
    if not hasattr(G, "initialized"):
        try:
            initialize()
            G.server.set_listen_timeout(0.001)
            G.server.start()
        except Exception, e:
            fatal(e)
    else:
        if not THREADED_SERVER:
            # server handles channels explicitly
            if not G.server.serve_once():
                print 'server returned an error'
                G.server.shutdown()
        # update blender with fresh face data
        update(G.server[FACE], G.eyes, time.time() - G.last_update_time)
        G.last_update_time = time.time()
