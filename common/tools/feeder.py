#!/usr/bin/python

import sys
import asyncore

import comm
from fgui_gtk import FeederGui

class EmoClient(comm.BasicHandler):
    """Protocol Handler"""

    def handle_connect(self):
        comm.BasicHandler.handle_connect(self)
        self.server.send_values(self)

    def cmd_get_vector(self, args):
        self.send_msg(self.server.sinks.__repr__())


class ESink(comm.BasicServer):
    """Emotional module - server"""

    def __init__(self, addr_port):
        self.sinks = {"Openness": .5,
                      "Conscientiousness": .5 ,
                      "Extraversion": .5,
                      "Agreeableness": .5,
                      "Neuroticism": .5}
        self.au_map = {"O" : { "": 0},
                       "C" : { "": 0},
                       "E" : { "": 0},
                       "A" : { "": 0},
                       "N" : { "": 0}
                      }
                       
                      
        self.interface = FeederGui(self)
        comm.BasicServer.__init__(self, EmoClient)
        try:
            self.listen_to(addr_port)
        except UserWarning, err:        # ok ok it's slightly dirty
            print err
            exit(-1)            # because we consider serving is important

    def cleanup(self):
        self.interface.quit()

    def run(self):
        self.interface.run()

    def update(self, key, value):
        self.sinks[key] = value
        self.send_values()

    def send_values(self, target=None):
        data = ""
        for au, value in self.au_map:
            data += " "+au+":"+value.__str__()[:4]

        if target: target.send_msg("emo"+data); return

        for client in asyncore.socket_map.values():
            client is not self and client.send_msg("emo"+data)

    def ocean_to_au(self):
        """Manage mapping from emotional space to AU space"""
        for s in self.sinks.iteritems():
		pass

if __name__ == "__main__":
#     s = ESink()
#     s.run()
#     s.cleanup()
    cmdline, clients, server = comm.create(sys.argv, {}, ESink)
    
    if cmdline == sys.argv:
        print "comm server argument expected.."
        exit(-1)
    if not server:
        exit(-1)

    while not server.interface.quit and server.is_readable:
        asyncore.loop(0.01, count=1)   # wait 10ms or new data before returning
        server.interface.iterate()

    server.shutdown()
