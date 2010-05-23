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
from constraint_solver import ConflictSolver

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
            for triplet in self.server.get_all_AU():
                self.send_msg("AU %s %.3f %.3f" % triplet) # name, target, duration

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
    """Main facial feature animation module - server

    Also maintains consistent muscle activation.
    AU value is normalized: 0 -> AU not streched, 1 -> stretched to max
    Setting an AU target value overwrites previous target.
    On target overwrite, interpolation starts from current value.
    """

    EYELIDS = ['43R', '43L', '07R', '07L']

    def __init__(self):
        self.blink_p = BLINK_PROBABILITY
        self.conflict_solver = ConflictSolver()
        LOG.info("Face started")
        
    def set_available_AUs(self, AUs):
        return self.conflict_solver.set_available_AUs(AUs)

    def get_all_AU(self):
        return ((item[0],item[1][:2],item[1][3])
                for item in self.conflict_solver.iteritems())

    def update(self, time_step):
        if self.blink_p > random.random():
            self.do_blink(BLINK_DURATION)
        return self.conflict_solver.update(time_step)

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
            self.conflict_solver.set_AU('f_expr', au, float(target), float(duration))

    def set_blink_probability(self, p):
        self.blink_p = p

    def do_blink(self, duration):
        """set AUs to create a blink of any duration"""
        LOG.debug("blink: %ss." % duration)
        self.conflict_solver.set_AU('f_expr', "43", .8, duration)
        self.conflict_solver.set_AU('f_expr', "07", .2, duration)


if __name__ == '__main__':
    conf.load()
    try:
        server = comm.createServer(Face, FaceClient, conf.conn_face)
    except UserWarning, err:
        comm.LOG.error("FATAL ERROR: %s (%s)", sys.argv[0], err)
        exit(-1)
    server.serve_forever()
    LOG.debug("Face done")
