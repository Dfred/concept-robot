#!/usr/bin/python

#
# This module implements the Katana-400-6M backend for the spine module.
# No protocol change so there's no need to override SpineClient.
#
# Axis are independant: an axis can be controlled (rigid) while others not.
#
import math
import threading

try:
  from utils import conf, get_logger
except ImportError, e:
  print e, "Make sure you have run 'source_me_to_set_env.sh'"
  exit(1)
import LH_KNI_wrapper

__all__ = ['SpineHW']


SPEED = 20
ACCEL = 1
TOLER = 10
LOG = get_logger(__package__)

if __name__ == '__main__':
  from utils import conf
  conf.load(name='lightHead')
from RAS.spine import SpineError, Spine_Server


class SpineHW(Spine_Server):
  """Spine implementation for the Katana400s-6m"""

  AU2Axis = {'51.5': 6,
             '53.5': 4,
             '55.5': 5,
             '57.5': None,
             'TZ':   1}

  def __init__(self, with_ready_pose=True):
    Spine_Server.__init__(self)
    self.running = False
    self.enabled_AUs = [ k for k,v in SpineHW.AU2Axis.items() if v ]
    self.AUs.set_availables(self.enabled_AUs)
    self.init_hardware()
    # check limits for floats (normalized angles) and convert them to encoders
    for i in range(len(self.SW_limits)):
      for b in range(2):
        if type(self.SW_limits[i][b]) == type(.1):
          self.SW_limits[i] = list(self.SW_limits[i])
          self.SW_limits[i][b] = self.value2encoder(i+1, self.SW_limits[i][b],
                                                    raw=True)
          LOG.debug('axis %i %s SW_limit: %ienc', i+1, ("min","max")[b],
                    self.SW_limits[i][b])
    self.switch_on()

  def configure(self):
    """
    """
    super(SpineHW, self).configure()
    from os.path import dirname, sep
    if dirname(__file__):
      self.KNI_cfg_file = dirname(__file__)+sep+"katana6M90T.cfg"
    else:
      self.KNI_cfg_file = "katana6M90T.cfg"

  def init_hardware(self):
    """
    """
    LOG.info('Trying to connect (%s:%s)', self.hardware_name, self.KNI_address)
    self.KNI = LH_KNI_wrapper.LHKNI_wrapper(self.KNI_cfg_file, self.KNI_address)

    # calibrate_if_needed
    encoders_at_init = self.KNI.getEncoders()
    for axis in range(6):
      try:
        self.KNI.moveMot(axis+1, encoders_at_init[axis], SPEED, ACCEL)
      except SpineError, e:
        try:
          LOG.info("Calibration needed.")
          print "\n\n\n\n=== MAKE SURE THE HEAD IS NOT ATTACHED TO THE ARM ==="
          raw_input("Press Enter key to start calibration")
          self.KNI.calibrate()
          break
        except SpineError, e:
          LOG.fatal('Could not switch on properly: %s', e)
          raise

    self.HW_limits, self.EPCs = self.KNI.getMinMaxEPC()
    self.EPCs = [ epc/2 for epc in self.EPCs ]
    for i in range(6):
      LOG.debug('axis %i HW: %se %se/pi', i+1, self.HW_limits[i], self.EPCs[i])

    # Check for generated poses values from config
    for name, pose in self.poses.iteritems():
      for i,enc in enumerate(pose):
        if enc == None:
          pose[i] = encoders_at_init[i]
          LOG.debug("Pose '%s', axis %i: 0 is now %senc.", name, i+1, pose[i])

  def value2encoder(self, axis, nvalue, raw=False):
    """Computes the encoder value for a specific axis considering its limits.
    axis: KNI axis
    nvalue: normalized angle in [-1,1] (equivalent to [-pi,pi] or [-180,180])
    """
    axis -= 1
    value = int(self.EPCs[axis]*nvalue) + self.poses['ready'][axis]
    if raw:
      return value
    HWenc = min( max(value, int(self.HW_limits[axis][0])),
               self.HW_limits[axis][1])
    SWenc = min( max(HWenc, self.SW_limits[axis][0]), self.SW_limits[axis][1])
    LOG.debug("Axis %i: asked [%s -> %i] HW:%i SW:%s %s", axis+1, nvalue, value,
              HWenc, SWenc, value!=SWenc and "(clamped from %i)"%HWenc or "")
    return SWenc

  def is_moving(self):
    return self.KNI.is_moving(0)

  def update_loop(self):
    """Move arm upon new AU update. self.speed_control deals with dynamics.
    """
    while self.running:
      if self.AUs.wait(timeout=2):
        for au, infos in self.AUs.items():
          axis, target = SpineHW.AU2Axis[au], infos[0]
          assert axis, 'axis for AU %s is disabled!!?' % au
          # TODO: use dynamics
          self.KNI.moveMot(axis, self.value2encoder(axis,target), SPEED,ACCEL)
    print 'update_loop done!'

  def start_speed_control(self):
    if not self.running:
      self.SC_thread = threading.Thread(name='LHKNISpeedControl',
                                        target=self.update_loop)
      self.running = True
      self.SC_thread.start()

  def stop_speed_control(self):
    if self.running:
      self.running = False
      self.SC_thread.join()

  #TODO: complete this
  def speed_control(self):
    """Control the arm with speed to apply the required movement dynamics. 
    """
    pass

  def set_accel(self, value):
    """Set normalized values, relative to hardware capabilities."""
    self._accel = min(value, self.SPEED_LIMITS[1][1])

  def unblock_if_needed(self):
    """
    """
    if self.KNI.is_blocked():
      LOG.critical("---- The arm is blocked! -----")
      LOG.critical('GET READY TO HOLD THE ARM - ALL MOTORS WILL BE SHUT OFF!')
      self.KNI.unblock()
      if self.KNI.is_blocked():
        LOG.fatal("Failed to unblock the arm! Bailing out!")
        exit(2)                                         # crude but safer
      raw_input('PRESS ENTER TO ENTER MANUAL MODE')
      self.switch_manual()
      raw_input('PRESS ENTER ONCE THE ARM IS READY TO BE OPERATED AGAIN')
      self.switch_auto()

  def switch_on(self, with_ready_pose=True):
    """Mandatory 1st call after hardware is switched on.
    """
    self.unblock_if_needed()
    self.switch_auto()
    self.reach_pose('rest')                             # we may have moved
    if with_ready_pose:
      self.reach_pose('ready')
    self.start_speed_control()

  def switch_off(self):
    """Set the robot for safe hardware switch off."""
    self.stop_speed_control()
    self.reach_pose('rest')
    self.switch_manual()

  def switch_manual(self):
    """WARNING: Allow free manual handling of the robot. ALL MOTORS OFF!"""
    self.KNI.allMotorsOff()
    self._motors_on = False

  def switch_auto(self):
    """Resumes normal (driven-mode) operation of the robot."""
    self._motors_on and self.KNI.allMotorsOn()
    self._motors_on = True

  def reach_pose(self, pose_name, wait=True):
    """Set all the motors to a pose (an absolute position).
    pose_name: identifier from Spine_Server.POSE_IDs
    wait: wait for the pose to be reached before returning
    """
    if pose_name not in self.poses.keys():
      LOG.warning('pose %s does not exist', pose_name)
      return
    try:
      LOG.debug('reaching pose %s : %s', pose_name, self.poses[pose_name])
      self.KNI.moveToPosEnc(*list(self.poses[pose_name])+
                             [50, ACCEL, TOLER, wait])
    except SpineError:
      raise SpineError("failed to reach pose '%s'" % pose_name)



if __name__ == "__main__":
  import time
  # just set the arm in manual mode and print motors' values upon key input.
  s = SpineHW(with_ready_pose=False)

  while s.is_moving():
    print '.'
    time.sleep(.2)
  print "\nencoders:", s.KNI.getEncoders(), "velocities:", s.KNI.getVelocities()
  s.switch_off()
  while not raw_input('press any key then Enter to finish > '):
    print "encoders:", s.KNI.getEncoders(), "velocities:", s.KNI.getVelocities()
