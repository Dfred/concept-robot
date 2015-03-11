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

import sys
from time import time

class SimpleFPS(object):
    """
    """

    def __init__(self, rate = 5):
        """
        """
        self.fps = 0
        self.rate = rate
        self.update_nbr = 0
        self.prev_time = time()

    def update(self):
        """
        """
        self.update_nbr += 1
        if self.update_nbr >= self.rate:
            now = time()
            self.fps = self.update_nbr/(now - self.prev_time)
            self.update_nbr = 0
            self.prev_time = now
        return self.fps

    def show(self):
        """
        """
        sys.stdout.write('FPS: %s\r' % self.fps)
        sys.stdout.flush()


if __name__ == "__main__":
    # use timeit for proper profiling
    for fps in (SimpleFPS(),):
        print fps
        for i in range(100000):
            fps.update()
            fps.show()
        print
    
