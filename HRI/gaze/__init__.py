#!/usr/bin/python

#
# This module handle the gazing of the face as well as eyes' iris diameter.
# Coordinates are one 3float vector, Orientations are three 3float vector.

import sys

import asyncore
import logging

logging.basicConfig(level=logging.WARNING)
LOG = logging.getLogger("gaze-srv")

import comm
import conf


class GazeClient(comm.RemoteClient):
    """Remote connection handler"""

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
                self.server.set_orientation(
                    tuple([args[0:3],args[3:6],args[6:9]]) )
            except Exception, e:
                LOG.warning("[orientation] bad argument line:'%s', caused: %s" %
                            (argline,e) )
        else:
            self.send_msg("orientation",str(self.server.angles))

    def cmd_shutdown(self, args):
        """args: unused."""
        self.server.shutdown()



class Gaze(comm.BasicServer):
    """Main vision module - server"""
    """
    Designed to receive on-demand queries from external systems.
    This class holds all information, so you can also import this module.
    Origin is between the eyes.
    Metric System is used.
    """

    def __init__(self, addr_port):
        comm.BasicServer.__init__(self, GazeClient)
        self.listen_to(addr_port)
        self.focus = (.0, -1.0, .0)
        self.orientation = ([0,0,0], [0,-1,0], [0,0,0])
        self.changed = False            # update flag ('f', 'o')

    def set_focus(self, pos):
        """Set focus (1 vector3)."""
        self.focus = pos
        self.changed = 'f'
        self.send_focus()
        
    def set_orientation(self, matrix):
        """Just set eyes orientation (3 vector3)."""
        self.orientation = matrix
        self.changed = 'o'
        self.send_orientation()

    def send_focus(self):
        """Echo focus command to clients"""
        for cl in self.get_clients():
            cl.send_msg("focus %f %f %f" % self.focus )

    def send_orientation(self):
        """Echo command to clients"""
        for cl in self.get_clients():
            cl.send_msg("orient "+ str(self.orientation) )
        


if __name__ == '__main__':
    try:
        server = Gaze(conf.gaze_addr)
    except UserWarning, err:
        comm.LOG.error("FATAL ERROR: %s (%s)", sys.argv[0], err)
        exit(-1)
    while server.is_readable:
        comm.loop(5, count=1)
    print "Gaze done"
