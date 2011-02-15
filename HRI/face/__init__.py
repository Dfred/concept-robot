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

import comm
import conf

LOG = logging.getLogger(__package__)
conf.load()
if hasattr(conf,'DEBUG_MODE') and conf.DEBUG_MODE:
    LOG.setLevel(logging.DEBUG)

# conversion table for float-based AU identification
float_to_AUname = { 
    -1:'01L', 1:'01R', -2:'02L', 2:'02R', -4:'04L', 4:'04R', -5:'05L', 5:'05R',
     -6:'06L', 6:'06R', -7:'07L', 7:'07R', -8:'08L', 8:'08R', -9:'09L', 9:'09R',
     -10:'10L', 10:'10R', -11:'11L', 11:'11R', -12:'12L', 12:'12R',
     -13:'13L', 13:'13R', -14:'14L', 14:'14R', -15:'15L', 15:'15R',
     -16:'16L', 16:'16R', .17:'17', -18:'18L', 18:'18R', -20:'20L', 20:'20R',
     -21:'21L', 21:'21R', -22:'22L', 22:'22R', -23:'23L', 23:'23R',
     -24:'24L', 24:'24R', .25:'25' , 26:'26', -28:'28L', 28:'28R', .31:'31',
     -32:'32L', 32:'32R', -33:'33L', 33:'33R', -38:'38L', 38:'38R',
     -39:'39L', 39:'39R', -61.5:'61.5L', 61.5:'61.5R', .635:'63.5'
}
AUname_to_float = dict(zip(float_to_AUname.values(),float_to_AUname.keys()))

class FaceProtocolError(comm.ProtocolError):
    pass

class FaceError(comm.CmdError):
    pass

class Face_Handler(object):
    """Remote connection handler: protocol parser."""
    
    def __init__(self, *args):
        self.fifo = collections.deque()

    def cmd_AU(self, argline):
        """if empty, returns current values. Otherwise, set them.
         argline: sending_module AU_name  target_value  duration.
        """
        if len(argline):
            try:
                au_name, value, duration = argline.split()[:3]
            except ValueError, e:
                raise FaceProtocolError("[AU] wrong number of arguments (%s)",e)
            try:
                value, duration = float(value), float(duration)
                self.fifo.append((AUname_to_float[au_name], value, duration))
            except ValueError,e:
                raise FaceProtocolError("[AU] invalid float (%s)", e)
            except KeyError, e:
                if not AUname_to_float.has_key(au_name+'R'):
                    raise FaceProtocolError("[AU] invalid float (%s)", e)
                self.fifo.append((AUname_to_float[au_name+'R'],value,duration))
                self.fifo.append((AUname_to_float[au_name+'L'],value,duration))
        else:
            msg = ""
            AU_info = self.server.get_all_AU()
            AU_info.sort()
            # name, target, duration
            for triplet in AU_info:
                msg += "AU {0[0]:5s} {0[1]} {0[2]:.3f}\n".format(triplet)
            self.send_msg(str(msg))

    def cmd_commit(self, argline):
        """Commit buffered updates"""
        self.server.set_AUs(self.fifo)
        self.fifo.clear()

    # def cmd_start(self, argline):
    #     try:
    #         start = float(argline.strip())
    #     except Exception, e:
    #         LOG.warning("[origin] bad argument line:'%s', caused: %s" %
    #                     (argline,e) )

    #     self.start_time = float(start)
    #     if self.start_time - time.time() < 0:
    #         LOG.warning("[origin] time received is elapsed: [r:%s c:%f]" %
    #                     (start, time.time()) )
    #     if self.start_time - time.time() > 30:
    #         LOG.warning("[origin] time received > 30s in future %s" % start)



class Face_Server(object):
    """Main facial feature animation module

    Also maintains consistent muscle activation.
    AU value is normalized: 0 -> AU not streched, 1 -> stretched to max
    Setting an AU target value overwrites previous target.
    On target overwrite, interpolation starts from current value.
    """

    COLS = 6

    def __init__(self):
        # array of : AU_name(in float), coeff, , duration, elapsed, value
        self.AUs = None
        self.updates = []
        self.thread_id = thread.get_ident()

    def set_featurePool(self, feature_pool):
        """Attach the feature_pool for further registration of self.AUs .
        feature_pool: a dict of { origin : numpy.array }
        """
        self.FP = feature_pool

    def index(self, AU):
        """Returns index of specified AU or raises IndexError if not found.
        AU: float
        """
        return numpy.nonzero(self.AUs[:,0] == AU)[0][0]

    def get_AU(self, AU):
        return self.AUs[numpy.where(self.AUs[:,0] == AU)[0][0],:]

    def get_all_AU(self):
        return self.AUs

    def set_available_AUs(self, available_AUs):
        """Define list of AUs available for a specific face.
         available_AUs: list of AUs (floats)
        """
        self.AUs = numpy.zeros((len(available_AUs), self.COLS), 
                               dtype=numpy.float32)
        self.AUs[:,0] = sorted([AUname_to_float[au] for au in available_AUs])
#        for name in SUPPORTED_ORIGINS:
#            self.FP.add_feature(name, self.subarray_from_origin(name))
        self.FP['face'] = self.AUs
        LOG.info("Available AUs:\n%s" % self.AUs[:,0])

    def set_AUs(self, iterable):
        """Set targets for a specific AU, giving priority to specific inputs.
        iterable: array of floats: AU, normalized target value, duration in sec.
        """
        if self.thread_id != thread.get_ident():
            self.threadsafe_start()
        for AU, target_value, duration in iterable:
            duration = max(duration, .001)
            try:
                AU_data = self.AUs[self.index(AU),:]
            except IndexError:
                LOG.warning('AU %s not found', AU)
            else:
                AU_data[1:5] = ((target_value-AU_data[3])/duration, AU_data[3],
                                duration, 0)
        if self.thread_id != thread.get_ident():
            self.threadsafe_stop()

    def update(self, time_step):
        """Update AU values. This function shall be called for each frame.
         time_step: time in seconds elapsed since last call.
        """
        if self.thread_id != thread.get_ident():
            self.threadsafe_start()
        #TODO: motion dynamics
        to_update = collections.deque()
        self.AUs[:,4] += time_step
        for AU, coeff, offset, duration, elapsed, value in self.AUs:
            target = coeff * duration + offset
            if elapsed >= duration:      # keep timing
                if value != target:
                    self.AUs[AU][4:] = duration, target
                    to_update.append((AU, target))
                continue

            up_value = coeff * elapsed + offset
            self.AUs[AU][4:] = elapsed, up_value
            to_update.append((AU, up_value))
        if self.thread_id != thread.get_ident():
            self.threadsafe_start()
        return to_update

    def solve(self):
        """Here we can set additional checks (eg. AU1 vs AU4, ...)
        """

try:
    conf.load()
    backend = getattr(__import__('face.'+conf.face_backend),conf.face_backend)
    main = backend.main
except ImportError, e:
    print 
    print '*** FACE MISCONFIGURATION ***'
    print 'check in your config file for the value of face_backend !'
    print 'for your information:', e
    sys.exit(-1)    # crude but avoids loads of further output.


if __name__ == '__main__':
    conf.name = sys.argv[-1]

    try:
        server = comm.create_server(backend.FaceServer, backend.FaceClient,
                                    conf.conn_face, (False,False))
    except UserWarning, err:
        comm.LOG.error("FATAL ERROR: %s (%s)", sys.argv[0], err)
        exit(-1)
    server.serve_forever()
    LOG.debug("Face server done")
