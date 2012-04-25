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


PARAM_GAZE_X = 0.14     #parameters for touchscreen
PARAM_GAZE_Y = 0.28

MIN_TIME_MOVES = 10     # minimum time between moves



class LightHead_Behaviour(BehaviourBuilder):
    """
    """
    
    def __init__(self, from_gq, to_gq, with_gui=True, with_vision=True):
        self.faces = []
        self.follow_face = False
        self.vision = None
        self.cycle = None
        self.time_last_action = time.time()
        
        machines_def = [
          ('cog', (
            (STARTED, self.st_start, 'stop_state'),
            ('stop_state', self.st_stopped, STOPPED),), None), 
          #('bor',   (
          #  (STARTED, self.st_check_boredom,   None), ),  'cog'),
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
        self.from_gq = from_gq
        self.to_gq = to_gq
        

    def st_start(self):
        item = None
        while not item:
            try:    # query the queue
                item = self.from_gq.get()
            except Queue.Empty:
                item = None

        if item[0] == "do_behaviour":
            self.cycle = item[4]
            self.time_last_action = time.time()
            self.do_behaviour(item[1], item[2], item[3])
            self.time_last_action = time.time()
            
            
        if item[0] == "end":
            print "ending"
            self.comm_expr.set_fExpression("neutral", intensity=.8)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , 0.0))")
            self.comm_expr.set_gaze((0.0,1.0,0.0), duration=1.0)
            self.comm_expr.sendDB_waitReply()
            return True
          
        
    def st_check_boredom(self):
        """if we have done nothing for a while, do something random
        """
        time.sleep(0.5)
        if time.time() - self.time_last_action > MIN_TIME_MOVES:
            self.do_random_behaviour_small()
            print "small random move"
    
    
    def do_behaviour(self, behaviour, gaze_target, teacher_word):
        if behaviour == "1": # starting
            pass
        if behaviour == "2A": # waiting for teacher to choose a topic
            self.comm_expr.set_gaze((0,10,0), duration=1.0)
            self.comm_expr.sendDB_waitReply()
            signs = [1.0, -1.0]
            sign_mod = signs[ran.randint(0,1)]
                
            self.comm_expr.set_gaze((PARAM_GAZE_X*sign_mod,1.0,-PARAM_GAZE_Y), duration=2.0)
            self.comm_expr.set_spine('shoulderr', (0.0, .0, .0), 'o', duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((%2f, 0.0 , -.7))" % (-.6*sign_mod))
            self.comm_expr.sendDB_waitReply()
            
            self.comm_expr.set_text(self.get_next_round_statement())    # get speech
            self.comm_expr.send_datablock()     # we are not waiting for the text to finish
            
            self.comm_expr.set_gaze((0.0,1.0,-PARAM_GAZE_Y), duration=1.5)
            self.comm_expr.set_spine('shoulderr',(0.0, .0, .0), 'o', duration=1.5)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , -0.7))")
            self.comm_expr.sendDB_waitReply()

            self.comm_expr.set_gaze((-PARAM_GAZE_X*sign_mod,1.0,-PARAM_GAZE_Y), duration=1.0)
            self.comm_expr.set_spine('shoulderr',(0.0, .0, .0), 'o', duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((%2f, 0.0 , -0.7))"% (.6*sign_mod))
            self.comm_expr.sendDB_waitReply()
                
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
            self.comm_expr.set_gaze((PARAM_GAZE_X*sign_mod,1.0,-PARAM_GAZE_Y), duration=1.0)
            self.comm_expr.set_spine('shoulderr',(0.0, .0, .0), 'o', duration=2.0)
            self.comm_expr.set_instinct("gaze-control:target=((%2f, 0.0 , -.6))" % (-.6*sign_mod))
            self.comm_expr.sendDB_waitReply()
            
            self.comm_expr.set_text(self.get_next_round_active_statement())    # get speech
            self.comm_expr.send_datablock()     # we are not waiting for the text to finish
            
            self.comm_expr.set_gaze((0.0,1.0,-PARAM_GAZE_Y), duration=1.5)
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=1.5)
            self.comm_expr.set_spine('shoulderr',(0.0, .0, .0), 'o', duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , -0.6))")
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_gaze((-PARAM_GAZE_X*sign_mod,1.0,-PARAM_GAZE_Y), duration=1.0)
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=1.0)
            self.comm_expr.set_spine('shoulderr',(0.0, .0, .0), 'o', duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((%2f, 0.0 , -0.6))"% (.6*sign_mod))
            self.comm_expr.sendDB_waitReply()
            
            self.comm_expr.set_fExpression("evil_grin", intensity=.8, duration=1.0)
            self.comm_expr.set_gaze(  ( -PARAM_GAZE_X + (gaze_target*PARAM_GAZE_X), 1.0, -PARAM_GAZE_Y), duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=[[%2f, 0.0, -.6]]" % (.5 - (gaze_target*.6)))
            self.comm_expr.sendDB_waitReply()
        if behaviour == "3": # don't know word
            self.follow_face = True
            self.comm_expr.set_text(self.get_dont_know_statement(teacher_word))    # get speech
            #self.comm_expr.set_gaze((0.2,1.0,0.2), duration=.5)
            self.comm_expr.set_fExpression("surprised", intensity=1.0,)
            self.comm_expr.sendDB_waitReply()   # get speech
            #self.comm_expr.set_gaze((0.0,1.0,0.0), duration=1.0)
            #self.comm_expr.sendDB_waitReply()
        if behaviour == "4": # learns word
            self.follow_face = False
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=2.0)
            self.comm_expr.set_gaze(  ( -PARAM_GAZE_X + (gaze_target*PARAM_GAZE_X), 1.0, -PARAM_GAZE_Y), duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=[[%2f, 0.0, -.6]]" % (.5 - (gaze_target*.5)))
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_text(self.get_learning_statement(teacher_word))    # get speech
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , -.3))")
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=2.0)
            self.comm_expr.sendDB_waitReply()
            self.to_gq.put(["done"], None)
        if behaviour == "5": # guessing an animal
            self.follow_face = False
            signs = [1.0, -1.0]
            sign_mod = signs[ran.randint(0,1)]
            self.comm_expr.set_gaze((PARAM_GAZE_X*sign_mod,1.0,-PARAM_GAZE_Y), duration=1.0)
            self.comm_expr.set_spine('shoulderr', (0.0, .0, .0), 'o', duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((%2f, 0.0 , -.7))" % (-.6*sign_mod))
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_text(self.get_guessing1_statement(teacher_word))    # get speech
            self.comm_expr.send_datablock()     # we are not waiting for the text to finish
            self.comm_expr.set_gaze((0.0,1.0,-PARAM_GAZE_Y), duration=1.0)
            self.comm_expr.set_spine('shoulderr',(0.0, .0, .0), 'o', duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , -0.7))")
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_gaze((-PARAM_GAZE_X*sign_mod,1.0,-PARAM_GAZE_Y), duration=1.0)
            self.comm_expr.set_spine('shoulderr',(0.0, .0, .0), 'o', duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((%2f, 0.0 , -0.7))"% (.6*sign_mod))
            self.comm_expr.sendDB_waitReply()
            
            self.comm_expr.set_text(self.get_guessing2_statement(teacher_word))    # get speech
            self.comm_expr.set_gaze(  ( -PARAM_GAZE_X + (gaze_target*PARAM_GAZE_X), 1.0, -PARAM_GAZE_Y), duration=1.0)
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=[[%2f, 0.0, -.45]]" % (.5 - (gaze_target*.5)))
            self.follow_face = True
            self.comm_expr.sendDB_waitReply()
            
            
            #self.comm_expr.set_spine('shoulderr',(0.0, .0, .0), 'o', duration=1.0)
            #self.comm_expr.set_instinct("gaze-control:target=[[%2f, 0.0, -.4]]" % (.5 - (gaze_target*.5)))
            #self.comm_expr.sendDB_waitReply()
            
        if behaviour == "6": # guessed right
            self.follow_face = False
            self.comm_expr.set_text(self.get_correct_statement())    # get speech
            self.comm_expr.set_gaze((0.0,1.0,0.0), duration=1.0)
            self.comm_expr.set_fExpression("smiling", 1.0, duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , -.3))")
            self.comm_expr.sendDB_waitReply()
            self.to_gq.put(["done"], None)
        if behaviour == "7": # guessed wrong
            self.follow_face = False
            self.comm_expr.set_text(self.get_wrong_statement())
            self.comm_expr.set_gaze((0.0,1.0,0.0), duration=1.0)
            self.comm_expr.set_fExpression("disgust1", 1.0, duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , -.3))")
            self.comm_expr.sendDB_waitReply()
            self.to_gq.put(["done"], None)
        if behaviour == "8": # language game over
            print "LG over"
            self.comm_expr.set_text("Thank you, and bye bye")
            self.comm_expr.set_fExpression("smiling", 1.0)
            self.comm_expr.sendDB_waitReply()


    def get_next_round_statement(self):
        if self.cycle < 6:
            stats = ("mentally choose an animal, and tell me its category",
                     "think of an animal, and tell me its category",
                     "picture an animal in your mind, and let me know which category it belongs to!",
                     "decide on an animal, and click on the category it belongs to!",
                     "choose an animal that you want me to guess, and click its category")
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
        stats = ("uum, I don't know what a " + teacher_word + " is, click on the animal",
                 "I don't have a clue what a " + teacher_word + " might be, click on the correct animal",
                 "Never heard off " + teacher_word + " before, let me know what animal this is",
                 "don't know " +teacher_word + ", tell me what it is",
                 teacher_word + "?, I don't really know, click on the correct animal so I can learn",
                 teacher_word + "? I don't know that one. click on the animal",
                 "a " +teacher_word+ "? No clue. click on the correct animal") 
        return stats[ran.randint(0, len(stats)-1)]
    
    
    def get_learning_statement(self, teacher_word):
        stats = ("ah, so this is a " + teacher_word,
                 "so this is what a " + teacher_word + " looks like",
                 "right, good to know",
                 "allright, now I know what a " + teacher_word + " looks like",
                 "ok, so a " + teacher_word + " looks like this")
        return stats[ran.randint(0, len(stats)-1)]
    
    
    def get_guessing1_statement(self, teacher_word):
        stats = ("right, lets see",
                 "a " + teacher_word + "?, em",
                 teacher_word + "?, I should know",
                 "I know what a " +teacher_word+ " is",
                 teacher_word + "?, lets see which one that is",
                 "ok, I should know",
                 "a " + teacher_word + "?, that should not be too hard",
                 "Yes, I am familiar with a " + teacher_word)
        return stats[ran.randint(0, len(stats)-1)]
    
    
    def get_guessing2_statement(self, teacher_word):
        stats = ("I'm guessing this is a " + teacher_word + "?, click on the animal that you had in mind",
                 "is this a " + teacher_word + "? tell me which animal you had in mind",
                 "I think this is a " + teacher_word + "?, tell me if I am correct",
                 "Am I correct in thinking this is a " + teacher_word + "?, click on the correct animal",
                 "um, I think this is a " + teacher_word + ", is that correct?",
                 "a " + teacher_word + "?, that must be this one!",
                 "um, I think this is a " + teacher_word+ ", right?",
                 "yes, I think this is a " + teacher_word+ ", did I guess right?",
                 "it is this one!, right?" )
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
                 "um, too bad",
                 "no, not wrong again", 
                 "too bad, I thought I knew that one",
                 "sadly, I am mistaken",
                 "really? I thought otherwise, oh well",
                 "if you say so, I guess I was wrong",
                 "um, I guessed wrong",
                 "is that not correct?, oh well",
                 "are you sure, well, if you say so")
        return stats[ran.randint(0, len(stats)-1)]


    def do_random_behaviour_small(self):
        var = 100.0
        ran_x, ran_y, ran_z = ran.randint(-50,50)/var, ran.randint(-50,50)/var, ran.randint(-50,50)/(var*2)
        self.comm_expr.set_gaze((ran_x/-2.0, 1.0, ran_z), duration=1.0)
        self.comm_expr.set_spine('shoulderr', (0.0, .0, .0), 'o', duration=1.0)
        self.comm_expr.set_instinct("gaze-control:target=((%2f, 0.0 , %2f))" %(ran_x, ran_z) )
        self.comm_expr.sendDB_waitReply(tag='BOR')
        self.time_last_action = time.time()
    
    
    def do_random_behaviour_big(self):
        pass
    
    
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
                    self.comm_expr.set_gaze(self.calc_face_target())
                    self.comm_expr.sendDB_waitReply()
        return len(self.faces)


    def calc_face_target(self):
        rect = self.faces[0]
        fx, fy, fw, fh = rect.x, rect.y, rect.w, rect.h
        face_dist = ((-88.5 * math.log(fw)) + 538.5)
        fx = fx + (fw/2.0)
        fy = fy + (fh/2.0)
        x_dist = 0.3 * (((fx/640.0) *-2) +1)
        y_dist = 0.2 * (((fy/480.0) *-2) +1)
        return (x_dist, face_dist/100.0, y_dist)
    
    
    def update_vision(self):
        self.vision.update()
        self.vision.gui_show()
        
    
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

