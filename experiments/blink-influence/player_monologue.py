import time
import math
import random

from os.path import dirname, join

from utils.expression_player import FSM_Builder
from control import Behaviour

UTTERANCES = join(dirname(__file__),'./monologue.txt')

class Utterances(object):
    def __init__(self):
        self.file = file(UTTERANCES, 'r', 1)
        self.next_time = None
        self.buff = None

    def __del__(self):
        if hasattr(self, 'file'):
            self.file.close()

    def next(self):
        """Switch to next line. Also, check self.lock() for deferred reading.
        """
        if not self.next_time:
            self.next_time = time.time()
        if time.time() >= self.next_time:
            line = self.file.readline()
            if not line:
                return 'EOF'
            line = line.strip()
            if not line:
                return
            while line.startswith('#'):
                line = self.file.readline().strip()
            print "time", time.time()
            try:
                min_dur, datablock = line.split(None,1)
            except ValueError:
                print 'UTTERRANCES ERROR - line: %s' % line
                return None
            return (float(min_dur), datablock[:datablock.rindex(';')+1],
                    datablock[datablock.rindex(';')+1:])
        return None

    def lock_for(self, duration):
        """Lock iterating over the file for duration seconds.
        """
        self.next_time = time.time() + duration
        print "next_time", self.next_time


class MonologuePlayer(FSM_Builder):
    """A simple player reading monologue file.
    """

    def read(self):
        """
        Returns: Behaviour.STOPPED
        """
        if self.wait_reply:
            return
        line = self.utterances.next()
        if line == 'EOF':
            return Behaviour.STOPPED
        if line:
            def got_reply(status, tag):
                self.wait_reply = False
                self.comm_expr.on_reply_fct(self.tag, None)
                self.utterances.lock_for(pause)
            pause, datablock, self.tag = line
            self.wait_reply = True
            self.comm_expr.on_reply_fct(self.tag, got_reply)
            self.comm_expr.send_my_datablock(datablock, self.tag)

    def search_participant(self):
        """
        Returns: 'FOUND_PART'
        """
        self.faces = self.vision.find_faces()
        if self.vision.gui:
            self.vision.mark_rects(self.faces)
            self.vision.gui.show_frame(self.vision.frame)
        return self.faces and 'FOUND_PART' or None

    def adjust_gaze_neck(self):
        """
        Returns: 'ADJUSTED'
        """
        eyes = self.vision.find_eyes([self.faces[0]])[0]
        center = Frame(((eyes[0].x + eyes[1].x)/2, (eyes[0].y+eyes[1].y)/2,
                        self.faces[0].w, self.faces[0].h))
        gaze_xyz = self.vision.camera.get_3Dfocus(center)
        # TODO: ideally, we would not have to set the neck if gaze is enough to
        #  drive the neck (an expr2 instinct could do it).
        if not self.vision_frame.is_within(center.x, center.y):
            neck = (gaze_xyz,(.0,.0,.0))
        self.comm_expr.set_gaze(gaze_xyz)
        self.comm_expr.set_neck(*neck)
        tag = self.comm_expr.send_datablock('gaze_neck')
        self.comm_expr.wait_reply(tag)
        return 'ADJUSTED'

    def finish(self, name):
        """Called on FSM.STOPPED state.
        name: name of the machine.
        """
        del self.utterances
        return None

    def __init__(self):
        """
        """
        PLAYER_DEF= ( (Behaviour.STARTED, self.read),
                      (Behaviour.STOPPED, self.finish),
                    )
        FSM_Builder.__init__(self, [('player',PLAYER_DEF,None)])
        self.utterances = Utterances()
        self.wait_reply = False

if __name__ == '__main__':
    m = MonologuePlayer()
    m.run()
    m.cleanup()
    print 'done'
