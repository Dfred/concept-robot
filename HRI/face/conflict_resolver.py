#!/usr/bin/python

# Lighthead-bot programm is a HRI PhD project at 
#  the University of Plymouth,
#  a Robotic Animation System including face, eyes, head and other
#  supporting algorithms for vision and basic emotions.  
# Copyright (C) 2010 Frederic Delaunay, frederic.delaunay@plymouth.ac.uk

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

import collections
import logging

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)

class ConflictSolver(object):
    def __init__(self):
        self.AUs = {}

    def set_available_AUs(self, available_AUs):
        """Define list of AUs available for a specific face.
         available_AUs: list of AU names.
        """
        for name in available_AUs:
            # target_coeffs, duration, elapsed, value
            self.AUs[name] = [(0,0) , .0 , .0, .0]
        LOG.info("Available AUs: %s" % sorted(self.AUs.keys()))

    def set_AU(self, name, target_value, duration):
        """Set targets for a specific AU, giving priority to specific inputs.
         name: AU name
         target_value: normalized value
         duration: time in seconds
        """
        duration = max(duration, .001)
        if self.AUs.has_key(name):
            self.AUs[name][:3] = ( ((target_value - self.AUs[name][3])/duration,
                                    self.AUs[name][3]),
                                   duration, 0)
        else:
            self.AUs[name+'R'][:3] = ( ((target_value-self.AUs[name+'R'][3])/duration,
                                        self.AUs[name+'R'][3]),
                                       duration, 0)
            self.AUs[name+'L'][:3] = ( ((target_value-self.AUs[name+'L'][3])/duration,
                                        self.AUs[name+'L'][3]),
                                       duration, 0)

    def solve(self):
        """Here we can set additional checks (eg. AU1 vs AU4, ...)
        """

    def update(self, time_step):
        """Update AU values. This function shall be called for each frame.
         time_step: time in seconds elapsed since last call.
        """
        #TODO: motion dynamics
        to_update = collections.deque()
        for id,info in self.AUs.iteritems():
            coeffs, duration, elapsed, value = info
            target = coeffs[0] * duration + coeffs[1]
            elapsed += time_step
            if elapsed >= duration:      # keep timing
                if value != target:
                    self.AUs[id][2:] = duration, target
                    to_update.append((id, target))
                continue

            up_value = coeffs[0] * elapsed + coeffs[1]
            self.AUs[id][2:] = elapsed, up_value
            to_update.append((id, up_value))
        return to_update

