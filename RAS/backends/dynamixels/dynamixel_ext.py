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

try:
  import dynamixel
except ImportError as e:
  raise ImportError("dynamixel for python could not be imported (%s)."
                    "Try with easy-install or pip" % e)

class DynamixelEx(dynamixel.Dynamixel):
  """
  """
  def __setattr__(self, register, value):
    """Enforce valid registers"""
    #XXX there must be a better way!
    assert register in ('_id','_dyn_net', '_synchronized', 
                        'cache', 'changed', 'id', 'led', 'synchronized',
                        'alarm_led', 'alarm_shutdown', 'baud_rate',
                        'cw_angle_limit', 'ccw_angle_limit',
                        'ccw_compliance_margin', 'cw_compliance_margin',
                        'ccw_compliance_slope', 'cw_compliance_slope',
                        'goal_position',
                        'high_voltage_limit', 'low_voltage_limit',
                        'max_torque', 'moving_speed', 
                        'punch', 'registered_instruction',
                        'return_delay', 'status_return_level',
                        'torque_enable', 'torque_limit', 'temperature_limit'
                        ), "invalid attribute: %s" % register
    if register in ("baud_rate", "id"):
      print "--- WARNING: SETTING %s @%i !!! ----" % (register, value)
    dynamixel.Dynamixel.__setattr__(self, register, value)


class DynamixelNetworkEx(dynamixel.DynamixelNetwork):
  """
  """
  def add_dynamixel(self, dynamixel_id):
    """Adds a dynamixel by ID without scanning.
    """
    if not self.ping(dynamixel_id):
      raise ValueError("servo #%i not responding to ping." % dynamixel_id)
    self._dynamixel_map[dynamixel_id] = DynamixelEx(dynamixel_id, self)

