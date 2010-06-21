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

import sys
import GameLogic
import comm


PREFIX="OB"
TIME_STEP=1/GameLogic.getLogicTicRate()
SH_ACT_LEN=50
EYES_AU = ['61.5L', '61.5R', '63.5']

def check_actuators(cont, acts):
    """Check if actuators have their property set and their mode ."""
    for act in acts:
        if not cont.owner.has_key('p'+act.name) or \
                act.mode != GameLogic.KX_ACTIONACT_PROPERTY:
            print "missing property: p"+act.name, "or bad Action Playback type"
            sys.exit(-1)


def initialize():
    """Initialize connections and configures facial subsystem"""

    # for init, imports are done on demand
    print "LIGHTHEAD face synthesis, using python version:", sys.version
    print "loaded module from", __path__[0]

    import logging
    logging.basicConfig(level=logging.WARNING, format=comm.FORMAT)

    import conf
    missing = conf.load(raise_exception=False)
    
    import face
    GameLogic.srv_face = comm.createServer(face.Face, face.FaceClient,
                                           conf.conn_face)
    # for eye orientation.
    objs = GameLogic.getCurrentScene().objects
    GameLogic.eyes = (objs[PREFIX+"eye-R"], objs[PREFIX+"eye-L"])

    # set available Action Units from the blender file (Blender Shape Actions)
    cont = GameLogic.getCurrentController()
    acts = [act for act in cont.actuators if
            not act.name.startswith('-') and act.action]
    check_actuators(cont, acts)
    GameLogic.srv_face.set_available_AUs([act.name for act in acts]+EYES_AU)

    # ok, startup
    GameLogic.initialized = True	
    cont.activate(cont.actuators["- wakeUp -"])
    print "BGE logic running at", GameLogic.getLogicTicRate(), "fps."


def update(srv_face, cont, eyes):
    for au, infos in srv_face.update(TIME_STEP):
        target_val, duration, elapsed, value = infos
        if au == '63.5':
            eyes[0].applyRotation([target_val, 0,0], False)
            eyes[1].applyRotation([target_val, 0,0], False)
        elif au == '61.5L':
            eyes[0].applyRotation([0,target_val,0], False)
        elif au == '61.5R':
            eyes[1].applyRotation([0,target_val,0], False)
        else:
            cont.owner['p'+au] = value * SH_ACT_LEN
            cont.activate(cont.actuators[au])



#
# Main loop
#

def main():
    cont = GameLogic.getCurrentController()

    if not hasattr(GameLogic, "initialized"):
        try:
            initialize()

            import threading
            threading.Thread(name='face',
                             target=GameLogic.srv_face.serve_forever).start()
        except Exception, e:
            cont.activate(cont.actuators["- QUITTER"])
            raise

    update(GameLogic.srv_face, cont, GameLogic.eyes)
