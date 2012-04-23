#!/usr/bin/python
# -*- coding: utf-8 -*-

# behaviours to be used in conjunction with LG experiments

import logging
import time, Queue, math
import random as ran

from RAS.au_pool import VAL
from HMS.behaviour_builder import BehaviourBuilder, fatal
from HMS.communication import MTLightheadComm
from utils.parallel_fsm import STARTED, STOPPED, MPFSM as FSM
from utils import conf, vision

LOG = logging.getLogger(__package__)

#parameters for touchscreen
param_gaze_x = 0.15
param_gaze_y = 0.25


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
            self.cycle = item[4]
            self.do_behaviour(item[1], item[2], item[3])
            
        if item[0] == "end":
            print "ending"
            self.comm_expr.set_fExpression("neutral", intensity=.8)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , 0.0))")
            self.comm_expr.set_gaze((0.0,1.0,0.0), duration=1.0)
            self.comm_expr.sendDB_waitReply()
            return True
        
    
    def do_behaviour(self, behaviour, gaze_target, teacher_word):
        if behaviour == "1": # starting
            pass
        if behaviour == "2A": # waiting for teacher to choose a topic
            self.comm_expr.set_gaze((0,10,0), duration=1.0)
            self.comm_expr.sendDB_waitReply()
            signs = [1.0, -1.0]
            sign_mod = signs[ran.randint(0,1)]
                
            self.comm_expr.set_gaze((param_gaze_x*sign_mod,1.0,-param_gaze_y), duration=2.0)
            self.comm_expr.set_spine('shoulderr', (0.0, .0, .0), 'o', duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((%2f, 0.0 , -.6))" % (-.6*sign_mod))
            self.comm_expr.sendDB_waitReply()
            
            self.comm_expr.set_gaze((0.0,1.0,-param_gaze_y), duration=1.0)
            self.comm_expr.set_spine('shoulderr',(0.0, .0, .0), 'o', duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , -0.6))")
            self.comm_expr.sendDB_waitReply()
            
            self.comm_expr.set_gaze((-param_gaze_x*sign_mod,1.0,-param_gaze_y), duration=1.0)
            self.comm_expr.set_spine('shoulderr',(0.0, .0, .0), 'o', duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((%2f, 0.0 , -0.6))"% (.6*sign_mod))
            self.comm_expr.sendDB_waitReply()
                
            self.comm_expr.set_text(self.get_next_round_statement())    # get speech
            self.comm_expr.set_gaze((0.0,1.0,0.0), duration=1.0)
            self.comm_expr.set_spine('shoulderr',(0.0, .0, .0), 'o', duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , 0.0))")
            self.comm_expr.sendDB_waitReply()
            self.follow_face = True
        if behaviour == "2B": # trying to indicate preferred topic to teacher
            self.comm_expr.set_gaze((0,10,0), duration=1.0)
            self.comm_expr.sendDB_waitReply()
            signs = [1.0, -1.0]
            sign_mod = signs[ran.randint(0,1)]
                
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=1.0)
            self.comm_expr.set_gaze((param_gaze_x*sign_mod,1.0,-param_gaze_y), duration=1.0)
            self.comm_expr.set_spine('shoulderr',(0.0, .0, .0), 'o', duration=2.0)
            self.comm_expr.set_instinct("gaze-control:target=((%2f, 0.0 , -.6))" % (-.6*sign_mod))
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_gaze((0.0,1.0,-param_gaze_y), duration=1.0)
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=1.0)
            self.comm_expr.set_spine('shoulderr',(0.0, .0, .0), 'o', duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , -0.6))")
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_gaze((-param_gaze_x*sign_mod,1.0,-param_gaze_y), duration=1.0)
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=1.0)
            self.comm_expr.set_spine('shoulderr',(0.0, .0, .0), 'o', duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((%2f, 0.0 , -0.6))"% (.6*sign_mod))
            self.comm_expr.sendDB_waitReply()
            
            self.comm_expr.set_text(self.get_next_round_active_statement())    # get speech
            self.comm_expr.set_fExpression("evil_grin", intensity=.8, duration=1.0)
            self.comm_expr.set_gaze(  ( -param_gaze_x + (gaze_target*param_gaze_x), 1.0, -param_gaze_y), duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=[[%2f, 0.0, -.6]]" % (.5 - (gaze_target*.6)))
            self.comm_expr.sendDB_waitReply()
        if behaviour == "3": # don't know word
            self.follow_face = False
            self.comm_expr.set_text(self.get_dont_know_statement(teacher_word))    # get speech
            self.comm_expr.set_gaze((0.2,1.0,0.2), duration=1.0)
            self.comm_expr.set_fExpression("surprised", intensity=1.0,)
            self.comm_expr.sendDB_waitReply()   # get speech
            self.comm_expr.set_gaze((0.0,1.0,0.0), duration=1.0)
            self.comm_expr.sendDB_waitReply()
        if behaviour == "4": # learns word
            self.comm_expr.set_text(self.get_learning_statement(teacher_word))    # get speech
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=2.0)
            self.comm_expr.set_gaze(  ( -param_gaze_x + (gaze_target*param_gaze_x), 1.0, -param_gaze_y), duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=[[%2f, 0.0, -.6]]" % (.5 - (gaze_target*.5)))
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , -.3))")
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=2.0)
            self.comm_expr.sendDB_waitReply()
        if behaviour == "5": # guessing an animal
            self.follow_face = False
            self.comm_expr.set_text(self.get_guessing_statement(teacher_word))    # get speech
            self.comm_expr.set_gaze(  ( -param_gaze_x + (gaze_target*param_gaze_x), 1.0, -param_gaze_y), duration=1.0)
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=[[%2f, 0.0, -.6]]" % (.5 - (gaze_target*.5)))
            self.comm_expr.sendDB_waitReply()
        if behaviour == "6": # guessed right
            self.comm_expr.set_text(self.get_correct_statement())    # get speech
            self.comm_expr.set_gaze((0.0,1.0,0.0), duration=1.0)
            self.comm_expr.set_fExpression("smiling", 1.0, duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , -.3))")
            self.comm_expr.sendDB_waitReply()
        if behaviour == "7": # guessed wrong
            self.comm_expr.set_text(self.get_wrong_statement())
            self.comm_expr.set_gaze((0.0,1.0,0.0), duration=1.0)
            self.comm_expr.set_fExpression("disgust1", 1.0, duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , -.3))")
            self.comm_expr.sendDB_waitReply()
        if behaviour == "8": # language game over
            print "LG over"
            self.comm_expr.set_fExpression("smiling", 1.0)
            self.comm_expr.sendDB_waitReply()


    def get_next_round_statement(self):
        if self.cycle < 6:
            stats = ("mentally choose an animal, and tell me its category",
                     "think of an animal, and tell me its category",
                     "picture an animal in your mind, and let me know which category it belongs to!",
                     "mentally choose an animal, and click on the category it belongs to!",
                     "choose an animal that you want to teach me, and click its category")
            statement = stats[ran.randint(0, len(stats)-1)]
        else:
            stats = ("Lets do another round",
                     "Right, lets go again",
                     "here are some more animals",
                     "what about these?",
                     "lets do some more!",
                     "another guessing round",
                     "tell me a category, and I will guess",
                     "tell me the animal category",
                     "lets guess one more time")
            statement = stats[ran.randint(0, len(stats)-1)]
        return statement
    
    
    def get_next_round_active_statement(self):
        if self.cycle < 6:
            stats = ("I would like to learn another animal, tell me its category",
                     "think of an animal, and tell me its category",
                     "picture an animal in your mind, and let me know which category it belongs to!",
                     "mentally choose an animal, and click on the category it belongs to!",
                     "choose an animal that you want to teach me, and click its category")
            statement = stats[ran.randint(0, len(stats)-1)]
        else:
            stats = ("Lets do another round",
                     "Right, lets go again",
                     "lets do some more!",
                     "another guessing round",
                     "tell me a category, and I will guess",
                     "tell me the animal category",
                     "I want to learn more",
                     "I think this is interesting",
                     "Just wondering about this",
                     "lets guess one more time")
            statement = stats[ran.randint(0, len(stats)-1)]
        return statement
        
    
    def get_dont_know_statement(self, teacher_word):
        stats = ("uum, I don't know what a " + teacher_word + " is, please click on the animal",
                 "I don't have a clue what a " + teacher_word + "might be, please click on correct the animal",
                 "Never heard off " + teacher_word + " before, let me know what animal this is",
                 "don't know " +teacher_word + ", please tell me what it is",
                 teacher_word + "?, I don't really know, just click on the correct animal so I can learn",
                 teacher_word + "? I don't know that one. please click on the animal",
                 "a " +teacher_word+ "? No clue. Please click on the correct animal") 
        return stats[ran.randint(0, len(stats)-1)]
    
    
    def get_learning_statement(self, teacher_word):
        stats = ("ah, so this is a " + teacher_word,
                 "so this is what a " + teacher_word + " looks like",
                 "right, good to know",
                 "allright, now I know what a " + teacher_word + " looks like",
                 "ok, so a " + teacher_word + " looks like this")
        return stats[ran.randint(0, len(stats)-1)]
    
    
    def get_guessing_statement(self, teacher_word):
        stats = ("I'm guessing this is a " + teacher_word + "?, please click on the animal that you had in mind",
                 "is this a " + teacher_word + "? Please tell me which animal you had in mind",
                 "I think this is a " + teacher_word + "?, please tell me if I am correct",
                 "Am I correct in thinking this is a " + teacher_word + "?, please click on the correct animal",
                 "uum, I think this is a " + teacher_word + ", is this correct?",
                 "a " + teacher_word + "?, that must be this one!",
                 teacher_word + "?, umm, I think this is a " + teacher_word+ ", is this correct?",
                 "yes, I think this is a " + teacher_word+ ", did I guess right?",
                 "I know what a " +teacher_word+ " is, it is this one!, is that correct?" )
        return stats[ran.randint(0, len(stats)-1)]
    
    
    def get_correct_statement(self):
        stats = ("yes!, just as I thought!",
                 "Aha, just what I thought!",
                 "yes!, I knew that one",
                 "indeed, my guess was correct",
                 "naturally, I'm pretty clever",
                 "right, my hypothesis is confirmed",
                 "ofcourse it is",
                 "yes, another one correct",
                 "I like it when I am right",
                 "yeehaa, lets do another one!")
        return stats[ran.randint(0, len(stats)-1)]
    
    
    def get_wrong_statement(self):
        stats = ("ow!, I guessed wrong",
                 "mmm, too bad",
                 "noho, not wrong again", 
                 "too bad, I thought I knew that one",
                 "sadly, I am mistaken",
                 "really? I thought otherwise, oh well",
                 "if you say so, I guess I was wrong",
                 "mm, guessed that one wrong",
                 "that's not correct?, oh well",
                 "are you sure, well, if you say so")
        return stats[ran.randint(0, len(stats)-1)]


    def st_stopped(self):
        return True
    
    
    def st_detect_faces(self):
        if self.vision:
            self.update_vision()
            self.faces = self.vision.find_faces()
            if self.faces and self.vision.gui:
                self.vision.mark_rects(self.faces)
                self.vision.gui.show_frame(self.vision.frame)
            if self.faces:
                if self.follow_face:
                    #target = self.vision.get_face_3Dfocus(self.faces)[0]
                    #print self.faces, target
                    #self.comm_expr.set_spine('shoulderr',(0.0, .0, .0), 'o', duration=.5)
                    self.comm_expr.set_instinct("gaze-control:target=%s" %self.calc_face_target())
                    #self.comm_expr.set_instinct("gaze-control:target=%s" % self.comm_expr.get_transform(target,'r'))
                    self.comm_expr.sendDB_waitReply(tag='KUV')
                    print "looking for face"
        return len(self.faces)


    def calc_face_target(self):
        rect = self.faces[0]
        fx, fy, fw, fh = rect.x, rect.y, rect.w, rect.h
        face_dist = ((-88.5 * math.log(fw)) + 538.5)
        fx = fx + (fw/2.0)
        fy = fy + (fh/2.0)
        x_dist = 0.5 * (((fx/320.0) *-2) +1)
        y_dist = 0.5 * (((fy/240.0) *-2) +1)
        return "(%2f, %2f, %2f)" %(-x_dist, (face_dist/100.0), y_dist)
    
    
    def update_vision(self):
        self.vision.update()
        self.vision.gui_show()
  
  
    def __init__(self, from_gui_queue, with_gui=True, with_vision=True):
        self.faces = []
        self.follow_face = False
        self.vision = None
        self.cycle = None
        machines_def = [
          ('cog', (
            (STARTED, self.st_start, 'stop_state'),
            ('stop_state', self.st_stopped, STOPPED),), None), 
          ('vis',   (
            (STARTED, self.st_detect_faces,   None), ),  'cog'),
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
        try:
            self.vision.gui_destroy()
        except AttributeError:
            pass # we have no gui
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

