#!/usr/bin/python

#
# This module handle the gazing of the face as well as eyes' iris diameter.
# Gazing can be set by specifying:
#       a focus point (vector3)
#       an rotation axis (vector3) and an angle (radians)
# INPUT: - planner
#        - emotion (iris diameter + saccades)
#
# OUTPUT: * face module (to update eyelids)
#

import sys

import asyncore
import logging

logging.basicConfig(level=logging.WARNING)
LOG = logging.getLogger("gaze-srv")

import comm
import conf


class GazeClient(comm.RemoteClient):
    """Remote connection handler: protocol parser."""

    def cmd_focus(self, argline):
        """args: if empty, returns current focus coords. Otherwise, set them."""
        if len(argline):
            try:
                args = [ float(arg) for arg in argline.split() ]
                self.server.set_focus(tuple(args[:3]))
            except Exception, e:
                LOG.warning("[focus] bad argument line:'%s', caused: %s" %
                            (argline,e) )
        else:
            self.send_msg("focus",str(self.server.focus))

    def cmd_orientation(self, argline):
        """args: if empty, returns current orientation. Otherwise, set it."""
        if len(argline):
            try:
                args = [ float(arg) for arg in argline.split() ]
                self.server.set_orientation(args[:3], args[3], args[4])
            except Exception, e:
                LOG.warning("[orientation] bad argument line:'%s', caused: %s" %
                            (argline,e) )
        else:
            self.send_msg("orientation ",str(self.server.orientation))

    def cmd_shutdown(self, args):
        """args: unused."""
        self.server.shutdown()



class Gaze(comm.BasicServer):
    """Main gaze module - server"""
    """
    Designed to receive on-demand queries from external systems.
    This class holds all information, so you can also import this module.
    """

    def __init__(self, addr_port):
        comm.BasicServer.__init__(self, GazeClient)
        self.listen_to(addr_port)
        self.focus = (.0, -5.0, 0.0)
        self.orientation = [0, 0.0, (.0,.0,.0)]         # target, angle, vector
        self.duration = 0                               # eye movement duration
        self.elapsed = 0
        self.changed = None

    def update(self, time_step):
#        factor = not self.duration and 1 or self.elapsed/self.duration
#        self.orientation[1] += (self.orientation[0]-self.orientation[1])*factor
#        self.elapsed += time_step
        pass

    def set_focus(self, pos):
        """Set focus (1 vector3)."""
        self.focus = pos
        self.changed = 'f'
        self.send_focus()
        
    def set_orientation(self, vector3, angle, duration):
        """Just set eyes orientation ()."""
        self.orientation = [angle, angle, vector3]
#TODO:        self.orientation = [angle, 0, vector3]
        self.duration = duration
        self.changed = 'o'
        self.send_orientation()

    def send_focus(self):
        """Echo focus command to clients"""
#        for cl in self.get_clients():
#            cl.send_msg("focus %f %f %f" % self.focus )
        pass

    def send_orientation(self):
        """Echo command to clients"""
#        for cl in self.get_clients():
#            cl.send_msg("orientation "+str(self.orientation)+" "+str(self.duration))
        pass



if __name__ == '__main__':
    try:
        server = Gaze(conf.gaze_addr)
    except UserWarning, err:
        comm.LOG.error("FATAL ERROR: %s (%s)", sys.argv[0], err)
        exit(-1)
    while server.is_readable:
        comm.loop(5, count=1)
    print "Gaze done"