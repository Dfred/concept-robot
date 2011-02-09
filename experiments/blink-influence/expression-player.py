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
import random

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
        print 'finishiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiing', self.name
        return None

    def read_section(self):
        """
        Returns: 'EOSECTION','STOPPED'
        """
        line = self.performance.readline()
        if line.startswith('EOSECTION'):
            return 'EOSECTION'
        if not line:
            return 'STOPPED'
        self.comm_expr.send_msg(line)
        self.wait_comm_expr_reply()

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
        line = random.Random().choice(self.replies['rep'])
        self.comm_expr.send_msg(line)
        self.wait_comm_expr_reply()
        return 'REPLIED'
    
    def nodTo_participant(self):
        """
        Returns: 'REPLIED'
        """
        line = random.Random().choice(self.replies['nod'])
        self.comm_expr.send_msg(line)
        self.wait_comm_expr_reply()
        return 'REPLIED'
    
    def interrupt_participant(self):
        """
        Returns: 'REPLIED'
        """
        line = random.Random().choice(self.replies['int'])
        self.comm_expr.send_msg(line)
        self.wait_comm_expr_reply()
        return 'REPLIED'
    
    def search_participant(self):
        """
        Returns: 'FOUND_PART'
        """
        self.vision.update()
        self.faces = self.vision.find_faces()
        if self.vision.gui:
            self.vision.mark_areas(self.faces)
            self.vision.gui.show_frame(self.vision.frame)
        return self.faces and 'FOUND_PART' or None

    def adjust_head(self):
        """
        Returns: 'ADJUSTED'
        """
        area = self.faces[0]
        relative_x = (self.vision_area[0] - (area.x + (area.w/2.0)) )
        relative_y = (self.vision_area[1] - (area.y + (area.h/2.0)) )
        gaze = (0,0,0)#self.follow_face_with_gaze(relative_x, relative_y)
        neck = (gaze,(0,0,0))#self.follow_face_with_neck(relative_x, relative_y, gaze[1])
        # reuse numbers from Joachim's magic hat ;P
        face_distance = ((-88.4832 * math.log(self.vision_area[0])) + 538.3782)
        self.comm_expr.send_neck_gaze(gaze, neck)
#        self.wait_comm_expr_reply()
        return 'ADJUSTED'

    def wait_comm_expr_reply(self):
        """Wait for a reply from the server.
        """
        while self.comm_expr.status is None:
            time.sleep(0.05)

    def read_replies(self):
        """
        """
        with file('./performance_replies.txt', 'r', 1) as f:
            for i,l in enumerate(f.readlines()):
                try:
                    group, line = l.split('  ')
                    self.replies[group].append(line)
                except Exception, e:
                    print 'error with replies file line %i: %s (%s)' % (i,l,e)
                    exit(1)

    def __init__(self, dev_index):
        """
        dev_index: camera device index
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
                      
        self.player = control.Behaviour('player', PLAYER_DEF)
        self.tracker = control.Behaviour('tracker',FACETRACKER_DEF, self.player)
        conf.load()
        try:
            self.vision = vision.CamFaceFinder(conf.haar_cascade_path,dev_index)
            self.vision_area = self.vision.get_resolution()
            self.vision.gui_create()
        except vision.VisionException, e:
            print e
            exit(1)
        self.performance = file('./performance.txt', 'r', 1)
        self.replies = {'rep' : [], 'int': [], 'nod' : []}
        self.read_replies()
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
    import sys
    try:
        dev_index = len(sys.argv) > 1 and int(sys.argv[-1]) or 0
    except ValueError:
        print 'argument shall be the camera device index (as an integer).'
        exit(1)
    # in this scenario, we are a process using at least the webcam (and audio).
    player = IntelligentPlayer(dev_index)
    player.run()
    player.cleanup()
    print 'done'
