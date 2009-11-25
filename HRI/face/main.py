#
# A few things to remember:
#  * defining classes in toplevel scripts (like here) leads to scope problems (imports...)
#

import GameLogic
import comm


PREFIX="OB"
EYES_MAX_ANGLE=30
TIME_STEP=1/GameLogic.getLogicTicRate()
	
def initialize():
    # for init, imports are done on demand since the standalone BGE has issues.
    import sys
    print "LIGHTBOT face synthesis, using python version:", sys.version

    import logging
    logging.basicConfig(level=logging.WARNING, format=comm.FORMAT)
    
    objs = GameLogic.getCurrentScene().objects
    GameLogic.eyes = (objs[PREFIX+"eye-R"], objs[PREFIX+"eye-L"])
    GameLogic.empty_e = objs[PREFIX+"Empty-eyes"]
    GameLogic.empty_e.updated = False
    
    cont = GameLogic.getCurrentController()
    
    import conf
    import gaze
    GameLogic.srv_gaze = gaze.Gaze(conf.gaze_addr)
    
    import face
    # make sure we have the same activables
    acts = [act for act in cont.actuators if
            not act.name.startswith('-') and act.action]
    GameLogic.srv_face = face.Face(conf.face_addr, acts)
    # override actuators mode
    check_actuators(cont, acts)

    # ok, startup
    GameLogic.initialized = True	
    cont.activate(cont.actuators["- wakeUp -"])

	
def check_actuators(cont, acts):
    """Check required actuators are ok."""
    for act in acts:
        act.mode = GameLogic.KX_ACTIONACT_PROPERTY
        act.framePropName = act.name[:3]
        if not cont.owner.has_key('p'+act.name):
#    property_act = cont.actuators['- property setter']
#            print ": Setting property 'p"+act.name+"'"
#            property_act.prop_name = 'p'+act.name
#            property_act.value = "0"
#            cont.activate(property_act)
            print "missing property: p"+act.name


def update_eyes(srv_gaze):
    """To get a smooth movement (just linear), we start the eye movement,
        next iteration shall continue."""
    if GameLogic.empty_e.updated:
        srv_gaze.set_focus(GameLogic.empty_e.localPosition)
        factor = float(GameLogic.eyes[0].orientation[2][1]) + .505
        GameLogic.srv_face.set_AU('43R', 0.9-factor, TIME_STEP)
        GameLogic.srv_face.set_AU('43L', 0.9-factor, TIME_STEP)
        GameLogic.srv_face.set_AU('07R', factor, TIME_STEP)
        GameLogic.srv_face.set_AU('07L', factor, TIME_STEP)
        GameLogic.empty_e.updated = False
        return

    srv_gaze.update(TIME_STEP)
    if srv_gaze.changed == 'f':   # focus
        GameLogic.empty_e.worldPosition = srv_gaze.focus
    elif srv_gaze.changed == 'o': # orientation
        import Mathutils
        o_angle, o_vect = srv_gaze.orientation
        # angle is normalized, we need it in degrees here, +
        #  see TODO: eye texture orientation.
        if o_angle == .0:
            o_vect = (.0,.0,.0001)
        oMatrix = Mathutils.RotationMatrix(factor*EYES_MAX_ANGLE*o_angle-180,
                                           3, "r", Mathutils.Vector(*o_vect))
        GameLogic.eyes[0].setOrientation(oMatrix)
        GameLogic.eyes[1].setOrientation(oMatrix)
        print "eyes orientation set to ", GameLogic.eyes[0].getOrientation()


def update_face(srv_face, cont):
    srv_face.update(TIME_STEP)
    for au, infos in srv_face.AUs.iteritems():
        target_val, duration, elapsed, value = infos
        print "setting property", au, "to value", value
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
