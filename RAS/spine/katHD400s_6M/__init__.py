#!/usr/bin/python
# -*- coding: utf-8 -*-

# LightHead is a programm part of CONCEPT, a HRI PhD project at the University
#  of Plymouth. LightHead is a Robotic Animation System including face, eyes,
#   head and other supporting algorithms for vision and basic emotions.
# Copyright (C) 2010-2011 Frederic Delaunay, frederic.delaunay@plymouth.ac.uk

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
# This module implements the Katana-400-6M backend for the spine module.
# No protocol change so there's no need to override SpineClient.
#
# Axis are independant: an axis can be controlled (rigid) while others not.
#
import time
import threading

try:
  from utils import conf, get_logger
except ImportError, e:
  print e, "Make sure you have run 'source_me_to_set_env.sh'"
  exit(1)
import LH_KNI_wrapper
from RAS.au_pool import BVAL, RDIST, TDUR, DDUR, DVT, VAL
from RAS.spine import SpineError, Spine_Server, PoseManager, Pose

__all__ = ['SpineHW']

_MSG_ERR_CFG_SW = """
Erroneous Software limits for axis %i! SW:%s HW:%s
Either:
* Narrow down software limits in config file
* Use another value for that axis in 'ready' definition.
* In manual mode, try turning that axis by ±180 degrees, and restart.
"""
ACCEL = 1
SPEED = 20
TOLER = 10
VELOC = 50
MAX_VELOCITY = 180      # HW limit
LOG = get_logger(__package__)


def LH_KNI_get_poseFromHardware(self, check_SWlimits=False):
  """Implementation of PoseManager.get_poseFromHardware"""
  assert SpineHW.KNI_instance, "call before hardware initialization is complete"
  pose = []
  for i, enc in enumerate(SpineHW.KNI_instance.getEncoders()):
    try:
      AU = SpineHW.Axis2AU[i+1]                         # has only enabled AUs
    except KeyError:
      continue
    pi_factor, offset = self.infos[AU][0:2]             # self is a pose_manager
    pose.append((AU,(enc-offset)/pi_factor))
  return Pose(pose, self, check_SWlimits)


class SpineHW(Spine_Server):
  """Spine implementation for the Katana400s-6m"""

  AU2Axis = {'51.5': 6,
             '53.5': 4,
             '55.5': 5,
#             '57.5': None,
             'TX':   2,
             'TZ':   1}
  Axis2AU = dict([ (axis,AU) for AU,axis in AU2Axis.items() if axis ])
  AUs_sorted = [ Axis2AU.has_key(a) and Axis2AU[a] for a in range(1,7) ]
  KNI_instance = None

  def __init__(self):
    Spine_Server.__init__(self)
    self.running = False
    self.enabled_AUs = [ k for k,v in SpineHW.AU2Axis.items() if v ]
    self._init_hardware()
    self._review_infos()
    self.pmanager = PoseManager( dict([ 
          (AU,
           (self.EPPs[axis-1], self.HWready[axis-1],
            self.HW_limits[axis-1][0], self.HW_limits[axis-1][1],
            self.SW_limits[AU][0],     self.SW_limits[AU][1])
           ) for AU,axis in self.AU2Axis.iteritems() if axis != None ]) )
    self.pmanager.get_poseFromHardware = LH_KNI_get_poseFromHardware.__get__(
      self.pmanager, PoseManager)
    self.switch_on()
    self.AUs.set_availables(*zip(*self.pmanager.get_poseFromHardware().items()))

  def configure(self):
    """Overriden in order to set the KNI config file.
    """
    super(SpineHW, self).configure()
    from os.path import dirname, sep
    if dirname(__file__):
      self.KNI_cfg_file = dirname(__file__)+sep+"katana6M90T.cfg"
    else:
      self.KNI_cfg_file = "katana6M90T.cfg"

  def _init_hardware(self):
    """Initializes hardware: calibrate, check encoders, unlock arm if needed. 
    """
    def calibrate():
      print "\n\n\n\n=== MAKE SURE THE HEAD IS NOT ATTACHED TO THE ARM ==="
      raw_input("Press Enter key to start calibration")
      self.KNI.calibrate()
      self.switch_off()
      raw_input("Press Enter key when ready to use the arm (axis centered)")
      encoders_at_init = self.KNI.getEncoders()
      self.reach_raw(self.HWrest)
      self.reach_raw(self.HWready)
      return encoders_at_init

    LOG.info('Trying to connect (%s:%s)', self.hardware_name, self.KNI_address)
    self.KNI = LH_KNI_wrapper.LHKNI_wrapper(self.KNI_cfg_file, self.KNI_address)
    SpineHW.KNI_instance = self.KNI

    encoders_at_init = self.KNI.getEncoders()
    for axis in range(6):
      try:
        self.KNI.moveMot(axis+1, encoders_at_init[axis], SPEED, ACCEL)
      except SpineError, e:
        if self.unblock_if_needed() == None:            #TODO: set a policy ?
          try:
            LOG.info("Calibration needed.")
            LOG.debug("Got these encoders: %s", encoders_at_init)
            encoders_at_init = calibrate()
            break
          except SpineError, e:
            LOG.fatal('Could not switch on properly: %s', e)
            raise
        else:
          encoders_at_init = self.KNI.getEncoders()

    self.HW_limits, EPCs = self.KNI.getMinMaxEPC()
    self.EPPs = [ float(epc)/2 for epc in EPCs ]
    # rest and ready poses insignificant joints (None value) are set to 0 rad.
    for name, pose in (('ready',self.HWready),('rest',self.HWrest)):
      for i,enc in enumerate(pose):
        if enc == None:
          pose[i] = encoders_at_init[i]
          LOG.debug("Pose '%s', axis %i: 0 is now %senc.", name, i+1, pose[i])

  def _review_infos(self):
    """Manages software limits:

    * negating EPPs to fix rotation direction
    * checking for configuration value errors
    * setting encoder values to normalized values
    """
    for AU in self.SW_limits.iterkeys():
      try:
        axis = SpineHW.AU2Axis[AU]
      except KeyError:
        LOG.info("AU %s not supported by this backend", AU)
        continue
      # negates EPP if extra flag found
      if len(self.SW_limits[AU]) == 3:
        LOG.info("config for AU %s: extra param found, inverting rotation.", AU)
        self.EPPs[axis-1] *= -1
        self.SW_limits[AU] = self.SW_limits[AU][0:2]
      # Try avoiding stupid mistakes enforcing same type for min/max
      if repr(coerce(*self.SW_limits[AU])) != repr(self.SW_limits[AU]):
        raise SpineError("config: AU %s Software limits: same type needed.", AU)
      # convert encoder values to normalized
      if type(self.SW_limits[AU][0]) != type(.1):
        self.SW_limits[AU] = list(self.SW_limits[AU])           # set editable
        self.SW_limits[AU][0] = self.enc2nval(axis,self.SW_limits[AU][0])
        self.SW_limits[AU][1] = self.enc2nval(axis,self.SW_limits[AU][1])

  def unblock_if_needed(self):
    """Returns True if unblocked, None if not blocked, exits if still blocked.
    """
    if self.KNI.is_blocked(0):
      LOG.critical("---- The arm is blocked! -----")
      LOG.critical('GET READY TO HOLD THE ARM - ALL MOTORS WILL BE SHUT OFF!')
      self.KNI.unblock()
      if self.KNI.is_blocked(0):
        LOG.fatal("Failed to unblock the arm! Bailing out!")
        exit(2)                                         # crude but safer
      raw_input('PRESS ENTER TO ENTER MANUAL MODE')
      self.switch_manual()
      raw_input('PRESS ENTER ONCE THE ARM IS READY TO BE OPERATED AGAIN')
      self.switch_auto()
      return True
    return None

  def reach_raw(self, raw_vals):
    """Set all the motors to the given encoders (in sequence for KNI).
    """
    LOG.debug('reaching raw: %se', raw_vals)
    try:
      self.KNI.moveToPosEnc(*raw_vals+[VELOC, ACCEL, TOLER, True])
    except SpineError:
      raise SpineError("failed to reach raw '%s'" % raw_vals)

  def reach_pose(self, pose, wait=True):
    """Set all the motors to a pose (an absolute position).

    pose: a Pose instance
    wait: if True, waits for the pose to be reached before returning
    """
    for AU, raw_val in pose.to_raw().items():
      self.KNI.moveMotFaster(SpineHW.AU2Axis[AU],int(raw_val))          # ~ 20ms
    #self.KNI.moveToPosEnc(*encs+[10, ACCEL, TOLER, wait])              # ~460ms

  def set_targetTriplets(self, triplets):
    """Unlocks speed control loop to update the AUpool with accurate HW values.
    """
    super(SpineHW, self).set_targetTriplets(triplets)
    self.AUs.unblock_wait()

  def set_speeds(self, curr_Hpose, step_dur):
    """Computes and sets arm's speed from current hardware pose and ideal speed.
    """
    # The problem: arm's acceleration profile is unknown which generates
    # prediction errors. Hence the use of weighted average between ideal speed
    # and estimated speed to reach our next target.
    # Also notice that KNI.getVelocity(axis) is ~ 0.019s but too inaccurate.
    for AU,nHval in curr_Hpose.iteritems():
      if self.AUs[AU][DDUR] <= 0:
        continue
      row, axis = self.AUs[AU], SpineHW.AU2Axis[AU]
      next_distance = self.AUs.fct_mov(row) - nHval
      epp = self.EPPs[axis-1]                   # KNI speed is in encoders/0.01s
      needed_spd =  int(abs(epp * next_distance/step_dur *.01))
      ideal_spd =   int(abs(epp * row[DVT]               *.01))
      speed = int((4*ideal_spd+needed_spd)/5)
      if speed > MAX_VELOCITY:                          #TODO: broadcast/report
        LOG.warning("speed %i > MAX_VELOCITY (%i)", speed, MAX_VELOCITY)
      self.KNI.setMaxVelocity(axis, speed)

  def update_loop(self):
    """Moves the arm using dynamics (speed control) upon new AU update.
    """
    f = lambda x:x[TDUR]                                        #keep active AUs
    while self.running:
      if self.AUs.wait() and self.running:
        last_t = time.time()
        while True:
          curr_Hpose = self.pmanager.get_poseFromHardware()
          if self._new_pt:
            pose, triplets = self._new_pt
            for AU, nval in pose.iteritems():
              self.AUs[AU][VAL] = curr_Hpose[AU]
            self.AUs.update_targets(triplets)
            self.reach_pose(pose, wait=False)
            self._new_pt = None
          curr_t = time.time()
          #XXX: update returns False when all values reached their targets
          if self.AUs.update_time(curr_t-last_t, with_speed=True) == False:
            break
          self.set_speeds(curr_Hpose, curr_t-last_t)
          last_t = curr_t
        #XXX: Warning! the arm may still be moving at this point. 
    print 'update_loop done!'

  def start_speedControl(self):
    if not self.running:
      self.SC_thread = threading.Thread(name='LHKNISpeedControl',
                                        target=self.update_loop)
      self.running = True
      self.SC_thread.start()

  def stop_speedControl(self):
    if self.running:
      self.running = False
      self.AUs.unblock_wait()
      self.SC_thread.join()

  def switch_on(self):
    """Mandatory 1st call after hardware is switched on.
    """
    self.unblock_if_needed()
    self.switch_auto()
    pose_diff = [ abs(cp - rp) for cp,rp in zip(self.KNI.getEncoders(),
                                                self.HWready) ]
    if max(pose_diff) > TOLER:
      LOG.debug("moving to rest pose (too far from ready pose: +%s)", pose_diff)
      self.reach_raw(self.HWrest)

    self.reach_raw(self.HWready)
    self.start_speedControl()

  def switch_off(self):
    """Set the robot for safe hardware switch off."""
    self.stop_speedControl()
    self.reach_raw(self.HWrest)
    self.switch_manual()

  def switch_manual(self):
    """WARNING: Allow free manual handling of the robot. ALL MOTORS OFF!"""
    self.KNI.allMotorsOff()
    self._motors_on = False

  def switch_auto(self):
    """Resumes normal (driven-mode) operation of the robot."""
    self._motors_on and self.KNI.allMotorsOn()
    self._motors_on = True

  def nval2enc(self, axis, nvalue):
    """Computes encoder value for given axis.

    axis: KNI axis
    nvalue: normalized angle in [-1,1] (equivalent to [-pi,pi] or [-180,180])
    """
    enc = int(self.EPPs[axis-1]*nvalue) + self.HWready[axis-1]
    #print 'nval2enc',nvalue,int(self.EPPs[axis-1]*nvalue), self.HWready[axis-1]
    return enc

  def enc2nval(self, axis, encoder):
    """Returns the AU value for a specific axis.

    axis:    KNI axis identifier
    encoder: encoder value
    """
    axis -= 1
    value = float(encoder - self.HWready[axis])/self.EPPs[axis]
    #print "Axis %i: got %i encoder -> %s nvalue" % (axis+1, encoder, value)
    return value

  def is_moving(self):
    """Returns True if currently moving."""
    return self.KNI.is_moving(0)

  def cleanUp(self):
    """Calls switch_off"""
    self.stop_speedControl()
    self.switch_off()


if __name__ == "__main__":
  import logging
  from utils import comm, conf, LOGFORMATINFO
  logging.basicConfig(level=logging.DEBUG, **LOGFORMATINFO)
  import time

  from utils import conf
  conf.load(name='lightHead')

  s = SpineHW()
  while s.is_moving():
    print '.'
    time.sleep(.2)
  encs = s.KNI.getEncoders()
  print "this scripts shows you a snapshot of all axis' values"
  print "\nencoders:", encs, "normalized:", [ s.enc2nval(i+1,e) for i,e
                                              in enumerate(encs) ],
  print "velocities:", s.KNI.getVelocities()
  s.switch_off()
  while not raw_input('press any key then Enter to finish > '):
    encs = s.KNI.getEncoders()
    print "encoders:", s.KNI.getEncoders(),
    print "/ normalized:", [ s.enc2nval(i+1,e) for i,e in enumerate(encs) ],
    print "velocities:", s.KNI.getVelocities()
