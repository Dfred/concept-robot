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
# This module handles the Blender Game Engine.
# 
# MODULES IO:
#===========
# INPUT: - face
#
# A few things to remember:
#  * defining classes in toplevel scripts (like here) leads to scope problems (imports...)
#

import sys
import GameLogic
import comm


PREFIX="OB"
EYES_MAX_ANGLE=30
TIME_STEP=1/GameLogic.getLogicTicRate()
SH_ACT_LEN=50

def check_actuators(cont, acts):
    """Check required actuators are ok."""
    for act in acts:
        if not cont.owner.has_key('p'+act.name) or \
                act.mode != GameLogic.KX_ACTIONACT_PROPERTY:
#    property_act = cont.actuators['- property setter']
#            print ": Setting property 'p"+act.name+"'"
#            property_act.prop_name = 'p'+act.name
#            property_act.value = "0"
#            cont.activate(property_act)
            print "missing property: p"+act.name, "or bad Action Playback type"
            sys.exit(-1)


def set_eyelids(srv_face, time_step):
    """This function is for demo purposes only and do not use a proper interface
    """
    factor = float(GameLogic.eyes[0].orientation[2][1]) + .505
    GameLogic.getCurrentController().owner['p43L'] = 0.9-factor * SH_ACT_LEN
    GameLogic.getCurrentController().owner['p43R'] = 0.9-factor * SH_ACT_LEN
#    srv_face.conflict_solver.set_AU('gaze', '43', 0.9-factor, time_step)
    srv_face.conflict_solver.set_AU('gaze', '07', factor, time_step)


def initialize():
    # for init, imports are done on demand since the standalone BGE has issues.
    print "LIGHTBOT face synthesis, using python version:", sys.version

    import logging
    logging.basicConfig(level=logging.WARNING, format=comm.FORMAT)

    cont = GameLogic.getCurrentController()
    
    import conf
    missing = conf.load()
    if missing:
        raise Exception("WARNING: missing definitions %s in config file:" %\
                            (missing, conf.file_loaded))
    
    import face
    GameLogic.srv_face = comm.createServer(face.Face, face.FaceClient, conf.conn_face)
    # set available Action Units from the blender file (Blender Shape Actions)
    acts = [act for act in cont.actuators if
            not act.name.startswith('-') and act.action]
    GameLogic.srv_face.set_available_AUs([act.name for act in acts])
    # override actuators mode
    check_actuators(cont, acts)

    import threading
    threading.Thread(name='face', target=GameLogic.srv_face.serve_forever).start()
    # for demo purposes only
    objs = GameLogic.getCurrentScene().objects
    GameLogic.eyes = (objs[PREFIX+"eye-R"], objs[PREFIX+"eye-L"])
    GameLogic.empty_e = objs[PREFIX+"Empty-eyes"]
    GameLogic.empty_e['updated'] = False

    print "BGE logic running at", GameLogic.getLogicTicRate(), "fps."

    # ok, startup
    GameLogic.initialized = True	
    cont.activate(cont.actuators["- wakeUp -"])
    set_eyelids(GameLogic.srv_face, 0)


def update_face(srv_face, cont):
    for au, infos in srv_face.update(TIME_STEP):
        target_val, duration, elapsed, value = infos
#        print "setting property p"+au+" to value", value
        cont.owner['p'+au] = value * SH_ACT_LEN
        cont.activate(cont.actuators[au])
#TODO: check why 43R is a valid key, and what is the value ?
# print cont.owner['43R'], cont.owner['p43R']



#
# Main loop
#

def main():
    cont = GameLogic.getCurrentController()

    if not hasattr(GameLogic, "initialized"):
        try:
            initialize()
        except Exception, e:
            cont.activate(cont.actuators["- QUITTER"])
            raise

#   update eyes
    if GameLogic.empty_e['updated']:       # handle empty_e when moved
        set_eyelids(GameLogic.srv_face, TIME_STEP)
        GameLogic.empty_e['updated'] = False
    update_face(GameLogic.srv_face, cont)
