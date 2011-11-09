#!/usr/bin/python

#
# This module implements the Katana-400-6M backend for the spine module.
# No protocol change so there's no need to override SpineClient.
#
# Axis are independant: an axis can be controlled (rigid) while others not.
#
import math

from utils import conf, get_logger
import LH_KNI_wrapper

__all__ = ['SpineHW']

LOG = get_logger(__package__)

if __name__ == '__main__':
  from utils import conf
  conf.set_name('lightHead')
  conf.load()
from RAS.spine import SpineError, SpineBase


def showTPos(tpos):
  print 'rotation: (phi/X:{0.phi}, theta/Y:{0.theta}, psi/Z:{0.psi})'\
        '- position: (X:{0.X}, Y:{0.Y}, Z:{0.Z})'.format(tpos)

class SpineHW(SpineBase):
  """Spine implementation for the Katana400s-6m"""

  POSES = {'rest' : None,                                   # safe rest position
           'zero' : None,                                   # all axis at 0rad.
           'avg'  : None,                                   # all at mid-range
           }

  def __init__(self):
    SpineBase.__init__(self)
    self.load_conf()
    self.has_torso = True
    self._speed = 50
    self._accel = 1
    self._tolerance = 50
    #TODO: fill self.neck_info and self.torso_info
    LOG.info('Trying to connect (%s:%s)', self.hardware_name, self.KNI_address)
    self.KNI = LH_KNI_wrapper.LHKNI_wrapper(self.KNI_cfg_file, self.KNI_address)
    self.switch_on()

  def load_conf(self):
    spine_conf = conf.ROBOT['mod_spine']
    try:
      self.hardware_name = spine_conf['backend']
    except:
      raise conf.LoadException("mod_spine has no 'backend' key")
    try:
      self.KNI_address = spine_conf['hardware_addr']
    except:
      raise conf.LoadException("mod_spine has no 'hardware_addr' key")
    try:
      hardware = conf.lib_spine[self.hardware_name]
    except:
      raise conf.LoadException("lib_spine has no '%s' key" %
                                 self.hardware_name)
    try:
      self.AXIS_LIMITS = hardware['AXIS_LIMITS']
    except:
      raise conf.LoadException("lib_spine['%s'] has no 'AXIS_LIMITS' key"%
                                self.hardware_name)
    SpineHW.POSES['zero'] = [0]*len(self.AXIS_LIMITS)
    SpineHW.POSES['avg'] = [(mn+mx)/2 for mn,mx,orig,fac in self.AXIS_LIMITS]
    try:
      SpineHW.POSES['rest'] = hardware['POSE_OFF']
    except:
      raise conf.LoadException("lib_spine['%s'] has no 'POSE_OFF' key" %
                                self.hardware_name)
    from os.path import dirname, sep
    self.KNI_cfg_file = dirname(__file__)+sep+"katana6M90T.cfg"

  def rad2enc(self, axis, rad):
    """Considers axis limits.
    """
    mn, mx, neutral, factor = self.AXIS_LIMITS[axis-1]
    e = int(factor*rad) + neutral
    f = min(max(mn, e), mx)
    if e != f:
      LOG.warning('axis %i: limited value %i to %i %s', axis,e,f,(mn,mx))
    return f

  def enc2rad(self, axis, enc):
    mn, mx, neutral, factor = self.AXIS_LIMITS[axis-1]
    return 1.0/factor*(enc - neutral)

  def is_moving(self):
    return self.KNI.is_moving()

  def get_speedLimit(self):
    """In rad/s"""
    return float(self._speed)/self.SPEED_LIMITS[0][1]

  def set_speedLimit(self, value):
    """In rad/s"""
    max_speed = self.SPEED_LIMITS[0][1]
    self._speed = min(int(value*max_speed), max_speed)
    self.KNI.SetMotorVelocityLimit()

  def set_accel(self, value):
    """Set normalized values, relative to hardware capabilities."""
    self._accel = min(value, self.SPEED_LIMITS[1][1])

  def get_tolerance(self, tolerance):
    """In radians, needs to convert to encoder value.
    0 means wait until reached. Not consistent.."""
    self._tolerance = tolerance

  def get_torso_info(self):
    """Returns TorsoInfo instance"""
    self._torso_info.rot= self.round([self.enc2rad(2,self.KNI.getEncoder(2)),
                                      0.0,
                                      self.enc2rad(1,self.KNI.getEncoder(1))])
    return self._torso_info

  def get_neck_info(self):
    """Returns NeckInfo instance"""
    # XXX: we are not using the same reference: create a mapping function
    #tp = self.KNI.TPos()
    #self.KNI.getPosition(tp)
    #self._neck_info.pos= self.round([tp.X, tp.Y, tp.Z])
    #self._neck_info.rot= self.round([tp.phi, tp.theta, tp.psi])

    self._neck_info.rot = self.round( \
        [ self.enc2rad(i, self.KNI.getEncoder(i+1)) for i in \
              xrange(3, len(self.AXIS_LIMITS)) ])
    return self._neck_info

  def switch_on(self):
    """Mandatory 1st call after hardware is switched on.
    Starts calibration if needed.
    """
    m_status = self.check_motors()
    LOG.debug("motor status: %s", m_status)
    if False in m_status:
      self.calibrate()
    self.switch_auto()
    self.set_neck_orientation((0,0,0))
    self.set_torso_orientation((0,0,0))

  def switch_off(self):
    """Set the robot for safe hardware switch off."""
    self.reach_pose('rest')
    self.switch_manual()

  def switch_manual(self):
    """WARNING: Allow free manual handling of the robot. ALL MOTORS OFF!"""
    if self.KNI.allMotorsOff() == -1:
      raise SpineError('failed to switch motors off')
    self._motors_on = False

  def switch_auto(self):
    """Resumes normal (driven-mode) operation of the robot."""
    if not self._motors_on and self.KNI.allMotorsOn() == -1:
      raise SpineError('failed to switch motors on')
    self._motors_on = True

  def calibrate(self):
    """Mandatory call upon hardware switch on. Also can be use to test
     calibration procedure."""
    # TODO: use another sequence so that the arm does not collide itself
    if self.KNI.calibrate(0) == -1:
      raise SpineError('failed to calibrate hardware')

  def check_motors(self):
    """Test each motor status"""
    motors = [None]*len(self.AXIS_LIMITS)
    encoders = self.KNI.getEncoders()
    for i in xrange(len(self.AXIS_LIMITS)):
      LOG.debug('checking motor %i', i+1)
      motors[i] = self.KNI.moveMot(i+1, encoders[i], self._speed, self._accel) != -1
    if not all(motors):
      LOG.debug("some motors can't move before calibration: %s", motors)
    return motors

  def reach_pose(self, pose_name, wait=True):
    """Set the motors to an absolute position.
    pose_name: identifier from SpineBase.POSE_IDs
    wait: wait for the pose to be reached before returning
    """
    if pose_name not in SpineBase.POSE_IDs:
      LOG.warning('pose %s does not exist', pose_name)
      return
    if self.KNI.moveToPosEnc(*list(SpineHW.POSES[pose_name])+
                        [self._speed, self._accel, self._tolerance, wait])== -1:
      raise SpineError('failed to reach pose %s' % pose_name)

  def set_neck_orientation(self, xyz, wait=True):
    """Absolute orientation:
    Our own version since the IK is useless (ERROR: No solution found)"""
    encs = [ (4+i, self.rad2enc(4+i, v)) for i,v in enumerate(xyz) ]
    for axis, enc in encs:
      LOG.debug('moving axis %i to encoder %i', axis, enc)
      if self.KNI.moveMot(axis, enc, self._speed, self._accel) == -1:
        raise SpineError('failed to reach rotation (axis %i)' % axis)
    if not wait:
      return
    for axis, enc in encs:
      if self.KNI.waitForMot(axis, enc, self._tolerance) != 1:
        raise SpineError('failed to wait for motor %i' % (axis))

  def set_torso_orientation(self, xyz, wait=True):
    """Absolute orientation:
    Our own version since the IK is useless (ERROR: No solution found)"""
    encs = [ (1, self.rad2enc(1, xyz[2])),
             (2, self.rad2enc(2, xyz[0])),
             (3, self.rad2enc(3, 0)) ]
    for axis, enc in encs:
      LOG.debug('moving axis %i to encoder %i', axis, enc)
      if self.KNI.moveMot(axis, enc, self._speed, self._accel) == -1:
        raise SpineError('failed to reach rotation (axis %i)' % axis)
    if not wait:
      return
    for axis, enc in encs:
      if self.KNI.waitForMot(axis, enc, self._tolerance) != 1:
        raise SpineError('failed to wait for motor %i' % axis)

  def set_neck_rot_pos(self, rot_xyz=None, pos_xyz=None):
    """Absolute orentation and position using KNI IK"""
    if not self._motors_on or (rot_xyz == pos_xyz == None):
      LOG.info('motors are %s [rot: %s\t pos: %s]', self._motors_on,
               rot_xyz, pos_xyz)
      return False
    tp = self.KNI.TPos()
    self.KNI.getPosition(tp)
    if rot_xyz:
      tp.phi, tp.theta, tp.psi = rot_xyz
    if pos_xyz:
      tp.X, tp.Y, tp.Z = pos_xyz
    ret = self.KNI.moveToPos(tp, self._speed, self._accel)
    self.KNI.getPosition(tp)
    if ret == -1:
      raise SpineError('failed to reach rotation/position')
    return True


if __name__ == '__main__':
  import time
  __path__ = ['.']
  from utils import comm
  comm.set_debug_logging(True)
  # just set the arm in manual mode and print motors' values upon key input.
  s = SpineHW()
  print "getting to pose 'rest';"
  s.reach_pose('rest', wait=False)

  while s.KNI.is_moving():
    print '.'
    time.sleep(.2)
  print "\nencoders:", s.KNI.getEncoders(), "velocities:", s.KNI.getVelocities()
  s.switch_off()
  while not raw_input('press any key then Enter to finish > '):
    print "encoders:", s.KNI.getEncoders(), "velocities:", s.KNI.getVelocities()
