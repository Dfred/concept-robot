# -*- coding: utf-8 -*-

# This file is part of lightHead.
#
# lightHead is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# lightHead is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with lightHead.  If not, see <http://www.gnu.org/licenses/>.

import math
import time

import control
import vision
import conf
import comm
from control.interfaces.communication import ExpressionComm

__author__ = "Frédéric Delaunay"
__copyright__ = "Copyright 2011, University of Plymouth, lightHead system"
__credits__ = [""]
__license__ = "GPL"
__version__ = "0.0.1"
__maintainer__ = "Frédéric Delaunay"
__email__ = "frederic.delaunay@plymouth.ac.uk"
__status__ = "Prototype" # , "Development" or "Production"

def error(msg):
    print msg
    exit(1)


class IntelligentPlayer():
    """
    """

    def finish(self):
        """Called on 'STOPPED' state.
        """
        return None

    def read_section(self):
        """
        Returns: 'EOSECTION','FINISHING'
        """
        line = self.performance.readline()
        if not line:
            return 'FINISHING'
        self.comm_expr.send_msg(line)

    def listenTo_participant(self):
        """
        Returns: 'P_QUESTION', 'P_STATEMENT', 'P_TIMEOUT'
        """
        return 'P_QUESTION'
        return 'P_STATEMENT'
        return 'P_TIMEOUT'

    def answer_participant(self):
        """
        Returns: 'REPLIED'
        """
        return 'REPLIED'
    
    def nodTo_participant(self):
        """
        Returns: 'REPLIED'
        """
        return 'REPLIED'
    
    def interrupt_participant(self):
        """
        Returns: 'REPLIED'
        """
        return 'REPLIED'
    
    def search_participant(self):
        """
        Returns: 'FOUND_PART'
        """
        self.vision.update()
        faces = self.vision.find_faces()
        if self.vision.gui:
            self.vision.mark_faces(faces)
            self.vision.gui.show_frame(self.vision.frame)
        return faces and 'FOUND_PART' or None

    def adjust_head(self):
        """
        Returns: 'ADJUSTED'
        """
        return 'ADJUSTED'

    def __init__(self):
        """
        """
        PLAYER_DEF = ( (('FOUND_PART', 'REPLIED'), self.read_section),
                       ('EOSECTION',  self.listenTo_participant),
                       ('P_QUESTION', self.answer_participant),
                       ('P_STATEMENT', self.nodTo_participant),
                       ('P_TIMEOUT', self.interrupt_participant),
                       ('STOPPED', self.finish),
                   )
    
        FACETRACKER_DEF = ( (('STARTED', 'ADJUSTED'), self.search_participant),
                            ('FOUND_PART', self.adjust_head),
                            ('STOPPED', self.finish),
                        )
                      
        self.player = control.Behaviour(PLAYER_DEF)
        self.tracker = control.Behaviour(FACETRACKER_DEF, self.player)
        conf.load()
        self.vision = vision.CamFaceFinder(conf.haar_cascade_path)
        self.vision.gui_create()
        self.performance = file('./performance.txt', 'r', 1)
        self.comm_expr = ExpressionComm(conf.expression_server)

    def cleanup(self):
        """
        """
        print 'cleaning up'
        self.vision.gui_destroy()
        self.performance.close()
        self.comm_expr.done()

    def check_channels(self, machines):
        """
        Returns: finishes on disconnection.
        """
        if not self.comm_expr.connected:
            self.tracker.stop()
            self.player.stop()

    def run(self):
        """
        """
        try:
            while not self.comm_expr.connected:
                time.sleep(1)
            self.player.run(self.check_channels)
        except KeyboardInterrupt:
            print 'stopping'
            self.player.stop()



if __name__ == '__main__':
    # in this scenario, we are a process using at least the webcam (and audio).
    player = IntelligentPlayer()
    player.run()
    player.cleanup()
    print 'done'
