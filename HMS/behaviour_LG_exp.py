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
        self.comm_expr.set_fExpression('neutral', intensity=1)
        self.comm_expr.set_text("Starting...")
        if item[0] == "gaze_adjust":
            self.comm_expr.set_gaze(item[1])
            self.comm_expr.sendDB_waitReply()
        if item[0] == "end":
            return True


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

