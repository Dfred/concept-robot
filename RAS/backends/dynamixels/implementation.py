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

"""Backend for Robotis' Dynamixel.
Tested with:    * AX-12A / AX-12+
                *
"""
import math
import logging

from . import BAUD_RATES
from dynamixel_ext import DynamixelNetworkEx
from dynamixel import SerialStream

from utils import EXIT_DEPEND, EXIT_CONFIG
from utils.conf import CONFIG
from RAS.spine import (SpineServerMixin, SpineHandlerMixin, PoseManager,
                       SpineError)
#from RAS.au_pool import 

LOG = logging.getLogger(__package__)

## Doc conflict: .29*1024 = 296.96 , but 300/1024 ~= .293 (~3 degrees)
PIF = (1024-512)/math.radians(296.96)           ## pi factor
MINRAWDELTA_READY = 50                          ## to prevent weird startups

  
class SrvMix_Dynamixel(SpineServerMixin):
  """Spine implementation for Dynamixel servos.
  """

  def __init__(self):
    """
    """
    self.name = "dynamixels"
    super(SrvMix_Dynamixel,self).__init__()             ## sets self.SW_limits
    self.daisy_chain = None
    self.__init_hardware()
    self.pmanager.get_poseFromHardware = self.get_poseFromHardware.__get__(
      self.pmanager, PoseManager)
    self.AUs.set_availables(*zip(*self.pmanager.get_poseFromHardware().items()))
    self.ready()
    print "done ready"

  def __init_hardware(self):
    """
    """
    pman = self.pmanager
    pman.set_hardware_infos({ pman.ID2AU[ID] : (PIF, rVal, 0, 1023) for
                              ID, rVal in pman.get_rawNeutralPose().items() } )
    portID, baudsR = CONFIG[self.name+"_serial_port"]
    try:
      #XXX these arguments are passed over to python's serial module
      serial = SerialStream(port=portID, baudrate=baudsR, timeout=.1)
      LOG.debug("opened port %s @%ibps", portID, baudsR)
      self.daisy_chain = DynamixelNetworkEx(serial)
    except ValueError as e:
      LOG.fatal("Cannot start dynamixel: %s", e)

    pose_manager_info = {}
    for ID, AU in pman.ID2AU.iteritems():
      self.daisy_chain.add_dynamixel(ID)
      servo = self.daisy_chain[ID]
      servo.read_all()
      LOG.debug("dynamixel #%i:\n"
                "\tstatus_return_level: %i\n"
                "\tWill shutdown for alarms: %s\n"
                "\tcurrent position: %i\n"
                "\tcurrent temperature: %i°C\n",
                ID, servo.status_return_level, 
                self.daisy_chain.error_text(servo.alarm_shutdown),
                servo.goal_position, servo.current_temperature)
      servo.synchronized = True                                 ## only internal
      servo.torque_enable = False                               ## HW protect
      servo.torque_limit = 1023                                 ## 100%
      servo.max_torque = 960

      if self.AUs.has_key(AU):
        LOG.warning("AU %s already present in pool.", AU)
##TDL use that if needed, (requires some traffic on serial).
#    LOG.debug("serial statistics: %s", self.daisy_chain.dump_statistics())
    self.daisy_chain[1].moving_speed = 512
    self.daisy_chain[2].moving_speed = 50
    self.daisy_chain[3].moving_speed = 512

  def _nval2enc(self, nval, axis):
    """Translates from normalized AU value to iCub value.
    Return: iCub value
    """
    pass

  def get_poseFromHardware(self):
    """
    """
    return { AU : 
             self.pmanager.get_val(AU,self.daisy_chain[axisID].current_position)
             for axisID,AU in self.pmanager.ID2AU.items() }

  def ready(self):
    """
    """
    ## Ensure the configuration is very close to the resting pose
    pose_it = self.pmanager.get_rawRestingPose().iteritems()
    while True:
      try:
        ID, rVal = pose_it.next()
      except StopIteration:
        break
      else:
        servo = self.daisy_chain[ID]
        if abs(servo.current_position - rVal) > MINRAWDELTA_READY:
          LOG.warning("AU %s (servo %i) is too far from rest position (%i).", 
                      self.pmanager.get_AU(ID), ID, servo.current_position)
          raw_input("--- Press Enter when ready ---")
          pose_it = self.pmanager.get_rawRestingPose().iteritems()
    
    ## Now go into neutral pose
    for ID, rVal in self.pmanager.get_rawNeutralPose().items():
      LOG.debug("servo #%i setting from %i -> %i", ID,
                self.daisy_chain[ID].current_position, rVal)
      self.daisy_chain[ID].goal_position = int(rVal)
    self.daisy_chain.synchronize()

  def commit_AUs(self, triplets_fifo):
    """Called upon reception of command 'commit'. Checks and commit AU updates.
    >triplets_fifo: fifo of triplets, i.e: (AU, value, duration).
    Return: None
    """
    super(SrvMix_Dynamixel,self).commit_AUs(triplets_fifo)
    if not self._new_pt:
      return
    try:
      for AU, (nVal, dur) in self._new_pt.items():
        servo = self.daisy_chain[self.pmanager.get_ID(AU)]
        rawVal = self.pmanager.get_raw(AU, nVal)
        servo.speed = int(abs(servo.current_position - int(rawVal)) / dur)
        servo.goal_position = int(rawVal)
        LOG.debug("set #%i: rVal: %i, speed: %i", servo.id, servo.speed,
                  servo.goal_position)
    except SpineError as e:
      LOG.warning("can't update hardware: %s", e)
    self.daisy_chain.synchronize()
    print "AU commited"

  def get_AU__vals(self):
    """Read servos values and translate them to RAS internal AU format.
    Return: ( (AU,val), ... )
    """
    encs = self.get_encoders()
    AU__vals = zip(AUs, [encs.get(i) for i in range(self.nbr_axis)] )
    #TDL: normalize
    return AU__vals

  def get_encoders(self):
    """Read current encoder values.
    Return: 
    """

  def values_from_triplets(self, nvals):
    """Translates from nvals (and index in iterable) to iCub internal value.
    >nvals: normalized values from triplets
    Return: a yarp vector.
    """
    pass
#    return [ self.SW_limits[

##
## Simple utility to display servos' goal values
##
if __name__ == "__main__":
  import logging
  from utils import comm, conf, LOGFORMATINFO
  logging.basicConfig(level=logging.DEBUG, **LOGFORMATINFO)

  from utils import conf
  conf.load(name='lighty')

  print "getting ready now!"
  srv = get_networking_classes()()
