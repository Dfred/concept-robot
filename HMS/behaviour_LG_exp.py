#!/usr/bin/python
# -*- coding: utf-8 -*-

# behaviours to be used in conjunction with LG experiments

import logging
import time, random, Queue

from RAS.au_pool import VAL
from HMS.behaviour_builder import BehaviourBuilder, fatal
from HMS.communication import MTLightheadComm
from utils.parallel_fsm import STARTED, STOPPED, MPFSM as FSM
from utils import vision, conf

LOG = logging.getLogger(__package__)

hw_robot = False    # hardware robot is present

class LightHead_Behaviour(BehaviourBuilder):
    """
    """

    def st_start(self):
        item = None
        while not item:
            try:    # query the queue
                item = self.from_gui_queue.get()
            except Queue.Empty:
                item = None

        if item[0] == "do_behaviour":
            self.do_behaviour(item[1], item[2])
        if item[0] == "end":
            self.comm_expr.set_fExpression("neutral", intensity=.8)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , 0.0))")
            self.comm_expr.set_gaze((0.0,1.0,0.0), duration=1.0)
            self.comm_expr.sendDB_waitReply()
            return True
        
    
    def do_behaviour(self, behaviour, gaze_target):
        if behaviour == "1": # starting
            pass
        if behaviour == "2A": # waiting for teacher to choose a topic
            self.comm_expr.set_gaze((0,10,0), duration=1.0)
            signs = [1.0, -1.0]
            sign_mod = signs[random.randint(0,1)]
                
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((%2f, 0.0 , -.5))" % (-.5*sign_mod))
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , -0.5))")
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((%2f, 0.0 , -0.5))"% (.5*sign_mod))
            self.comm_expr.sendDB_waitReply()
                
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , -.3))")
            self.comm_expr.sendDB_waitReply()
        if behaviour == "2B": # trying to indicate preferred topic to teacher
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=.5)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , -.3))")
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_fExpression("evil_grin", intensity=.8, duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=[[%2f, 0.0, -.6]]" % (.5 - (gaze_target*.5)))
            self.comm_expr.sendDB_waitReply()
            # look_at_teacher()
        if behaviour == "3": # don't know word
            self.comm_expr.set_gaze((0.2,1.0,0.2), duration=1.0)
            self.comm_expr.set_fExpression("surprised", intensity=1.0,)
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_gaze((0.0,1.0,0.0), duration=2.0)
            self.comm_expr.sendDB_waitReply()
        if behaviour == "4": # learns word
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=2.0)
            self.comm_expr.set_instinct("gaze-control:target=[[%2f, 0.0, -.6]]" % (.5 - (gaze_target*.5)))
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , -.3))")
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=2.0)
            self.comm_expr.sendDB_waitReply()
        if behaviour == "5": # guessing an animal
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=[[%2f, 0.0, -.6]]" % (.5 - (gaze_target*.5)))
            self.comm_expr.sendDB_waitReply()
        if behaviour == "6": # guessed right
            self.comm_expr.set_fExpression("smiling", 1.0, duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , -.3))")
            self.comm_expr.sendDB_waitReply()
        if behaviour == "7": # guessed wrong
            print "guessed wrong"
            self.comm_expr.set_fExpression("disgust1", 1.0, duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , -.3))")
            self.comm_expr.sendDB_waitReply()
        if behaviour == "8": # language game over
            print "LG over"
            self.comm_expr.set_fExpression("smiling", 1.0)
            self.comm_expr.sendDB_waitReply()



    def st_stopped(self):
        return True
    
    
    def st_detect_faces(self):
        self.update_vision()
        self.faces = self.vision.find_faces()
        if self.faces and self.vision.gui:
            self.vision.mark_rects(self.faces)
            self.vision.gui.show_frame(self.vision.frame)
        return len(self.faces)
    
    
    def update_vision(self):
        self.vision.update()
        self.vision.gui_show()
  
  
    def __init__(self, from_gui_queue, with_gui=True, with_vision=False):
        machines_def = [
          ('cog', (
            (STARTED, self.st_start, 'stop_state'),
            ('stop_state', self.st_stopped, STOPPED),), None), 
#          ('vis',   (
#            (STARTED, self.st_detect_faces,   None), ),  'cog'),
          ]
        super(LightHead_Behaviour,self).__init__(machines_def, FSM)
        
        if with_vision:
            try:
                self.vision = vision.CamUtils(conf.ROBOT['mod_vision']['sensor'])
                self.vision.update()
                LOG.info('--- %sDISPLAYING CAMERA ---', '' if with_gui else 'NOT ') 
                if with_gui:
                    self.vision.gui_create()
                    self.update_vision()
                self.vision.enable_face_detection()
            except vision.VisionException, e:
                fatal(e)
        
        self.comm_lightHead = MTLightheadComm(conf.lightHead_server)
        self.from_gui_queue = from_gui_queue
    
    
    def cleanUp(self):
        LOG.debug('--- cleaning up ---')
        self.comm_lightHead.done()
        super(LightHead_Behaviour,self).cleanUp()
    

if __name__ == '__main__':
    import sys, threading
    
    from utils import comm, LOGFORMATINFO
    LOGFORMATINFO['format'] = '%(threadName)s '+LOGFORMATINFO['format']
    logging.basicConfig(level=logging.DEBUG, **LOGFORMATINFO)
    conf.set_name('lightHead')
    missing = conf.load(required_entries=('lightHead_server',))
    if missing:
        print '\nMissing configuration entry: %s', missing
        sys.exit(2)
    
    print len(sys.argv) > 1 and sys.argv[1] == '-g'
    player = LightHead_Behaviour(len(sys.argv) > 1 and sys.argv[1] == '-g')
    player.run()
    player.cleanUp()
    #  import pdb; pdb.set_trace()
    print 'done', threading.enumerate()

