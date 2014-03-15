try:
  import dynamixel
  BAUD_RATES = sorted([ int(br[5:]) for br in dynamixel.BAUD_RATE.keys() ])
  MIN_BAUD_RATE = 7350                                  # 7343
  MAX_BAUD_RATE = 2000000
  ALL_BAUD_RATES = [ MAX_BAUD_RATE/i for i in range(1, 255) ]
except ImportError as e:
  BAUD_RATES = ("dynamixel unavailable")

## mandatory function returning server mixin and handler mixin classes.
def get_networking_classes():
  from implementation import SrvMix_Dynamixel, SpineHandlerMixin
  return (SrvMix_Dynamixel, SpineHandlerMixin)

