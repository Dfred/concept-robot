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

"""Entry point for most backends. Should also ensure conf is properly loaded
before starting the show.
"""
from utils import print_remaining_threads, EXIT_UNKNOWN

if __name__ == "__main__":
  import time
  import RAS
  ## threaded server flag , threaded clients flag 
  RAS_THREAD_INFO = (False, True)
  try:
    server = RAS.initialize(RAS_THREAD_INFO,"lighty")
  except StandardError as e:
    print "error initializing the RAS:", e
    exit(EXIT_UNKNOWN)

  print "starting the RAS"
  server.serve_forever()
  time.sleep(.5)
  print_remaining_threads(prefix="remaining threads:\n\t")
  print "RAS finished"
