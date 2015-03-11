#!/usr/bin/python
# -*- coding: utf-8 -*-

################################################################################
# This software is provided for academic research only: it is OSS but not GPL!
# In such a case, you can redistribute this software and/or modify it,
# provided you do not modify this license. Any other use is not permitted.

# ARAS is the open source software (OSS) version of the basic component of
# LightHead's software suite. 

# ARAS stands for Abstract Robotic Animation System, and features actuator,
# sensor, animation and remote management high-level interfaces.
# In particular, ARAS helps animating a head (virtual or physical), provides
# supporting algorithms for vision and hearing, as well as contributions from
# other scholars.
# Copyright 2009 - Frédéric Delaunay: dr.frederic.delaunay@gmail.com

# This software is the low-level Human-Robot-Interaction part of the CONCEPT
# project, which took place at the University of Plymouth (UK).
# The project stemed from by Frédéric Delaunay's PhD, himself under the
# supervision of professor Tony Belpaeme. The PhD project started in late 2008
# and ended in late 2011 but this part of the software is still maintained.
# Visit http://www.tech.plym.ac.uk/SoCCE/CONCEPT/ for more information.

# This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  General Public License for more details.
################################################################################

#
# This module implements the Katana-400-6M backend for the spine module.
# No protocol change so there's no need to override SpineClient.
#
# Axis are independant: an axis can be controlled (rigid) while others not.
#
import time
import logging
import threading

try:
  from utils import conf
except ImportError as e:
  print e, "Make sure you have run 'source_me_to_set_env.sh'"
  exit(1)
from katHD400s_6M.LH_KNI_wrapper import LHKNI_wrapper
from RAS.au_pool import BVAL, RDIST, TDUR, DDUR, DVT, VAL
from RAS.spine import SpineError, SpineServerMixin, PoseManager, Pose

__all__ = ['SrvMix_katana400s']

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
LOG = logging.getLogger(__package__)


def LH_KNI_get_poseFromHardware(self, check_SWlimits=False):
  """Implementation of PoseManager.get_poseFromHardware"""
  assert SrvMix_katana400s.KNI_instance, "no instance of SrvMix_katana400s yet."
  pose = []
  for i, enc in enumerate(SrvMix_katana400s.KNI_instance.getEncoders()):
    try:
      AU = SrvMix_katana400s.Axis2AU[i+1]               # has only enabled AUs
    except KeyError:
      continue
    pi_factor, offset = self.infos[AU][0:2]             # self is a pose_manager
    pose.append((AU,(enc-offset)/pi_factor))
  return Pose(pose, self, check_SWlimits)


class SrvMix_katana400s(SpineServerMixin):
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

  def __init__(self, conf):
    super(SrvMix_katana400s,self).__init__(conf)
    self.name = 'katHD400s_6M'
    self.running = False
    self.enabled_AUs = [ k for k,v in self.__class__.AU2Axis.items() if v ]
    self.pmanager = self._init_hardware()       #XXX:sets EPPs (Encoders Per Pi)
    self.pmanager.get_poseFromHardware = LH_KNI_get_poseFromHardware.__get__(
      self.pmanager, PoseManager)
    SrvMix_katana400s.KNI_instance = self.KNI
    self.switch_on()
    self.AUs.set_availables(*zip(*self.pmanager.get_poseFromHardware().items()))

  def configure(self):
    """Overriden in order to set the KNI config file.
    """
    super(SrvMix_katana400s, self).configure()
    try:
      self.KNI_address = self.conf['hardware_addr']
    except:
      raise conf.LoadingError("backend %s has no 'hardware_addr' key",__name__)
    from os.path import dirname, sep
    if dirname(__file__):
      self.KNI_cfg_file = dirname(__file__)+sep+"katana6M90T.cfg"
    else:
      self.KNI_cfg_file = "katana6M90T.cfg"

  def _init_hardware(self):
    """Calibrates, checks encoders, unlocks arm if needed. Big function!
    """
    PRESS_MSG = "--- Press Enter key when "
    def calibrate():
      print "\n\n\n\n=== Make sure the head is NOT attached to the arm ==="
      raw_input(PRESS_MSG+"to start calibration")
      self.KNI.calibrate()
      for i, raw_val in enumerate(self.HWrest):
        if raw_val:                                     # let user set centers
          self.KNI.moveMotFaster(i+1, int(raw_val))
      raw_input(PRESS_MSG+"ready to HOLD the arm for manual mode.")
      self.KNI.allMotorsOff()
      raw_input(PRESS_MSG+"the head is set on the arm.")
      for i, raw_val in enumerate(self.HWrest):
        if not raw_val:
          self.KNI.motorOn(i+1)
      del i
      return self.KNI.getEncoders()

    def manual_center(axis):
      raw_input(PRESS_MSG+"ready to HOLD axis %i (AU %s)" % (
          axis, SrvMix_katana400s.Axis2AU[axis]))
      self.KNI.motorOff(axis)
      raw_input(PRESS_MSG+"set at the neutral position for AUTOMATIC mode.")
      self.KNI.motorOn(axis)
      return self.KNI.getEncoders()

    def update_centers(encoders_at_init):
    # Rest and Ready poses unconfigured joints (None value) are set to 0 rad.
      for name, pose in (('ready',self.HW0pos),('rest',self.HWrest)):
        for i,enc in enumerate(pose):
          if enc == None:
            pose[i] = encoders_at_init[i]
            LOG.debug("Pose '%s', axis %i: 0 is now %senc.", name, i+1, pose[i])
      del i, enc

    def check_calibration():
      encoders_at_init = self.KNI.getEncoders()
      for axis in range(6):
        try:
          self.KNI.moveMot(axis+1, encoders_at_init[axis], SPEED, ACCEL)
        except SpineError as e:                         #TDL: better policy?
          if self.unblock_if_needed() == None:
            try:
              LOG.info("Calibration needed.")
              LOG.debug("Got these encoders: %s", encoders_at_init)
              encoders_at_init = calibrate()
              break
            except SpineError as e:
              LOG.fatal('Could not switch on properly: %s', e)
              raise
      del axis
      return encoders_at_init

    LOG.info('Trying to connect (%s:%s)', self.conf['backend'],self.KNI_address)
    self.KNI = LHKNI_wrapper(self.KNI_cfg_file, self.KNI_address)
    encoders_at_init = check_calibration()
    HW_limits, EPCs = self.KNI.getMinMaxEPC()
    while True:
      #axis 6 having no stopper, it can be set on/out of its reported HW bounds.
      for i,(rmin,rmax) in enumerate(HW_limits):
        while not (rmin < encoders_at_init[i] < rmax):
          print "motor %i is out of HW bounds [%i,%i]: %i" % (i+1, rmin, rmax,
                                                         encoders_at_init[i])
          encoders_at_init = manual_center(i+1)
      self.configure()
      update_centers(encoders_at_init)
      self.EPPs = self._review_infos([ float(epc)/2 for epc in EPCs ])
      try:                                      # axis may be out of SW bounds
        pmanager = PoseManager( { AU: (
              self.EPPs[axis-1],          self.HW0pos[axis-1],
              HW_limits[axis-1][0],       HW_limits[axis-1][1],
              self.SW_limits[AU][0],      self.SW_limits[AU][1] )
                                  for AU,axis in self.AU2Axis.iteritems()
                                  if axis != None } )
      except SpineError as e:
        LOG.warning("error: %s", e[0])
        encoders_at_init = manual_center(SrvMix_katana400s.AU2Axis[e[1]])
      else:
        return pmanager

  def _review_infos(self, EPPs):
    """Manages software limits:

    * negating EPPs (encoders per pi) to fix rotation direction
    * checking for configuration value errors
    * setting encoder values to normalized values
    """
    for AU in self.SW_limits.iterkeys():
      try:
        axis = SrvMix_katana400s.AU2Axis[AU]
      except KeyError:
        LOG.info("AU %s not supported by this backend", AU)
        continue
      # negates EPP if extra flag found
      if len(self.SW_limits[AU]) == 3:
        EPPs[axis-1] *= -1
        self.SW_limits[AU] = self.SW_limits[AU][0:2]
        LOG.info("[config] AU %s: extra param found, inverted rotation.", AU)
      # Try avoiding stupid mistakes enforcing same type for min/max
      if repr(coerce(*self.SW_limits[AU])) != repr(self.SW_limits[AU]):
        raise SpineError("config: AU %s Software limits: same type needed.", AU)
      # convert encoder values to normalized
      if type(self.SW_limits[AU][0]) != type(.1):
        self.SW_limits[AU] = list(self.SW_limits[AU])           # set editable
        self.SW_limits[AU][0] = self.enc2nval(axis,self.SW_limits[AU][0])
        self.SW_limits[AU][1] = self.enc2nval(axis,self.SW_limits[AU][1])
    return EPPs

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
    for AU, raw_val in self.pmanager.get_rawFromPose(pose).items():
      self.KNI.moveMotFaster(SrvMix_katana400s.AU2Axis[AU],int(raw_val))# ~ 20ms
    #self.KNI.moveToPosEnc(*encs+[10, ACCEL, TOLER, wait])              # ~460ms

  def set_targetTriplets(self, triplets):
    """Unlocks speed control loop to update the AUpool with accurate HW values.
    """
    super(SrvMix_katana400s, self).set_targetTriplets(triplets)
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
      row, axis = self.AUs[AU], SrvMix_katana400s.AU2Axis[AU]
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
                                                self.HW0pos) ]
    if max(pose_diff) > TOLER:
      LOG.debug("moving to rest pose (too far from ready pose: +%s)", pose_diff)
      self.reach_raw(self.HWrest)

    self.reach_raw(self.HW0pos)
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
    enc = int(self.EPPs[axis-1]*nvalue) + self.HW0pos[axis-1]
    #print 'nval2enc',nvalue,int(self.EPPs[axis-1]*nvalue), self.HW0pos[axis-1]
    return enc

  def enc2nval(self, axis, encoder):
    """Returns the AU value for a specific axis.

    axis:    KNI axis identifier
    encoder: encoder value
    """
    axis -= 1
    value = float(encoder - self.HW0pos[axis])/self.EPPs[axis]
    #print "Axis %i: got %i encoder -> %s nvalue" % (axis+1, encoder, value)
    return value

  def is_moving(self):
    """Returns True if currently moving."""
    return self.KNI.is_moving(0)

  def cleanUp(self):
    """Calls switch_off"""
    self.stop_speedControl()
    self.switch_off()

##
## Simple utility to draw axis values of the katana arm
##
if __name__ == "__main__":
  import logging
  from utils import comm, conf, LOGFORMATINFO
  logging.basicConfig(level=logging.DEBUG, **LOGFORMATINFO)
  import time

  from utils import conf
  conf.load(name='lighty')

  s = SrvMix_katana400s(conf.SPINE)
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
