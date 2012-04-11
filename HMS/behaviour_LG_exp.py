#!/usr/bin/python
# -*- coding: utf-8 -*-

# behaviours to be used in conjunction with LG experiments

import logging
import random
import time

from RAS.au_pool import VAL
from HMS.behaviour_builder import BehaviourBuilder, fatal
from HMS.communication import MTLightheadComm
from utils.parallel_fsm import STARTED, STOPPED, SPFSM as FSM
from utils import vision, conf

LOG = logging.getLogger(__package__)


class LightHead_Behaviour(BehaviourBuilder):
    """
    """

    def st_start(self):
        self.last_st_change_t = time.time()
        self.comm_expr.set_fExpression('neutral', intensity=1)
        self.comm_expr.set_text("Starting...")
        self.comm_expr.set_gaze((0,10,0))
        #self.comm_expr.set_instinct("gaze-control:target=%s" % self.comm_expr.get_transform([0,0,0],'p'))
        self.comm_expr.sendDB_waitReply()
        return True


    def st_stopped(self):
        print 'test stopped'
        return True
  
  
    def __init__(self, with_gui=True):
        machines_def = [
          ('cog', (
            (STARTED, self.st_start, 'stop_state'),
            ('stop_state', self.st_stopped, STOPPED),), None), 
          ]
        super(LightHead_Behaviour,self).__init__(machines_def, FSM)
        
        self.comm_lightHead = MTLightheadComm(conf.lightHead_server)    
    
    
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

