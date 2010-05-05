#!/usr/bin/python

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

import sys, random

import asyncore
import logging

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("face-srv")

import comm
import conf


BLINK_PROBABILITY=0.0
BLINK_DURATION=1        # in seconds

class FaceClient(comm.RequestHandler):
    """Remote connection handler: protocol parser."""

    def cmd_AU(self, argline):
        """if empty, returns current values. Otherwise, set them."""
        """argline: AU_name  target_value  duration"""
        if len(argline):
            try:
                au_name, value, duration = argline.split()[:3]
                self.server.set_AU(au_name, float(value), float(duration))
            except Exception, e:
                LOG.warning("[AU] bad argument line:'%s', caused: %s" %
                            (argline,e) )
        else:
            self.send_msg("AU ",str(self.server.focus))

    def cmd_f_expr(self, argline):
        # TODO: rewrite player to get rid of this function
        """argline: facial expression id + intensity + duration.
        That function is for the humanPlayer (ie. would eventually disappear)
        """
        try:
            self.server.set_f_expr(*argline.split())
        except Exception:
            LOG.warning("[f_expr] bad argument line:'%s', caused:" % argline)

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



class Face(object):
    """Main facial feature animation module - server"""
    """
    Also designed to maintain consistent muscle activation.
    This class holds all AU values, so you can also import this module.
    AU are normalized: 0 should/may be AU streched to an extreme, 1 to the other
    Resetting an AU would override the unfinished motion, starting from whenever
     the command has been received.
    """

    EYELIDS = ['43R', '43L', '07R', '07L']

    def __init__(self):
        self.blink_p = BLINK_PROBABILITY
        self.AUs = {}

    def set_available_AUs(self, available_AUs):
        for act in available_AUs:
            self.AUs[act.name] = [0]*4  # target_val, duration, elapsed, value
        LOG.info("Available AUs: %s" % sorted(self.AUs.keys()))
        self.do_blink(0)
        LOG.info("Face started")

    def set_AU(self, name, target_value, duration):
        """Set a target value for a specific AU"""
        try:
            self.AUs[name][:3] = target_value, duration, 0
        except KeyError:
            if len(name) != 2:
                raise Exception('AU %s is not defined' % name)
            self.AUs[name+'R'][:3] = target_value, duration, 0
            self.AUs[name+'L'][:3] = target_value, duration, 0
            LOG.debug("set AU[%sR/L]: %s" % (name, self.AUs[name+'R']))
        else:
            LOG.debug("set AU[%s]: %s" % (name, self.AUs[name]))

    def set_f_expr(self, id, target, duration):
        """Set a facial expression."""
        #TODO: this is indeed way too simple...
        sets={ "raised_brows": ('01', '02'),
               "furrowed_brows": ('04'),
               "squint": ('04', '10'),
               "smile": ('07', '10', '12', '25'),
               "agreement_chin": ('17'),
               "begrudging_acceptance" : ('02R', '17'),
               "neutral": ('01','02','04',      # leave eyelids
                           '09','10','12','15','16','17','18','20','25'), 
               "thought" : ('02', '15', '17'),
               "understanding" : ('07', '09', '12', '16'),
               "misunderstanding" : ('02', '04', '07', '09', '15', '16', '18'),
               "unsure_understanding" : ('02', '09', '20')
               }
        for au in sets[id]:
            self.set_AU(au, float(target), float(duration))

    def set_blink_probability(self, p):
        self.blink_p = p

    def do_blink(self, duration):
        """set AUs to create a blink of any duration"""
        LOG.debug("blink: %ss." % duration)
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
    conf.load()
    try:
        server = comm.createServer(Face, FaceClient, conf.conn_face)
    except UserWarning, err:
        comm.LOG.error("FATAL ERROR: %s (%s)", sys.argv[0], err)
        exit(-1)
    server.serve_forever()
    LOG.debug("Face done")
