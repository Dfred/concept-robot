# -*- coding: utf-8 -*-

# ARAS is the open source software (OSS) version of the basic component of
# Syntheligence's software suite. This software is provided for academic
# research only. Any other use is not permitted.
# Syntheligence SAS is a robotics and software company established in France.
# For more information, visit http://www.syntheligence.com .

# ARAS stands for Abstract Robotic Animation System, and features actuator,
# sensor, animation and remote management high-level interfaces.
# Copyright 2013 Syntheligence, fdelaunay@syntheligence.com

# This software was originally named LightHead, the Human-Robot-Interaction part
# of the CONCEPT project, which took place at the University of Plymouth (UK).
# The project originated as the PhD pursued by Frédéric Delaunay, who was under
# the supervision of Prof. Tony Belpaeme.
# This PhD project started in late 2008 and ended in late 2011.
# Visit http://www.tech.plym.ac.uk/SoCCE/CONCEPT/ for more information.

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

"""Backend for Robotis' Dynamixel.
Tested with:    * AX-12A / AX-12+
                *
"""
import math
import logging

from . import BAUD_RATES
from dynamixel_ext import DynamixelNetworkEx, DynamixelEx
from dynamixel import SerialStream

from utils import EXIT_DEPEND, EXIT_CONFIG
from utils.conf import CONFIG
from RAS.spine import (SpineServerMixin, SpineHandlerMixin, PoseManager,
                       SpineError)
#from RAS.au_pool import 

LOG = logging.getLogger(__package__)

OFFSET = 512                                            # goal value @0deg
## Doc conflict: .29*1024 = 296.96 , but 300/1024 ~= .293 (~3 degrees)
PIF = (1024-OFFSET)/math.radians(296.96)                # pi factor

  
class SrvMix_Dynamixel(SpineServerMixin):
  """Spine implementation for Dynamixel servos.
  """

  def __init__(self):
    """
    """
    self.name = "dynamixels"
    super(SrvMix_Dynamixel,self).__init__()             ## sets self.SW_limits
    self.daisy_chain = None
    self.pmanager.set_hardware_infos( { AU : (PIF, OFFSET, 0, 1023) for AU in 
                                        self.pmanager.ID2AU.values() } )
    self.__init_hardware()
    self.pmanager.get_poseFromHardware = self.get_poseFromHardware.__get__(
      self.pmanager, PoseManager)
    self.AUs.set_availables(*zip(*self.pmanager.get_poseFromHardware().items()))
    self.ready()

  def __init_hardware(self):
    """
    """
    portID, baudsR = CONFIG[self.name+"_serial_port"]
    try:
      #XXX these arguments are passed over to python's serial module
      serial = SerialStream(port=portID, baudrate=baudsR,
                            timeout=.1)
      LOG.debug("opened port %s @%ibps", portID, baudsR)
      self.daisy_chain = DynamixelNetworkEx(serial)
    except ValueError as e:
      LOG.fatal("Cannot start dynamixel: %s", e)

    pose_manager_info = {}
    for ID, AU in self.pmanager.ID2AU.iteritems():
      self.daisy_chain.add_dynamixel(ID)
      servo = self.daisy_chain[ID]
      servo.read_all()
      LOG.debug("dynamixel #%i:\n"
                "\tstatus_return_level: %i\n"
                "\tError status (alarm shutdown): %s\n"
                "\tcurrent position: %i\n"
                "\tcurrent temperature: %i°C\n",
                ID, servo.status_return_level, 
                self.daisy_chain.error_text(servo.alarm_shutdown),
                servo.goal_position, servo.current_temperature)
      servo.moving_speed = 1000                                  ## 50%
      servo.synchronized = True                                 ## only internal
      servo.torque_enable = False
      servo.torque_limit = 1023                                 ## 100%
      servo.max_torque = 512

      if self.AUs.has_key(AU):
        LOG.warning("AU %s already present in pool.", AU)
##TDL use that if needed, (requires some traffic on serial).
#    LOG.debug("serial statistics: %s", self.daisy_chain.dump_statistics())

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
    for ID, rVal in self.pmanager.get_rawNeutralPose().items():
      LOG.debug("servo #%i setting from %i -> %i", ID,
                self.daisy_chain[ID].goal_position, rVal)
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