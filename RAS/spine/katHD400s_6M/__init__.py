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

  POSES = {'rest'       : None,                         # safe rest position
           'oper-start' : None,                         # operating start pose
           'zero'       : None,                         # all axis at 0rad.
           'avg'        : None,                         # all at mid-range
           }

  def __init__(self):
    Spine_Server.__init__(self)
    self.running = False
    self.SC_thread = threading.Thread(name='LHKNISpeedControl',
                                      target=self.update_loop)
    self.enabled_AUs = [ k for k,v in SpineHW.AU2Axis.items() if v ]
  #TODO: load essentials to connect to the arm, connect, retreive hardware limits (TMotENL), and then add software limits from conf.
    self.parse_conf()
    LOG.info('Trying to connect (%s:%s)', self.hardware_name, self.KNI_address)
    self.KNI = LH_KNI_wrapper.LHKNI_wrapper(self.KNI_cfg_file, self.KNI_address)
    self.switch_on()
    self.AUs.set_availables(self.enabled_AUs)

  def parse_conf(self):
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
    return self.KNI.is_moving(0)

  def update_loop(self):
    """Move arm upon new AU update. self.speed_control deals with dynamics.
    """
    while self.running:
      self.AUs.wait()
      for au, infos in self.AUs.items():
        axis, target = SpineHW.AU2Axis[au], infos[0]
        assert axis, 'axis for AU %s is disabled!!?' % au
        # TODO: use dynamics
        self.KNI.moveMot(axis, self.rad2enc(axis, target*math.pi), SPEED, ACCEL)

  #TODO: complete this
  def speed_control(self):
    """Control the arm with speed to apply the required movement dynamics. 
    """
    pass

  def set_accel(self, value):
    """Set normalized values, relative to hardware capabilities."""
    self._accel = min(value, self.SPEED_LIMITS[1][1])

  def switch_on(self):
    """Mandatory 1st call after hardware is switched on.
    Starts calibration if needed.
    """
    self.KNI.calibrate_if_needed()                      #XXX: motor fail => axis
    self.switch_auto()
    self.reach_pose('oper-start')
    if not self.running:
      self.running = True
      self.SC_thread.start()

  def switch_off(self):
    """Set the robot for safe hardware switch off."""
    if self.running:
      self.running = False
      self.SC_thread.join()
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
    if pose_name not in Spine_Server.POSE_IDs:
      LOG.warning('pose %s does not exist', pose_name)
      return
    try:
      LOG.debug('reaching pose %s : %s', pose_name, SpineHW.POSES[pose_name])
      self.KNI.moveToPosEnc(*list(SpineHW.POSES[pose_name])+
                             [50, ACCEL, TOLER, wait])
    except SpineError:
      raise SpineError('failed to reach pose %s' % pose_name)



if __name__ == "__main__":
  import time
  # just set the arm in manual mode and print motors' values upon key input.
  s = SpineHW()
  print "getting to pose 'rest';"
  s.reach_pose('rest', wait=False)

  while s.is_moving():
    print '.'
    time.sleep(.2)
  print "\nencoders:", s.KNI.getEncoders(), "velocities:", s.KNI.getVelocities()
  s.switch_off()
  while not raw_input('press any key then Enter to finish > '):
    print "encoders:", s.KNI.getEncoders(), "velocities:", s.KNI.getVelocities()
