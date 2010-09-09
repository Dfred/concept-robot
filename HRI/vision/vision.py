#!/usr/bin/python

import sys

import asyncore
import logging

logging.basicConfig(level=logging.WARNING)

import comm

#TODO: use global configuration
VIS_ADDR = ("localhost", 4245)

class VisionClient(comm.RequestHandler):
    """Remote connection handler"""

    def cmd_focus(self, args):
        """args: if empty, returns current focus coords. Otherwise, set them."""
        if len(args):
            args = [float(arg) for arg in args.split()]
            self.server.choose_focus(args)
        else:
            self.send_msg(str(self.server.pos))


class Vision(comm.BaseServ):
    """Main vision module - server"""
    """
    Designed to receive on-demand queries from external systems.
    Origin is between the eyes.
    Metric System is used.
    """

    def __init__(self):
        comm.BaseServ.__init__(self)
        self.pos = (.0, -1.0, .0)       # default to reasonably close

    def choose_focus(self, pos):
        """Decide where to look at considering all inputs"""
        self.pos = pos
        #TODO: have a real heuristic
        self.send_values()
    
    def send_values(self):
        for cl in self.get_clients():
            cl.send_msg("focus %f,%f,%f"% (self.pos[0], self.pos[1], self.pos[2]))

if __name__ == '__main__':
    server = comm.createServer(Vision, VisionClient, VIS_ADDR)
    print 'server running'
    server.serve_forever()
    print "Vision done"
