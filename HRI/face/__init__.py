#!/usr/bin/python

#
# FACE MODULE
#
# This module handles motion of the facial features.
# 
# MODULES IO:
#===========
# INPUT: - vision (eye orientation for eyelid position) [event]
#        - affect (facial expressions) [event]
#        - planner (..eventually)
#

import sys, random

import asyncore
import logging

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger("face-srv")

import comm
import conf


BLINK_PROBABILITY=0.0
BLINK_DURATION=1        # in seconds

class FaceClient(comm.RemoteClient):
    """Remote connection handler: protocol parser."""

    def cmd_AU(self, argline):
        """if empty, returns current values. Otherwise, set them."""
        """argline: AU_name  target_value  duration"""
        if len(argline):
            try:
                au_name, value, duration = argline.split()[:3]
                self.server.set_AU(au_name, float(value), float(duration))
            except Exception, e:
                LOG.warning("[AU] bad argument line:'%s', caused: %s" %
                            (argline,e) )
        else:
            self.send_msg("AU ",str(self.server.focus))

    def cmd_f_expr(self, argline):
        # TODO: rewrite player to get rid of this function
        """argline: facial expression id + intensity + duration.
        That function is for the humanPlayer (ie. would eventually disappear)
        """
        try:
            self.server.set_f_expr(*argline.split())
        except Exception:
            LOG.warning("[f_expr] bad argument line:'%s', caused:" % argline)
            raise

    def cmd_blink(self, argline):
        """argline: duration of the blink in seconds."""
        try:
            self.server.do_blink(float(argline))
        except Exception, e:
                LOG.warning("[blink] bad argument line:'%s', caused: %s" %
                            (argline,e) )

    def cmd_shutdown(self, args):
        """args: unused."""
        self.server.shutdown()



class Face(comm.BasicServer):
    """Main facial feature animation module - server"""
    """
    Also designed to maintain consistent muscle activation.
    This class holds all AU values, so you can also import this module.
    AU are normalized: 0 should/may be AU streched to an extreme, 1 to the other
    Resetting an AU would override the unfinished motion, starting from whenever
     the command has been received.
    """

    EYELIDS = ['43R', '43L', '07R', '07L']

    def __init__(self, addr_port, available_AUs):
        comm.BasicServer.__init__(self, FaceClient)
        self.listen_to(addr_port)
        self.blink_p = BLINK_PROBABILITY
        self.AUs = {}
        for act in available_AUs:
            self.AUs[act.name] = [0]*4  # target_val, duration, elapsed, value
        LOG.info("Available AUs: %s" % sorted(self.AUs.keys()))
        self.do_blink(0)
        LOG.info("Face started")

    def set_AU(self, name, target_value, duration):
        """Set a target value for a specific AU"""
        try:
            self.AUs[name][:3] = target_value, duration, 0
        except KeyError:
            if len(name) != 2:
                raise Exception('AU %s is not defined' % name)
            self.AUs[name+'R'][:3] = target_value, duration, 0
            self.AUs[name+'L'][:3] = target_value, duration, 0
            LOG.debug("set AU[%sR/L]: %s" % (name, self.AUs[name+'R']))
        else:
            LOG.debug("set AU[%s]: %s" % (name, self.AUs[name]))

    def set_f_expr(self, id, target, duration):
        """Set a facial expression."""
        #TODO: this is indeed way too simple...
        sets={ "raised_brows": ('01', '02'),
               "furrowed_brows": ('04'),
               "squint": ('04', '10'),
               "smile": ('07', '10', '12', '25'),
               "agreement_chin": ('17'),
               "begrudging_acceptance" : ('02R', '17'),
               "neutral": ('01','02','04',      # leave eyelids
                           '09','10','12','15','16','17','20','25'), #18
               "thought" : ('02', '15', '17'),
               "understanding" : ('07', '09', '12', '16'),
               "misunderstanding" : ('02', '04', '07', '09', '15', '16'), #18
               "unsure_understanding" : ('02', '09', '20')
               }
        for au in sets[id]:
            self.set_AU(au, float(target), float(duration))

    def set_blink_probability(self, p):
        self.blink_p = p

    def do_blink(self, duration):
        """set AUs to create a blink of any duration"""
        LOG.debug("blink: %ss." % duration)
        self.AUs["43R"][1:] =  duration, 0, .8
        self.AUs["07R"][1:] =  duration, 0, .2
        self.AUs["43L"][1:] =  duration, 0, .8
        self.AUs["07L"][1:] =  duration, 0, .2

    def update(self, time_step):
        """Update AU values."""
        if self.blink_p > random.random():
            self.do_blink(BLINK_DURATION)
        #TODO: use motion dynamics
        for id,info in self.AUs.iteritems():
            target, duration, elapsed, val = info
            if val == target or elapsed > duration:
                continue        # let self.AUs[id] be reset on next command

            factor = not duration and 1 or elapsed/duration
            self.AUs[id][2:] = elapsed+time_step, val + (target - val)*factor


if __name__ == '__main__':
    try:
        server = Face(conf.conn_face)
    except UserWarning, err:
        comm.LOG.error("FATAL ERROR: %s (%s)", sys.argv[0], err)
        exit(-1)
    while server.is_readable:
        comm.loop(5, count=1)
    LOG.info("Face done")


###
#
# Blender part
#
###
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
    #TODO: move this to gaze module (which should update the face module)
    factor = float(GameLogic.eyes[0].orientation[2][1]) + .505
    srv_face.set_AU('43R', 0.9-factor, time_step)
    srv_face.set_AU('43L', 0.9-factor, time_step)
    srv_face.set_AU('07R', factor, time_step)
    srv_face.set_AU('07L', factor, time_step)


def initialize():
    # for init, imports are done on demand since the standalone BGE has issues.
    print "LIGHTBOT face synthesis, using python version:", sys.version

    import logging
    logging.basicConfig(level=logging.WARNING, format=comm.FORMAT)
    
    objs = GameLogic.getCurrentScene().objects
    GameLogic.eyes = (objs[PREFIX+"eye-R"], objs[PREFIX+"eye-L"])
    GameLogic.empty_e = objs[PREFIX+"Empty-eyes"]
    GameLogic.empty_e.updated = False
    
    cont = GameLogic.getCurrentController()
    
    import conf
    missing = conf.load()
    if missing:
        raise Exception("WARNING: missing definitions %s in config file:" %\
                            (missing, conf.file_loaded))
        
    import gaze
    GameLogic.srv_gaze = gaze.Gaze(conf.conn_gaze)
    
    import face
    # make sure we have the same Action Units (Blender Shape Actions)
    acts = [act for act in cont.actuators if
            not act.name.startswith('-') and act.action]
    GameLogic.srv_face = face.Face(conf.conn_face, acts)
    # override actuators mode
    check_actuators(cont, acts)

    import affect
    #XXX: faster way: disallow autoconnect and update face directly.
    GameLogic.srv_affect = affect.Affect(conf.conn_affect, True)

    # ok, startup
    GameLogic.initialized = True	
    cont.activate(cont.actuators["- wakeUp -"])
    set_eyelids(GameLogic.srv_face, 0)

	

def update_eyes(srv_gaze):
    """To get a smooth movement (just linear), we start the eye movement,
        next iteration shall continue."""

    if GameLogic.empty_e.updated:       # handle empty_e when moved
        GameLogic.empty_e.updated = False
        srv_gaze.set_focus(GameLogic.empty_e.localPosition)
    else:                               # or when commands were sent to server
        srv_gaze.update(TIME_STEP)

    if not srv_gaze.changed:
        return
    elif srv_gaze.changed == 'f':   # focus
        GameLogic.empty_e.worldPosition = srv_gaze.focus
    elif srv_gaze.changed == 'o': # orientation
        import Mathutils
        o_angle, o_vect = srv_gaze.orientation[1:]
        # angle is normalized, we need it in degrees here, +
        #  see TODO: eye texture orientation.
        if o_angle == .0:
            o_vect = (.0,.0,.0001)
        oMatrix = Mathutils.RotationMatrix(EYES_MAX_ANGLE*o_angle-180, 3, "r",
                                           Mathutils.Vector(*o_vect))
        GameLogic.eyes[0].setOrientation(oMatrix)
        GameLogic.eyes[1].setOrientation(oMatrix)
        #DBG: print "L eye orientation now:", GameLogic.eyes[0].getOrientation()
    set_eyelids(GameLogic.srv_face, 0)


def update_face(srv_face, cont):
    srv_face.update(TIME_STEP)
    for au, infos in srv_face.AUs.iteritems():
        target_val, duration, elapsed, value = infos
#        print "setting property p"+au+" to value", value
        cont.owner['p'+au] = value * 50
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
            print "exception received:",e
            cont.activate(cont.actuators["- QUITTER"])
	
    comm.loop(.01, count=1) # block for max 10ms and 1 packet

    own = cont.owner
    srv_gaze = GameLogic.srv_gaze
    srv_face = GameLogic.srv_face

    #if srv_gaze.connected:
    update_eyes(srv_gaze)

    #if srv_face.connected:
    update_face(srv_face,cont)
