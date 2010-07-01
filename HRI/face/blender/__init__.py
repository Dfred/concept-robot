#!/usr/bin/python

# Lighthead-bot programm is a HRI PhD project at
#  the University of Plymouth,
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
import time
from math import cos, sin, pi
import GameLogic as G

OBJ_PREFIX = "OB"
CTR_SUFFIX = "#CONTR#"
SH_ACT_LEN = 50
RESET_ORIENTATION = ([1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0])

def check_actuators(owner, acts):
    """Check if actuators have their property set and are in proper mode ."""
    for act in acts:
        if not owner.has_key('p'+act.name) or \
                act.mode != G.KX_ACTIONACT_PROPERTY:
            print "missing property: p"+act.name, "or bad Action Playback type"
            sys.exit(-1)

def initialize():
    """Initialize connections and configures facial subsystem"""
    import sys

    # for init, imports are done on demand
    print "LIGHTHEAD face synthesis, using python version:", sys.version
    print "loaded module from", __path__[0]

    import comm
    import conf
    missing = conf.load(raise_exception=False)
    
    import face
    G.srv_face = comm.createServer(face.Face, face.FaceClient,
                                           conf.conn_face)
    # for eye orientation.
    objs = G.getCurrentScene().objects
    G.eyes = (objs[OBJ_PREFIX+"eye-R"], objs[OBJ_PREFIX+"eye-L"])

    # for jaw opening
    G.jaw = objs[OBJ_PREFIX+"jaw"]
#    G.jaw_cont = G.jaw.controllers['c_open'+CTR_SUFFIX+'1']
#    G.jaw_act = G.jaw_cont.getActuator('a_open')

    # set available Action Units from the blender file (Blender Shape Actions)
    cont = G.getCurrentController()
    owner = cont.owner
    acts = [act for act in cont.actuators if
            not act.name.startswith('-') and act.action]
    check_actuators(owner, acts)
    G.srv_face.set_available_AUs([n[1:] for n in owner.getPropertyNames()])

    # ok, startup
    G.initialized = True	
    cont.activate(cont.actuators["- wakeUp -"])

    G.last_update_time = time.time()    
#    G.setMaxLogicFrame(1)       # relative to rendering
    G.setLogicTicRate(32.0)
    print "BGE logic running at", G.getLogicTicRate(), "fps."
    print "BGE physics running at", G.getPhysicsTicRate(), "fps."
    print "BGE graphics currently at", G.getAverageFrameRate(), "fps."
#    import Rasterizer
#    Rasterizer.enableMotionBlur( 0.65)


def update(srv_face, cont, eyes, time_diff):
    eyes_done = False
    for au, value in srv_face.update(time_diff):
        if au[0] == '6':        # yes, 6 is an eye prefix !
            if eyes_done:
                continue
            # The model is supposed to look towards negative Y values
            # Also Up is positive Z values
            ax  = -srv_face.get_AU('63.5')[3]
            az0 = srv_face.get_AU('61.5R')[3]
            az1 = srv_face.get_AU('61.5L')[3]
            eyes[0].worldOrientation = [
                [cos(az0),        -sin(az0),         0],
                [cos(ax)*sin(az0), cos(ax)*cos(az0),-sin(ax)],
                [sin(ax)*sin(az0), sin(ax)*cos(az0), cos(ax)] ]
            eyes[1].worldOrientation = [
                [cos(az1),        -sin(az1),          0],
                [cos(ax)*sin(az1), cos(ax)*cos(az1),-sin(ax)],
                [sin(ax)*sin(az1), sin(ax)*cos(az1), cos(ax)] ]
            eyes_done = True
        elif au == '26':
            # TODO: try with G.setChannel
            G.jaw['pJaw'] = SH_ACT_LEN*value    # see always sensor in .blend
        else:
            cont.owner['p'+au] = value * SH_ACT_LEN
            cont.activate(cont.actuators[au])


#TODO: write clean-up code
def shutdown():
    """Shutdown server and other clean-ups"""
    cont.activate(cont.actuators["- asleep -"])
    pass

#
# Main loop
#

def main():
    cont = G.getCurrentController()

    if not hasattr(G, "initialized"):
        try:
            initialize()

            import threading
            threading.Thread(name='face',
                             target=G.srv_face.serve_forever).start()
        except Exception, e:
            cont.activate(cont.actuators["- QUITTER"])
            raise
    
    update(G.srv_face, cont, G.eyes,
           time.time() - G.last_update_time)
    G.last_update_time = time.time()
