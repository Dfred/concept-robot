#!/usr/bin/python

#
# This module implements the Katana-400-6M backend for the spine module.
# No protocol change so there's no need to override SpineClient.
#
# Axis are independant: an axis can be controlled (rigid) while others not.
#
import math

import logging
LOG = logging.getLogger(__package__)

try:
    import KNI
except ImportError:
    raise ImportError('The KNI module is not included in this release and shall'
                      ' be built from source.')
from spine import SpineError, SpineBase


def showTPos(tpos):
    print 'rotation: (phi/X:{0.phi}, theta/Y:{0.theta}, psi/Z:{0.psi})'\
        '- position: (X:{0.X}, Y:{0.Y}, Z:{0.Z})'.format(tpos)

class SpineHW(SpineBase):
    """Spine implementation for the Katana400s-6m"""

    # The configuration file has other references, but this one maximizes 
    #  the range of movements from origin (based on ideal pose for our setup).
    # Another approach would have been to use these references and use offsets.

    AXIS_LIMITS = ( None,                               # indices like KNI
        #  min    max  mean(0rad)   factor
        (-18300, 31000,  6350, -12750/(math.pi/2)),
        (-31000,  5900, -9850, -23900/(math.pi/2)),     # real 0: -21800
        (-31000,  1900, -2450,  11850/(math.pi/2)),     # real 0: -14300
        ( 14700, 27500, 21100,  12800/(math.pi/2)),     # neck x
        (    50, 12950,  6500,  12900/(math.pi/2)),     # neck y
        (-15600,  -400, -8000,  12750/(math.pi/2)) )    # neck z

    SPEED_LIMITS = ( (0,255), (1,2) )   # 1: long accel, 2: short accel
    

#POSE_REST = [23500, 5600, 1800, 25100, 6500, 6900]     
# vertical, calibrate OK but unstable
    # POSE_REST = ( AXIS_LIMITS[1][2],
    #               -18000, -15600, 30900,
    #               AXIS_LIMITS[5][2],
    #               AXIS_LIMITS[6][2] )
# folded, but calibration from this position makes it collide slightly
    POSE_REST = ( AXIS_LIMITS[1][2],
                  5600, 1800, 25100,
                  AXIS_LIMITS[5][2],
                  AXIS_LIMITS[6][2] )

    @staticmethod
    def rad2enc(axis, rad):
        info = SpineHW.AXIS_LIMITS[axis]
        e = int(info[3]*rad) + info[2]
        f = min(max(info[0], e), info[1])
        if e != f:
            LOG.warning('axis %i limited value %i to %i %s', axis,e,f,info[:2])
        return f

    @staticmethod
    def enc2rad(axis, enc):
        info = SpineHW.AXIS_LIMITS[axis]
        return 1.0/info[3]*(enc - info[2])


    def __init__(self):
        SpineBase.__init__(self)
        self.has_torso = True
        self._speed = 50
        self._accel = 1                 
        self._tolerance = 50
        #TODO: fill self.neck_info and self.torso_info
        init_arm()
        self.switch_on()

    def get_speed(self):
        return float(self._speed)/self.SPEED_LIMITS[0][1]

    def set_speed(self, value):
        max_speed = self.SPEED_LIMITS[0][1]
        self._speed = min(int(value*max_speed), max_speed)

    def set_accel(self, value):
        """Set normalized values, relative to hardware capabilities."""
        self._accel = min(value, self.SPEED_LIMITS[1][1])

    def get_tolerance(self, tolerance):
        """In radians, needs to convert to encoder value.
        0 means wait until reached. Not consistent.."""
        self._tolerance = tolerance

    def get_torso_info(self):
        """Returns TorsoInfo instance"""
        self._torso_info.rot= self.round([SpineHW.enc2rad(2,KNI.getEncoder(2)),
                                          0.0,
                                          SpineHW.enc2rad(1,KNI.getEncoder(1))])
        return self._torso_info

    def get_neck_info(self):
        """Returns NeckInfo instance"""
        # XXX: we are not using the same reference: create a mapping function
#        tp = KNI.TPos()
#        KNI.getPosition(tp)
#        self._neck_info.pos= self.round([tp.X, tp.Y, tp.Z])
#        self._neck_info.rot= self.round([tp.phi, tp.theta, tp.psi])

        self._neck_info.rot = self.round( \
            [ SpineHW.enc2rad(i, KNI.getEncoder(i)) for i in \
                  xrange(4, len(self.AXIS_LIMITS)) ])
        return self._neck_info

    def switch_on(self):
        """Mandatory 1st call after hardware is switched on.
        Starts calibration if needed.
        """
        if False in self.check_motors():
            self.calibrate()
        self.switch_auto()
        self.set_neck_orientation((0,0,0))
        self.set_torso_orientation((0,0,0))

    def switch_off(self):
        """Set the robot for safe hardware switch off."""
        self.pose_rest()
        self.switch_manual()
        
    def switch_manual(self):
        """WARNING: Allow free manual handling of the robot. ALL MOTORS OFF!"""
        if KNI.allMotorsOff() == -1:
            raise SpineError('failed to switch motors off')
        self._motors_on = False

    def switch_auto(self):
        """Resumes normal (driven-mode) operation of the robot."""
        if not self._motors_on and KNI.allMotorsOn() == -1:
            raise SpineError('failed to switch motors on')
        self._motors_on = True

    def calibrate(self):
        """Mandatory call upon hardware switch on. Also can be use to test 
         calibration procedure."""
        # TODO: use another sequence so that the arm does not collide itself
        if KNI.calibrate(0) == -1:
            raise SpineError('failed to calibrate hardware')

    def check_motors(self):
        """Test each motor status"""
        motors = [None]*len(self.AXIS_LIMITS)
        for i in xrange(1, len(self.AXIS_LIMITS)):
            LOG.debug('checking motor %i', i)
            enc = KNI.getEncoder(i)
            motors[i] = KNI.moveMot(i, enc, self._speed, self._accel) != -1
        return motors

    def reach_pose(self, pose):
        """This pose is defined so that the hardware is safe to switch-off.
        pose: a *list* of encoder values for each spine axis
        """
        # no wait
        if KNI.moveToPosEnc(*pose+[self._speed, self._accel, self._tolerance]+
                             [True]) == -1:
            raise SpineError('failed to reach pose')

    def pose_rest(self):
        self.reach_pose(list(self.POSE_REST))

    def pose_average(self):
        """This pose is defined according to the mean value of each axis.
        Use this function to pose the robot so it has an even range of possible
        movements."""
        self.reach_pose([(mn+mx)/2 for mn,mx,orig,fac in self.AXIS_LIMITS[1:]])

    def set_neck_orientation(self, xyz, wait=True):
        """Absolute orientation:
        Our own version since the IK is useless (ERROR: No solution found)"""
        encs = [ (4+i, SpineHW.rad2enc(4+i, v)) for i,v in enumerate(xyz) ]
        for axis, enc in encs:
            LOG.debug('moving axis %i to encoder %i', axis, enc)
            if KNI.moveMot(axis, enc, self._speed, self._accel) == -1:
                raise SpineError('failed to reach rotation (axis %i)' % axis)
        if not wait:
            return
        for axis, enc in encs:
            if KNI.waitForMot(axis, enc, self._tolerance) != 1:
                raise SpineError('failed to wait for motor %i' % (axis))

    def set_torso_orientation(self, xyz, wait=True):
        """Absolute orientation:
        Our own version since the IK is useless (ERROR: No solution found)"""
        encs = [ (1, SpineHW.rad2enc(1, xyz[2])),
                 (2, SpineHW.rad2enc(2, xyz[0])),
                 (3, SpineHW.rad2enc(3, 0)) ]
        for axis, enc in encs:
            LOG.debug('moving axis %i to encoder %i', axis, enc)
            if KNI.moveMot(axis, enc, self._speed, self._accel) == -1:
                raise SpineError('failed to reach rotation (axis %i)' % axis)
        if not wait:
            return
        for axis, enc in encs:
            if KNI.waitForMot(axis, enc, self._tolerance) != 1:
                raise SpineError('failed to wait for motor %i' % axis)

    def set_neck_rot_pos(self, rot_xyz=None, pos_xyz=None):
        """Absolute orentation and position using KNI IK"""
        if not self._motors_on or (rot_xyz == pos_xyz == None):
            LOG.info('motors are %s [rot: %s\t pos: %s]', self._motors_on,
                     rot_xyz, pos_xyz) 
            return False
        tp = KNI.TPos()
        KNI.getPosition(tp)
        if rot_xyz:
            tp.phy, tp.theta, tp.psi = rot_xyz
        if pos_xyz:
            tp.X, tp.Y, tp.Z = pos_xyz
        ret = KNI.moveToPos(tp, self._speed, self._accel)
        KNI.getPosition(tp)
        if ret == -1:
            raise SpineError('failed to reach rotation/position')
        return True


def init_arm():
    # Just initializes the arm
    import os.path
    import conf
    KatHD400s_6m = __path__[0]+os.path.sep+"katana6M90T.cfg"
    LOG.info('trying to connect to Katana400s-6m on %s', conf.spine_hardware)
    if KNI.initKatana(KatHD400s_6m, conf.spine_hardware) == -1:
        raise SpineError('configuration file not found or'
                         ' failed to connect to hardware', KatHD400s_6m)
    else:
        print 'loaded config file', KatHD400s_6m, 'and now connected'
