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

import sys, random, time

import asyncore
import logging

LOG = logging.getLogger("face-srv")
LOG.setLevel(logging.DEBUG)

import comm
import conf
from conflict_resolver import ConflictSolver

BLINK_PROBABILITY=0.0
BLINK_DURATION=1        # in seconds
ORGN_FACE = 'face'
ORGN_GAZE = 'gaze'
ORGN_LIPS = 'lips'
ORGN_HEAD = 'head'
ORIGINS = (ORGN_GAZE, ORGN_FACE, ORGN_LIPS, ORGN_HEAD)

class FaceClient(comm.RequestHandler):
    """Remote connection handler: protocol parser."""
    
    def __init__(self, *args):
        self.origin = None
        self.origin_index = 0
        comm.RequestHandler.__init__(self, *args)       # keep last call.

    def cmd_origin(self, argline):
        """Sets the channel type.
        This stills allow for multiplexed channel or multi-channel since each
         instance represents a channel. In multiplexed channel, the sender need
         to ensure not mixing AUs whitout setting origin first.
        """
        origin = argline.strip()
        try:
            index = ORIGINS.index(origin)
        except ValueError:
            LOG.warning("[origin] unknown origin: %s", origin)
            return
        # Trick enforcing a stack of potential target overwrites for conflicts.
        if index < self.origin_index:
            LOG.warning("[origin] %s occurs too late, ignored!", origin)
            return
        self.origin = origin
        self.origin_index = index

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


    def cmd_AU(self, argline):
        """if empty, returns current values. Otherwise, set them.
         argline: sending_module AU_name  target_value  duration.
        """
        if len(argline):
            if self.origin == None:
                LOG.warning("[AU] origin not yet set (%s)", argline)
                return
            try:
                au_name, value, duration = argline.split()[:3]
                self.server.conflict_solver.set_AU(au_name,
                                                   float(value),
                                                   float(duration))
            except Exception, e:
                LOG.warning("[AU] bad argument line:'%s', caused: %s" %
                            (argline,e) )
        else:
            msg = ""
            AU_info = self.server.get_all_AU()
            AU_info.sort()
            # name, target, duration
            for triplet in AU_info:
                msg += "AU %s\t%.3f\t%.3f\n" % triplet
            self.send_msg(str(msg))


    def cmd_f_expr(self, argline):
        # TODO: rewrite player to get rid of this function
        """argline: facial expression id + intensity + duration.
        That function is for the humanPlayer (ie. would eventually disappear)
        """
        try:
            self.server.set_f_expr(*argline.split())
        except Exception, e:
            LOG.warning("[f_expr] bad argument line:'%s', caused: %s" %
                        (argline,e) )

    def cmd_commit(self, argline):
        """Commit buffered updates"""
        self.origin_index = 0
        # TODO: AU buffer flip (watch out for attack differences)

    def cmd_blink(self, argline):
        """argline: duration of the blink in seconds."""
        try:
            self.server.do_blink(float(argline))
        except Exception, e:
            LOG.warning("[blink] bad argument line:'%s', caused: %s" %
                        (argline,e) )


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
        return [(item[0],item[1][0],item[1][1])
                for item in self.conflict_solver.AUs.iteritems()]

    def get_AU(self, name):
        return self.conflict_solver.AUs[name]

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
