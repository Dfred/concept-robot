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

