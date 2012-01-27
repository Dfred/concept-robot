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


ACCEL = 1
SPEED = 20
TOLER = 10
VELOC = 50
MAX_VELOCITY = 170#255/1.5
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
    print 'AU %s (axis %i) from HW %iencs => %s' % (AU, i+1, enc, (enc-offset)/pi_factor)
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
           (self.EPPs[axis-1], self.ready[axis-1],
            self.HW_limits[axis-1][0], self.HW_limits[axis-1][1],
            (self.SW_limits[axis-1][0]-self.ready[axis-1]) / self.EPPs[axis-1],
            (self.SW_limits[axis-1][1]-self.ready[axis-1]) / self.EPPs[axis-1]
            )
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
          self.SW_limits[i][b]= self.nval2enc(i+1,self.SW_limits[i][b],raw=True)
      LOG.debug("AU %s - axis %i HW:%s %se/pi - "
                "SW:(%se{%.3f/pi}[%senc],%s,[%senc]%se{%.3f/pi})",
                SpineHW.Axis2AU[i+1] if SpineHW.Axis2AU.has_key(i+1) else None,
                i+1,
                self.HW_limits[i], self.EPPs[i], 
                self.SW_limits[i][0],
                self.enc2nval(i+1,self.SW_limits[i][0]),
                self.poses['ready'][i]-self.SW_limits[i][0],
                self.poses['ready'][i],
                self.SW_limits[i][1]-self.poses['ready'][i],
                self.SW_limits[i][1],
                self.enc2nval(i+1,self.SW_limits[i][1]))
      if ( self.SW_limits[i][0] < self.HW_limits[i][0] or
           self.SW_limits[i][1] > self.HW_limits[i][1] ):
        LOG.critical("""Erroneous Software limits for axis %i! SW:%s HW:%s
Either:
* Narrow down software limits in config file
* Use another value for that axis in pose 'ready'
* In manual mode, try turning that axis by ±180 degrees, and restart.""",
                     i+1, self.SW_limits[i], self.HW_limits[i])
#        exit(2)                                         # crude but safe

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
      self.reach_pose('rest')
#      self.reach_pose('ready')
      self.reach_Pose('ready')
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

    # Check for generated poses values from config
    for name, pose in self.poses.iteritems():
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

  def reach_pose(self, pose, wait=True, check_encoders=True):
    """Set all the motors to a pose (an absolute position).

    pose: string identifier from Spine_Server.POSE_IDs *OR* iterable of encoders
    wait: wait for the pose to be reached before returning
    tolerance: KNI tolerance to use.
    """
    name = type(pose) == type('') and pose or None
    if name:
      if name not in self.poses.keys():
        LOG.warning('pose %s does not exist', name)
        return
      pose = list(self.poses[name])
    elif check_encoders:
      [self.check_encoder(i+1,pose[i]) for i in range(len(pose))]#XXX raise UGLY
    LOG.debug('reaching pose %s : %s', name, pose)
    try:
      self.KNI.moveToPosEnc(*pose+[VELOC, ACCEL, TOLER, wait])
    except SpineError:
      raise SpineError("failed to reach pose '%s'" % pose)

  def reach_Pose(self, pose, wait=True):
    """Set all the motors to a pose (an absolute position).
    pose: a Pose instance
    wait: wait for the pose to be reached before returning
    """
    for AU, raw_val in pose.to_raw().items():
      self.KNI.moveMotFaster(SpineHW.AU2Axis[AU],int(raw_val))

  def update_from_HW(self):
    """Updates the AU pool current values with one read from the hardware.
    """
    for AU,nval in self.pmanager.get_poseFromHardware().iteritems():
      print 'AU %s: reaching %s (%se)' % (AU, nval, self.pmanager.get_rawFromNval(AU,nval))
      self.AUs[AU][-1] = nval

  def update_loop(self):
    """Moves the arm using dynamics (speed control) upon new AU update.
    """
#   AU_seq = [AU for AU,ax in sorted(SpineHW.AU2Axis.items(),key=lambda x:x[1])]
    while self.running:
      print 'waiting'
      if self.AUs.wait():
        print 'updated:', self.AUs
        start_time = time.time()
        #XXX: we need to set the AUPool's Base Value properly
        self.update_from_HW()
        #XXX: pose has been verified by server
        self.reach_Pose(self.pmanager.get_poseFromPool(self.AUs), wait=False)
        controlling = True
        t = start_time
        while controlling:                      #TODO: break loop for pose reset
          curr_Hpose = self.pmanager.get_poseFromHardware()
          print 'Hardware:', curr_Hpose, curr_Hpose.to_raw()
          tmp = time.time()
          t_diff = tmp - t
          t = tmp
          #XXX: update returns False when all values reached their targets
          if self.AUs.update_time(t_diff, with_speed=True) == False:
            controlling = False
            continue
          for AU,ndist in self.AUs.predict_dist(t_diff, curr_Hpose).items():
            if not ndist:                                       # actives only
              continue
            axis = SpineHW.AU2Axis[AU]
            # KNI speed is in encoders/0.01s
            speed = int(self.EPPs[axis]*ndist/t_diff *.01)
            LOG.debug('dist %.5f (%senc) speed: %s', ndist, int(self.EPPs[axis]*ndist),speed)
            self.KNI.setMaxVelocity(axis, speed)
        print 'done in %ss' % (time.time() - start_time)
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
      au = SpineHW.AU2Axis.keys()[0]
      self.AUs.update_targets(((au, self.AUs[au][-1], 0),))     # unblock thread
      self.SC_thread.join()

  def switch_on(self, with_ready_pose=True):
    """Mandatory 1st call after hardware is switched on.
    """
    self.unblock_if_needed()
    self.switch_auto()
    pose_diff = [ abs(cp - rp) for cp,rp in zip(self.KNI.getEncoders(),
                                                self.poses['ready']) ]
    if max(pose_diff) > TOLER:
      LOG.debug("moving (current pose far from 'ready' pose %s)", pose_diff)
      self.reach_pose('rest')                           # we may have moved
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

  def pose2values(self, pose):
    """Returns AU values for the given pose, skipping disabled axis in AU2Axis.

    pose: iterable of axis identifiers
    """
    encs = self.KNI.getEncoders()
    return [ self.enc2nval(i+1,encs[i]) for i,enc in
             enumerate(pose) if i+1 in SpineHW.AU2Axis.values() ]

  def nval2enc(self, axis, nvalue, raw=False):
    """Computes encoder value for given axis. ValueError if out of limits. 

    axis: KNI axis
    nvalue: normalized angle in [-1,1] (equivalent to [-pi,pi] or [-180,180])
    """
    axis -= 1
    if nvalue>1:
      import pdb; pdb.set_trace()
    enc = int(self.EPPs[axis]*nvalue) + self.poses['ready'][axis]
    #print 'nval2enc',nvalue,int(self.EPPs[axis]*nvalue), self.poses['ready'][axis]
    return raw and enc or self.check_encoder(axis+1, enc)

  def enc2nval(self, axis, encoder):
    """Returns the AU value for a specific axis.

    axis:    KNI axis identifier
    encoder: encoder value
    """
    axis -= 1
    value = float(encoder - self.poses['ready'][axis])/self.EPPs[axis]
#    LOG.debug("Axis %i: got %i encoder -> %s nvalue", axis+1, encoder, value)
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
