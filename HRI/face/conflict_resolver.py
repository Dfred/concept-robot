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
LOG.setLevel(logging.DEBUG)

class ConflictSolver(object):
    def __init__(self):
        self.AUs = {}
        self.face = {}

    def set_available_AUs(self, available_AUs):
        """Define list of AUs available for a specific face.
         available_AUs: list of AU names.
        """
        for name in available_AUs:
            self.AUs[name] = [0.0]*4  # target_val, duration, elapsed, value
        LOG.info("Available AUs: %s" % sorted(self.AUs.keys()))

    def set_AU(self, origin, name, target_value, duration):
        """Set targets for a specific AU, giving priority to specific inputs.
         origin: name of the input
         name: AU name
         target_value: normalized value
         duration: time in seconds
        """
        try:
            self.AUs[name][:3] = target_value, duration, 0
        except KeyError:
            if name[:-1] in "LR":
                raise Exception('AU %s is not defined' % name)
            self.AUs[name+'R'][:3] = target_value, duration, 0
            self.AUs[name+'L'][:3] = target_value, duration, 0
            LOG.debug("set AU[%sR/L]: %s" % (name, self.AUs[name+'R']))
        else:
            LOG.debug("set AU[%s]: %s" % (name, self.AUs[name]))

    def solve(self):
        """Solve target conflicts.
        """
        

    def update(self, time_step):
        """Update AU values. This function shall be called for each frame.
         time_step: time in seconds elapsed since last call.
        """
        #TODO: motion dynamics
        to_update = collections.deque()
        for id,info in self.AUs.iteritems():
            target, duration, elapsed, value = info
            if elapsed >= duration:      # be active for the required amount of time
                if value != target:
                    self.AUs[id][2:] = duration, target
                    to_update.append((id, target))
                continue

            factor = not duration and 1 or elapsed/duration
            up_value = value + (target - value)*factor
#            print id,"value",value,"target",target,"duration",duration,"elapsed",elapsed

            self.AUs[id][2:] = elapsed+time_step, up_value
            to_update.append((id, up_value))
        return to_update

