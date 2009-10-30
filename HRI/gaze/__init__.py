#!/usr/bin/python

#
# This module handle the gazing of the face as well as eyes' iris diameter.
#

import sys

import asyncore
import logging

logging.basicConfig(level=logging.WARNING)

import comm
import conf


class GazeClient(comm.RemoteClient):
    """Remote connection handler"""

    def cmd_focus(self, args):
        """args: if empty, returns current focus coords. Otherwise, set them."""
        if len(args):
            args = [float(arg) for arg in args.split()]
            self.server.choose_focus(args)
        else:
            self.send_msg(str(self.server.pos))

    def cmd_shutdown(self, args):
        """args: unused."""
        self.server.shutdown()



class Gaze(comm.BasicServer):
    """Main vision module - server"""
    """
    Designed to receive on-demand queries from external systems.
    Origin is between the eyes.
    Metric System is used.
    """

    def __init__(self, addr_port):
        comm.BasicServer.__init__(self, GazeClient)
        try:
            self.listen_to(addr_port)
        except UserWarning, err:
            comm.LOG.error("FATAL ERROR: %s (%s)", sys.argv[0], err)
            exit(-1)
        self.pos = (.0, -1.0, .0)       # default to reasonably close

    def set_focus(self, pos):
        """Decide where to look at considering all inputs"""
        self.pos = pos
        self.send_values()
    
    def send_values(self):
        for cl in self.get_clients():
            cl.send_msg("focus %f,%f,%f"% (self.pos[0], self.pos[1], self.pos[2]))

if __name__ == '__main__':
    server = Gaze(conf.gaze_addr)
    while server.is_readable:
        comm.loop(5, count=1)
    print "Gaze done"
