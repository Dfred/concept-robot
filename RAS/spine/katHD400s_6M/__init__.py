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

if __name__ == '__main__':
  from utils import conf
  conf.load(name='lightHead')
from RAS.spine import SpineError, Spine_Server, PoseManager, Pose


def LH_KNI_get_poseFromHardware(self):
  """Implementation of PoseManager.get_poseFromHardware"""
  assert SpineHW.KNI_instance, "call before hardware initialization is complete"
  pose = []
  for i, enc in enumerate(SpineHW.KNI_instance.getEncoders()):
    try:
      AU = SpineHW.Axis2AU[i+1]                         # has only enabled AUs
    except KeyError:
      continue
    pi_factor, offset = self.infos[AU][0:2]
#    print 'AU %s (axis %i) from HW %iencs => %s' % (AU, i+1, enc, (enc-offset)/pi_factor)
    pose.append((AU,(enc-offset)/pi_factor))
  return Pose(pose, self)


class SpineHW(Spine_Server):
  """Spine implementation for the Katana400s-6m"""

  AU2Axis = {'51.5': 6,
             '53.5': 4,
             '55.5': 5,
#             '57.5': None,
             'TZ':   1}
  Axis2AU = dict([ (axis,AU) for AU,axis in AU2Axis.items() if axis ])
  AUs_sorted = [ Axis2AU.has_key(a) and Axis2AU[a] for a in range(1,7) ]
  KNI_instance = None

  def __init__(self, with_ready_pose=True):
    Spine_Server.__init__(self)
    self.running = False
    self.enabled_AUs = [ k for k,v in SpineHW.AU2Axis.items() if v ]
    self.init_hardware()
    self.check_SWlimits()
    self.pmanager = PoseManager( dict([ 
          (AU,
           (self.EPPs[axis-1], self.HWready[axis-1],
            self.HW_limits[axis-1][0], self.HW_limits[axis-1][1],
            (self.SW_limits[axis-1][0]-self.HWready[axis-1]) /self.EPPs[axis-1],
            (self.SW_limits[axis-1][1]-self.HWready[axis-1]) /self.EPPs[axis-1])
           ) for AU,axis in self.AU2Axis.iteritems() if axis != None ]) )
    self.pmanager.get_poseFromHardware = LH_KNI_get_poseFromHardware.__get__(
      self.pmanager, PoseManager)
    self.AUs.set_availables(self.pmanager.get_poseFromHardware())
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

  def check_SWlimits(self):
    """
    """
    # check limits for floats (normalized angles) and convert them to encoders
    for i in range(len(self.SW_limits)):
      for b in range(2):
        if type(self.SW_limits[i][b]) == type(.1):      # normalized angle
          self.SW_limits[i] = list(self.SW_limits[i])
          self.SW_limits[i][b]= self.nval2enc(i+1,self.SW_limits[i][b])
      LOG.debug("AU %s - axis %i HW:%s %se/pi - "
                "SW:(%se{%.3f/pi}[%senc],%s,[%senc]%se{%.3f/pi})",
                SpineHW.Axis2AU[i+1] if SpineHW.Axis2AU.has_key(i+1) else None,
                i+1,
                self.HW_limits[i], self.EPPs[i], 
                self.SW_limits[i][0],
                self.enc2nval(i+1,self.SW_limits[i][0]),
                self.HWready[i]-self.SW_limits[i][0],
                self.HWready[i],
                self.SW_limits[i][1]-self.HWready[i],
                self.SW_limits[i][1],
                self.enc2nval(i+1,self.SW_limits[i][1]))
      if ( self.SW_limits[i][0] < self.HW_limits[i][0] or
           self.SW_limits[i][1] > self.HW_limits[i][1] ):
        LOG.critical(_MSG_ERR_CFG_SW, i+1, self.SW_limits[i], self.HW_limits[i])
        exit(2)                                         # crude but safe

  def check_encoder(self, axis, enc):
    """
    axis: KNI axis
    enc: encoder value for that axis
    """
    axis -= 1
    HWenc = min( max(enc,   self.HW_limits[axis][0]), self.HW_limits[axis][1])
    if HWenc != enc:
      raise ValueError("%senc. beyond axis %i Hardware limits." % (enc, axis+1))
    SWenc = min( max(HWenc, self.SW_limits[axis][0]), self.SW_limits[axis][1])
    if SWenc != enc:
      raise ValueError("%senc. beyond axis %i Software limits." % (enc, axis+1))
    return SWenc

  def init_hardware(self):
    """
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
            LOG.debug("Got this pose: %s", encoders_at_init)
            encoders_at_init = calibrate()
            break
          except SpineError, e:
            LOG.fatal('Could not switch on properly: %s', e)
            raise
        else:
          encoders_at_init = self.KNI.getEncoders()

    self.HW_limits, EPCs = self.KNI.getMinMaxEPC()
    self.EPPs = [ float(epc)/2 for epc in EPCs ]

    for name, pose in (('ready',self.HWready),('rest',self.HWrest)):
      for i,enc in enumerate(pose):
        if enc == None:
          pose[i] = encoders_at_init[i]
          LOG.debug("Pose '%s', axis %i: 0 is now %senc.", name, i+1, pose[i])

  def unblock_if_needed(self):
    """Returns True if unblocked, None if not blocked, exits if still blocked.
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
      print 'AU %s: reaching %se' % (AU, raw_val)
      self.KNI.moveMotFaster(SpineHW.AU2Axis[AU],int(raw_val))

  def set_targetTriplets(self, triplets):
    """Unlocks the speed control loop, so it can update the AUpool with
    accurate HW values.
    """
    super(SpineHW, self).set_targetTriplets(triplets)
    self.AUs.unblock_wait()

  def update_poolFromNewTriplets(self):
    """Also updates the AU pool current values with those read from hardware.
    """
    HW_p = self.pmanager.get_poseFromHardware()
    for triplet in self._target_triplets:
      AU = triplet[0]
      print 'setting AU %s target to %s (HW update %s [%se]) in %ss.' % (
        triplet[0],
        triplet[1],
        HW_p[triplet[0]],
        self.pmanager.get_rawFromNval(triplet[0],HW_p[triplet[0]]),
        triplet[2])
      self.AUs[AU][-1] = HW_p[AU]
    self.AUs.update_targets(self._target_triplets)              #XXX: ok now
    self._target_triplets = None

  def set_speeds(self, curr_Hpose):
    """
    """
    # .04s for setMaxVelocity + get_Encoders
    for AU,ndist in self.AUs.predict_dist(.04, curr_Hpose,
                                           self.EPPs[0],
                                           self.HWready[0]).items():
      if not ndist:                                             # actives only
        continue
      axis = SpineHW.AU2Axis[AU]
      # KNI speed is in encoders/0.01s
      speed = max(int(self.EPPs[axis-1]*ndist/.04 *.01), 0);
      LOG.debug('dist %.5f (%senc) speed: %s',
                ndist, int(self.EPPs[axis-1]*ndist),speed)
      self.KNI.setMaxVelocity(axis, speed)

  def update_loop(self):
    """Moves the arm using dynamics (speed control) upon new AU update.
    """
    while self.running:
      if self.AUs.wait() and self.running:
        self.update_poolFromNewTriplets()
        start_time = time.time()
        #XXX: pose has been verified by handler
        self.reach_pose(self.pmanager.get_poseFromPool(self.AUs), wait=False)
        last_t = start_time
        updates = 0
        while True:                      #TODO: break loop for pose reset
          curr_Hpose = self.pmanager.get_poseFromHardware()
          curr_t = time.time()
          #XXX: update returns False when all values reached their targets
          if self.AUs.update_time(curr_t-last_t, with_speed=True) == False:
            break
          self.set_speeds(curr_Hpose)
          last_t = curr_t
          updates += 1
        elapsed = time.time() - start_time
        print 'done in %ss : %.2f updates/s' % (elapsed, updates/elapsed)
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
      self.AUs.unblock_wait()
      self.SC_thread.join()

  def switch_on(self, with_ready_pose=True):
    """Mandatory 1st call after hardware is switched on.
    """
    self.unblock_if_needed()
    self.switch_auto()
    pose_diff = [ abs(cp - rp) for cp,rp in zip(self.KNI.getEncoders(),
                                                self.HWready) ]
    if max(pose_diff) > TOLER:
      LOG.debug("moving (current pose far from 'ready' pose %s)", pose_diff)
      self.reach_raw(self.HWrest)                           # we may have moved
      if with_ready_pose:
        self.reach_raw(self.HWready)
    self.start_speed_control()

  def switch_off(self):
    """Set the robot for safe hardware switch off."""
    self.stop_speed_control()
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

  def set_accel(self, value):
    """Set normalized values, relative to hardware capabilities."""
    self._accel = min(value, self.SPEED_LIMITS[1][1])

  def is_moving(self):
    return self.KNI.is_moving(0)

  def cleanUp(self):
    """Calls switch_off"""
    self.switch_off()


if __name__ == "__main__":
  import logging
  from utils import comm, conf, LOGFORMATINFO
  logging.basicConfig(level=logging.DEBUG, **LOGFORMATINFO)
  import time
  # just set the arm in manual mode and print motors' values upon key input.
  s = SpineHW(with_ready_pose=False)

  while s.is_moving():
    print '.'
    time.sleep(.2)
  print "this scripts shows you a snapshot of all axis' encoder values"
  print "\nencoders:", s.KNI.getEncoders(), "velocities:", s.KNI.getVelocities()
  s.switch_off()
  while not raw_input('press any key then Enter to finish > '):
    print "encoders:", s.KNI.getEncoders(), "velocities:", s.KNI.getVelocities()
