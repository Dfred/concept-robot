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
import collections
import asyncore
import logging

LOG = logging.getLogger("face-srv")
LOG.setLevel(logging.DEBUG)

import comm
import conf
from conflict_resolver import ConflictSolver

ORGN_FACE = 'face'
ORGN_GAZE = 'gaze'
ORGN_LIPS = 'lips'
ORGN_HEAD = 'head'
ORIGINS = (ORGN_GAZE, ORGN_FACE, ORGN_LIPS, ORGN_HEAD)

class FaceClient(comm.RequestHandler):
    """Remote connection handler: protocol parser."""
    
    def __init__(self, *args):
        self.origin = None
        self.fifos = {
            ORGN_FACE : collections.deque(),
            ORGN_GAZE : collections.deque(),
            ORGN_LIPS : collections.deque(),
            ORGN_HEAD : collections.deque()
            }
        self.fifo = None                                # pointer
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
            LOG.warning("[origin] unknown origin: '%s'", origin)
            return
        self.fifo = self.fifos[origin]
        self.origin = origin

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
                self.fifo.append((au_name, float(value), float(duration)))
            except FloatException:
                LOG.warning("[AU] invalid float argument")
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
        for origin in ORIGINS:
            for au, target, attack in self.fifos[origin]:
                try:
                    self.server.conflict_solver.set_AU(au, target, attack)
                except KeyError, e:
                    LOG.warning("[AU] bad argument line:'%s', AU %s not found",
                                au+" %f %f" % (target, attack), e)
            self.fifos[origin].clear()

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



class Face(comm.BaseServ):
    """Main facial feature animation module - server

    Also maintains consistent muscle activation.
    AU value is normalized: 0 -> AU not streched, 1 -> stretched to max
    Setting an AU target value overwrites previous target.
    On target overwrite, interpolation starts from current value.
    """

    EYELIDS = ['43R', '43L', '07R', '07L']

    def __init__(self):
        self.conflict_solver = ConflictSolver()
        comm.BaseServ.__init__(self)

    def set_available_AUs(self, AUs):
        return self.conflict_solver.set_available_AUs(AUs)

    def get_all_AU(self):
        return [(item[0],item[1][0],item[1][1])
                for item in self.conflict_solver.AUs.iteritems()]

    def get_AU(self, name):
        return self.conflict_solver.AUs[name]

    def update(self, time_step):
        return self.conflict_solver.update(time_step)


if __name__ == '__main__':
    conf.name = sys.argv[-1]
    conf.load()
    try:
        server = comm.createServer(Face, FaceClient, conf.conn_face)
    except UserWarning, err:
        comm.LOG.error("FATAL ERROR: %s (%s)", sys.argv[0], err)
        exit(-1)
    server.serve_forever()
    LOG.debug("Face done")
