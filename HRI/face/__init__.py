#!/usr/bin/python

#
# This module handle motion of the facial features.
# INPUT: - eye orientation to compute eyelid position
#        - emotion (facial expression)
#        - planner (eventually)
#

import sys, random

import asyncore
import logging

logging.basicConfig(level=logging.WARNING)
LOG = logging.getLogger("face-srv")

import comm
import conf


BLINK_PROBABILITY=0.02
BLINK_DURATION=1

class FaceClient(comm.RemoteClient):
    """Remote connection handler: protocol parser."""

    def cmd_AU(self, argline):
        """args: if empty, returns current values. Otherwise, set them."""
        if len(argline):
            try:
                self.server.set_AU(argline.split()[:3])
            except Exception, e:
                LOG.warning("[AU] bad argument line:'%s', caused: %s" %
                            (argline,e) )
        else:
            self.send_msg("AU ",str(self.server.focus))

    def cmd_shutdown(self, args):
        """args: unused."""
        self.server.shutdown()



class Face(comm.BasicServer):
    """Main facial feature animation module - server"""
    """
    Also designed to maintain consistent muscle activation.
    This class holds all AU values, so you can also import this module.
    AU are normalized: 0 should/may be AU streched to an extreme, 1 to the other
    Resetting an AU would override the unfinished motion, starting from whenever
     the command has been received.
    """

    EYELIDS = ['43R', '43L', '07R', '07L']

    def __init__(self, addr_port, AUs):
        comm.BasicServer.__init__(self, FaceClient)
        self.listen_to(addr_port)
        self.blink_p = BLINK_PROBABILITY
        self.AUs = {}
        for act in AUs:
            self.AUs[act.name] = [0]*4  # target_val, duration, elapsed, value
        print "created AUs", AUs
        self.do_blink(0)

    def set_AU(self, name, target_value, duration):
        """Set a target value for a specific AU"""
        self.AUs[name][:3] = target_value, duration, 0
        print "set AU["+name+"]:", self.AUs[name]

    def set_blink_probability(self, p):
        self.blink_p = p

    def do_blink(self, duration):
        """set AUs to create a blink of any duration"""
        self.AUs["43R"][1:] =  duration, 0, .8
        self.AUs["07R"][1:] =  duration, 0, .2
        self.AUs["43L"][1:] =  duration, 0, .8
        self.AUs["07L"][1:] =  duration, 0, .2

    def update(self, time_step):
        """Update AU values."""
        if self.blink_p > random.random():
            self.do_blink(BLINK_DURATION)
        #TODO: use motion dynamics
        for id,info in self.AUs.iteritems():
            target, duration, elapsed, val = info
            if val == target: #or elapsed > duration:
                continue        # let self.AUs[id] be reset on next command

            factor = not duration and 1 or elapsed/duration
            self.AUs[id][2:] = elapsed+time_step, val + (target - val)*factor


if __name__ == '__main__':
    try:
        server = Face(conf.face_addr)
    except UserWarning, err:
        comm.LOG.error("FATAL ERROR: %s (%s)", sys.argv[0], err)
        exit(-1)
    while server.is_readable:
        comm.loop(5, count=1)
    print "Face done"
