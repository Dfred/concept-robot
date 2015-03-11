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

