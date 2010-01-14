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


BLINK_PROBABILITY=0.0
BLINK_DURATION=1

class FaceClient(comm.RemoteClient):
    """Remote connection handler: protocol parser."""

    def cmd_AU(self, argline):
        """if empty, returns current values. Otherwise, set them."""
        """argline: AU name + target value + duration"""
        if len(argline):
            try:
                self.server.set_AU(argline.split()[:3])
            except Exception, e:
                LOG.warning("[AU] bad argument line:'%s', caused: %s" %
                            (argline,e) )
        else:
            self.send_msg("AU ",str(self.server.focus))

    def cmd_f_expr(self, argline):
        """argline: facial expression id + intensity + duration."""
        try:
            self.server.set_f_expr(*argline.split())
        except Exception, e:
            LOG.warning("[f_expr] bad argument line:'%s', caused: %s" %
                        (argline,e) )

    def cmd_blink(self, argline):
        """argline: duration of the blink in seconds."""
        try:
            self.server.do_blink(float(argline))
        except Exception, e:
                LOG.warning("[blink] bad argument line:'%s', caused: %s" %
                            (argline,e) )

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
#        print "created AUs", AUs
        self.do_blink(0)

    def set_AU(self, name, target_value, duration):
        """Set a target value for a specific AU"""
        self.AUs[name][:3] = target_value, duration, 0
        print "set AU["+name+"]:", self.AUs[name]

    def set_f_expr(self, id, target, duration):
        """Set a facial expression."""
        #TODO: this is indeed way too simple...
        sets={ "raised_brows": ('01R', '02R', '01L', '02L'),
               "furrowed_brows": ('04R', '04L'),
               "squint": ('04R', '04L', '10R', '10R'),
               "smile": ('07R', '10R', '12R', '07L', '10L', '12L', '25'),
               "agreement_chin": ('17'),
               "begrudging_acceptance" : ('02R', '17'),
               "neutral": ('01R', '01L', '02R', '02L', '04R', '04L',
                           '10R', '10L', '12R', '12L', '25') # leave eyelids
               }
        for au in sets[id]:
            self.set_AU(au, float(target), float(duration))

    def set_blink_probability(self, p):
        self.blink_p = p

    def do_blink(self, duration):
        """set AUs to create a blink of any duration"""
        print "blink:", duration
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
            if val == target or elapsed > duration:
                continue        # let self.AUs[id] be reset on next command

            factor = not duration and 1 or elapsed/duration
            self.AUs[id][2:] = elapsed+time_step, val + (target - val)*factor


if __name__ == '__main__':
    try:
        server = Face(conf.conn_face)
    except UserWarning, err:
        comm.LOG.error("FATAL ERROR: %s (%s)", sys.argv[0], err)
        exit(-1)
    while server.is_readable:
        comm.loop(5, count=1)
    print "Face done"
