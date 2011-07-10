#!/usr/bin/python

# LightHead programm is a HRI PhD project at the University of Plymouth,
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


#
# FACE MODULE
#
# This module handles motion of the facial features.
#
# MODULES IO:
#===========
# INPUT: - vision (eye orientation for eyelid position) [event]
#        - affect (facial expressions) [event]
#        - planner (..eventually)
#

import sys
import time
import thread
import random
import collections
import logging
import numpy

from utils import comm, conf
import HRI

LOG = logging.getLogger(__package__)
conf.load()
if hasattr(conf,'DEBUG_MODE') and conf.DEBUG_MODE:
    LOG.setLevel(logging.DEBUG)

class Face_Handler(object):
    """Remote connection handler: protocol parser."""

    def __init__(self, *args):
        self.fifo = collections.deque()

    def cmd_AU(self, argline):
        """if empty, returns current values. Otherwise, set them.
         argline: sending_module AU_name  target_value  duration.
        """
        argline = argline.strip()
        if not len(argline):
            return
        try:
            au_name, value, duration = argline.split()[:3]
        except ValueError, e:
            LOG.error("[AU] wrong number of arguments (%s)",e)
            return
        try:
            value, duration = float(value), float(duration)
        except ValueError,e:
            LOG.error("[AU] invalid float (%s)", e)
            return
        if duration < self.server.MIN_ATTACK_TIME:
            LOG.warning("attack time (%s) too short, setting at %s.",
                        duration, self.server.MIN_ATTACK_TIME)
            duration = self.server.MIN_ATTACK_TIME
        if self.server.AUs.has_key(au_name):
            self.fifo.append((au_name, value, duration))
        elif self.server.AUs.has_key(au_name+'R'):
            self.fifo.append((au_name+'R',value,duration))
            self.fifo.append((au_name+'L',value,duration))
        else:
            LOG.warning("[AU] invalid AU (%s)", au_name)
            return

    def cmd_commit(self, argline):
        """Commit buffered updates"""
        self.server.set_AUs(self.fifo)
        self.fifo.clear()


class Face_Server(object):
    """Main facial feature animation module

    Also maintains consistent muscle activation.
    AU value is normalized: 0 -> AU not streched, 1 -> stretched to max
    Setting an AU target value overwrites previous target.
    On target overwrite, interpolation starts from current value.
    """

    MIN_ATTACK_TIME = 0.001     # in seconds.

    def __init__(self):
        self.AUs = None
        self.updates = []
        self.thread_id = thread.get_ident()
        self.FP = HRI.FeaturePool()         # dict of { origin : numpy.array }

    def set_available_AUs(self, available_AUs):
        """Define list of AUs available for a specific face.
         available_AUs: list of AUs (floats) OR list of tuples (AU, init_value)
        """
        available_AUs.sort()
        a = numpy.zeros((len(available_AUs), 4), dtype=numpy.float32)
        if type(available_AUs[0]) == tuple:
            available_AUs, init_values = zip(*available_AUs)
            a[:,0] = a[:,3] = numpy.array(init_values)
        # { AU_name : numpy array [target, remaining, coeff, value] }
        self.AUs = dict(zip(available_AUs,a))
        # set region-based AUs
#        for name in SUPPORTED_ORIGINS:
#            self.FP.add_feature(name, self.subarray_from_origin(name))
        self.FP['face'] = a
        LOG.info("Available AUs:\n")
        for key in sorted(self.AUs.keys()):
            LOG.info("%5s : %s", key, self.AUs[key])

    def set_AUs(self, iterable):
        """Set targets for a specific AU, giving priority to specific inputs.
        iterable: array of floats: AU, normalized target value, duration in sec.
        """
        if self.thread_id != thread.get_ident():
            self.threadsafe_start()
        for AU, target, attack in iterable:
            try:
                self.AUs[AU][:-1]= target,attack,(target-self.AUs[AU][3])/attack
            except IndexError:
                LOG.warning("AU '%s' not found", AU)
        if self.thread_id != thread.get_ident():
            self.threadsafe_stop()

    def update(self, time_step):
        """Update AU values. This function shall be called for each frame.
         time_step: time in seconds elapsed since last call.
        #TODO: motion dynamics
        """
        if self.thread_id != thread.get_ident():
            self.threadsafe_start()
        data = self.FP['face']
        actives_idx = data[:,1] > 0  # AUs with remaining time
        if not any(actives_idx):
            return {}
        data[actives_idx,3] += data[actives_idx,2] * time_step
        data[:,1] -= time_step
        # finish off shortest activations
        overgone_idx = data[:,1]< self.MIN_ATTACK_TIME
        data[overgone_idx, 1] = 0
        data[overgone_idx, 3] = data[overgone_idx, 0]
        if self.thread_id != thread.get_ident():
            self.threadsafe_stop()
        return self.AUs

    def solve(self):
        """Here we can set additional checks (eg. AU1 vs AU4, ...)
        """

try:
    conf.load()
    backend = __import__(conf.mod_face['backend'], fromlist=['HRI.face'])
except ImportError, e:
    print
    print '*** FACE MISCONFIGURATION ***'
    print 'check in your config file for the value of face_backend !'
    print 'for your information:', e
    sys.exit(-1)    # crude but avoids loads of further output.


if __name__ == '__main__':
    conf.name = sys.argv[-1]

    try:
        server = comm.create_server(Face_Server, Face_Handler, conf.conn_face,
                                    (False,False))
    except UserWarning, err:
        comm.LOG.error("FATAL ERROR: %s (%s)", sys.argv[0], err)
        exit(-1)
    server.serve_forever()
    LOG.debug("Face server done")
