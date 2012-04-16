#!/usr/bin/python
# -*- coding: utf-8 -*-

# behaviours to be used in conjunction with LG experiments

import logging
import time, random, Queue

from RAS.au_pool import VAL
from HMS.behaviour_builder import BehaviourBuilder, fatal
from HMS.communication import MTLightheadComm
from utils.parallel_fsm import STARTED, STOPPED, SPFSM as FSM
from utils import conf

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
        
        self.last_st_change_t = time.time()

        if item[0] == "do_behaviour":
            self.do_behaviour(item[1], item[2])
        if item[0] == "end":
            self.comm_expr.set_fExpression("neutral", intensity=.8)
            self.comm_expr.sendDB_waitReply()
            return True
        
    
    def do_behaviour(self, behaviour, gaze_target):
        if behaviour == "1": # starting
            pass
        if behaviour == "2A": # waiting for teacher to choose a topic
            if hw_robot:
                self.comm_expr.set_neck((-0.1, 0.0, 0.1))
                self.comm_expr.sendDB_waitReply()
                self.comm_expr.set_neck((-0.1, 0.0, 0.0))
                self.comm_expr.sendDB_waitReply()
                self.comm_expr.set_neck((-0.1, 0.0, -0.1))
                self.comm_expr.sendDB_waitReply()
                # look_at_teacher()
            self.comm_expr.set_fExpression("neutral", intensity=.8)
            self.comm_expr.set_gaze((3,10,0), duration=.5)
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_gaze((0,10,0), duration=.5)
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_gaze((-3,10,0), duration=.5)
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_gaze((0,10,0), duration=.5)
            self.comm_expr.sendDB_waitReply()
        if behaviour == "2B": # trying to indicate preferred topic to teacher
            if hw_robot:
                self.comm_expr.set_neck((-0.1, 0.0, 0.1))
                # look_at_teacher()
        if behaviour == "3": # don't know word
            if hw_robot:
                self.comm_expr.set_neck((0.0, 0.0, 0.0))
                self.comm_expr.set_neck((0.0, -0.1, 0.0))
            self.comm_expr.set_gaze((3,10,3))
            self.comm_expr.set_fExpression("really_look", intensity=.5, duration=1.5)
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_gaze((0,10,0))
            self.comm_expr.sendDB_waitReply()
        if behaviour == "4": # learns word
            if hw_robot:
                self.comm_expr.set_neck((-0.1, 0.0, 0.1)) # look at topic
                self.comm_expr.set_neck((0.0, 0.0, 0.0))
                self.comm_expr.set_neck((-0.1, 0.0, 0.0))
                self.comm_expr.set_neck((0.0, 0.0, 0.0))
            self.comm_expr.set_gaze((-3 + (gaze_target*3),10,0), duration=.5)
            self.comm_expr.sendDB_waitReply()
        if behaviour == "5": # guessing an animal
            if hw_robot:
                self.comm_expr.set_neck((-0.1, 0.0, 0.1)) # look at topic
                # look_at_teacher()
            self.comm_expr.set_gaze((-3 + (gaze_target*3),10,0))
            self.comm_expr.sendDB_waitReply()
        if behaviour == "6": # guessed right
            if hw_robot:
                self.comm_expr.set_neck((0.0, 0.0, 0.0))
                self.comm_expr.set_neck((0.1, 0.0, 0.0))
                self.comm_expr.set_neck((0.0, 0.0, 0.0))
            self.comm_expr.set_fExpression("simple_smile_wide2", 1.0, duration=2.0)
            self.comm_expr.sendDB_waitReply()
        if behaviour == "7": # guessed wrong
            if hw_robot:
                self.comm_expr.set_neck((0.0, 0.0, 0.0))
                self.comm_expr.set_gaze((0,10,-3))
            self.comm_expr.set_fExpression("disgust1", 1.0, duration=2.0)
            self.comm_expr.sendDB_waitReply()
        if behaviour == "8": # guessing game over
            if hw_robot:
                self.comm_expr.set_neck((0.0, 0.0, 0.0))
            self.comm_expr.set_gaze((0,10,0))
            self.comm_expr.set_fExpression("simple_smile_wide1", 1.0)
            self.comm_expr.sendDB_waitReply()



    def st_stopped(self):
        return True
  
  
    def __init__(self, from_gui_queue, with_gui=True):
        machines_def = [
          ('cog', (
            (STARTED, self.st_start, 'stop_state'),
            ('stop_state', self.st_stopped, STOPPED),), None), 
          ]
        super(LightHead_Behaviour,self).__init__(machines_def, FSM)
        
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

