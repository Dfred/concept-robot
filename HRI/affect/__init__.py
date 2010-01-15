#!/usr/bin/python

#
# This module handles the affective behaviour of the robot.
# The Affect class holds 2 layers of influence: personality and mood.
# In contrast, Emotion is a realtime-updated vector.
#
# MODULES IO:
#===========
# INPUT: - hear (classification id) [event]
#        - vision (classification id) [event]
#
# OUTPUT:* face (facial expressions + iris diameter + saccades) [push mode]
#        * dynamics
#

import sys
import logging

logging.basicConfig(level=logging.WARNING)
LOG = logging.getLogger("gaze-srv")

import comm
import conf

AFFECT_DIMS=["joy", "sad", "dis", "sur", "fea", "ang"]

class AffectClient(comm.BasicHandler):
    """Remote connection handler: protocol parser"""

    def cmd_affect(self, argline):
        """Sets or gets current values.
        no arg: display values.
        2 args: set arg[0] with value from arg[1]
        6 args: set values in order defined by AFFECT_DIMS
        """
        args = argline.split()
        if len(args) == 2:
            if args[0] not in AFFECT_DIMS:
                self.send_msg("unmatched affective dimension name")
                return
            try:
                self.server.set_value(args[0], float(args[1]))
            except ValueError:
                self.send_msg("float value error:"+args[1])
        elif len(args) == len(AFFECT_DIMS):
            self.server.set_value(None, [float(val) for val in args])
        else:
            self.send_msg(self.server.sinks.__repr__())


    def cmd_shutdown(self, args):
        self.server.shutdown()



class Affect(comm.BasicServer):
    """Affective module - server.
    This class maps affective vector to AU values. Blending these values is the
    job of the face module. These AU values are pushed/sent on an update basis.
    """

    def __init__(self, addr_port):
        self.mood = []
        self.pers = []
        self.sinks = {AFFECT_DIMS[0]: .5, #joy
                      AFFECT_DIMS[1]: .5, #sadness
                      AFFECT_DIMS[2]: .5, #disgust
                      AFFECT_DIMS[3]: .5, #surprise
                      AFFECT_DIMS[4]: .5, #fear
                      AFFECT_DIMS[5]: .5} #anger

        self.AU_map= {AFFECT_DIMS[0]: { 7:.8, 10:.8, 12:.8, 25:.8},
                      AFFECT_DIMS[1]: {17:.8, 16:.8, 15:.8,  1:.8,
                                        2:.8,  4:.8},
                      AFFECT_DIMS[2]: {17:.8, 16:.8, 15:.8, 10:.8,  9:.8},
                      AFFECT_DIMS[3]: {27:.2, #jaw relax
                                        1:.2},
                      AFFECT_DIMS[4]: { 1:.2, 10:.6, 25:.7},
                      AFFECT_DIMS[5]: { 4:.6,  9:.9, 10:.8, 17:.7}
                      }
                       
        comm.BasicServer.__init__(self, AffectClient)
        self.listen_to(addr_port)
        print "Affect started"

    def update(self, time_step):
        """Send updates to face if values not stabilized."""
        #TODO: compute target AU values according to affect vector.
        #     blend affect values with mood + personality (rise, peak, recovery)
        #     update mood and personality over time
        pass

    def set_value(self, key, value):
        if key in AFFECT_DIMS:
            self.sinks[key] = value
        else:
            for i in xrange(len(AFFECT_DIMS)):
                self.sinks[AFFECT_DIMS[i]] = value[i]
        self.send_values()

    def send_values(self, target=None):
        """Send values to face module"""
        data = ""
        for au, value in self.au_map:
            data += " "+au+":"+value.__str__()[:4]

        if target:
            target.send_msg("affect"+data)
            return

        for client in asyncore.socket_map.values():
            client is not self and client.send_msg("emo"+data)

    def affect_to_au(self):
        """Manage mapping from affective space to AU space"""
        for s in self.sinks.iteritems():
            pass



if __name__ == "__main__":
    missing = conf.load()
    if missing:
        print "WARNING: missing configuration entries:",missing
    try:
        server = Affect(conf.conn_affect)
    except UserWarning, err:
        comm.LOG.error("FATAL ERROR: %s (%s)", sys.argv[0], err)
        exit(-1)
    while server.is_readable:
        comm.loop(0.01, count=1)   # wait 10ms or new data before returning
    print "Affect done"
