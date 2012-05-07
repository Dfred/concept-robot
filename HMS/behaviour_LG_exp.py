#!/usr/bin/python
# -*- coding: utf-8 -*-

# behaviours to be used in conjunction with LG experiments

import logging
import time, Queue, math
import random as ran

from HMS.behaviour_builder import BehaviourBuilder, fatal
from HMS.communication import MTLightheadComm
from utils.parallel_fsm import STARTED, STOPPED, MPFSM as FSM
from utils import conf, vision

LOG = logging.getLogger(__package__)


PARAM_GAZE_X = 0.14     # parameters for touchscreen
PARAM_GAZE_Y = 0.32
USER_URGE = 13          # time to wait before urging the user

# STATES
ST_BORED        = 'check_bored'
ST_CHECKB       = 'urge_user'

cat_text_colours = {1: "colour",
                   2: "a colour",
                   3: "colours",
                   4: "",
                   5: ""}

cat_text_animals = {1: "animal",
                    2: "an animal",
                    3: "animals",
                    4: "a ",
                    5: "the "}


class LightHead_Behaviour(BehaviourBuilder):
    """
    """
    
    def __init__(self, from_gq, to_gq, participant_nr, with_gui=True, with_vision=True):
        self.participant_nr = participant_nr
        self.gaze_target = None
        self.faces = []
        self.follow_face = False
        self.look_at_target = False
        self.expect_user_input = False
        self.vision = None
        self.cycle = None
        self.user_timer = 0
        self.var_user_time = 8
        self.cat_text = cat_text_colours
        self.robot_speech = None
        self.statement_history = []

        machines_def = [
          ('cog', (
            (STARTED, self.st_start, 'stop_state'),
            ('stop_state', self.st_stopped, STOPPED),), None), 
          ('bor',   (
            (STARTED, self.st_check_boredom,   ST_BORED), 
            (ST_BORED, self.st_urge_user,     ST_CHECKB),
            (ST_CHECKB, self.st_check_boredom, ST_BORED),),  'cog'),
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
                    
                par_name = "par_" + str(self.participant_nr)
                fname = time.strftime("/Users/joachim/Documents/workspace/LG_exp/exp_records/"+par_name+"/"+par_name+"-%H_%M_%S.avi")
                
                print "recording vision as "+fname
                self.vision.toggle_record(fname, fps=11)    #fps=11 seems to correspond with camera capture
                
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
            
        if item[0] == "switch_cat":
            if item[1] == "colours":
                self.cat_text = cat_text_colours
            if item[1] == "animals":
                self.cat_text = cat_text_animals
            
        if item[0] == "end":
            print "ending"
            self.comm_expr.set_fExpression("neutral", intensity=.8)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , 0.0))")
            self.comm_expr.set_gaze((0.0,1.0,0.0), duration=1.0)
            self.comm_expr.sendDB_waitReply()
            return True
          
        
    def st_check_boredom(self):
        """check for no activity from user
        """
        if self.expect_user_input:
            if time.time() - self.user_timer > self.var_user_time:
                return True
        time.sleep(.1)
        return False
    
    
    def st_urge_user(self):
        """ urge user to get going
        """
        self.comm_expr.set_text(self.get_urging_statement())    # get speech
        self.do_random_behaviour_small()
        self.follow_face = True
        self.user_timer = time.time()
        self.var_user_time = ran.gauss(USER_URGE, 2)
        return True
        
    
    def do_behaviour(self, behaviour, gaze_target, teacher_word):
        
        if behaviour == "T": # tutorial
            self.follow_face = True
            self.comm_expr.set_text("Hello. I am the lightHead robot. This experiment is about teaching category names. "+
                                    "I will explain how we are going to do this. ")
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_text("we are going to play a guessing game. First we are going to practice with some colour categories.")
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_text("On the touchscreen, you will see 3 different coloured patches. "+
                                    "you mentally choose one colour patch as the topic for our guessing game. ")
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_text("Then, you tell me the name of this colour by clicking on the corresponding button. ")
            self.comm_expr.sendDB_waitReply()

            gaze_target = 2
            self.comm_expr.set_text("When I hear the colour name, I will try to guess which of the colour patches you were thinking off. ")
            self.comm_expr.send_datablock()     # we are not waiting for the text to finish
            self.comm_expr.set_gaze(  ( -PARAM_GAZE_X + (gaze_target*PARAM_GAZE_X), 1.0, -PARAM_GAZE_Y), duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=[[%2f, 0.0, -.4]]" % (.6 - (gaze_target*.6)))
            
            self.gaze_target = gaze_target
            self.look_at_target = True
            self.comm_expr.sendDB_waitReply()
            
            self.comm_expr.set_text("When I guessed right, you click on the colour patch to confirm")
            self.comm_expr.sendDB_waitReply()
            
            self.comm_expr.set_text("When I guessed wrong, you click on the colour patch that you actually had in mind")
            self.comm_expr.sendDB_waitReply()
            
            self.look_at_target = False
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , 0.0))")
            self.comm_expr.sendDB_waitReply()
            
            self.comm_expr.set_text("If you have any questions, you can ask them to the experimenter. ")
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_text("If you want to hear these instructions again, click on the tutorial button")
            self.comm_expr.sendDB_waitReply()
            
    
            self.comm_expr.set_text("Otherwise, let's start a practice round. " +
                                    "when you are ready with the practice, press the done button")
            self.comm_expr.sendDB_waitReply()
        
            
        if behaviour == "P_done": # starting
            self.expect_user_input = False
            self.comm_expr.set_text("Alright. Practice is done. When you are ready, press the start button to start the experiment.") 
            self.comm_expr.set_gaze((0,10,0), duration=1.0)
            self.comm_expr.set_neck((.0, .0, .0), duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , 0.0))")
            self.comm_expr.sendDB_waitReply()
            
            
        if behaviour == "thanks": # starting
            pass
#            if ran.randint(0,5) > 3:
#                self.comm_expr.set_text("thanks for teaching my choice")
#            self.comm_expr.sendDB_waitReply()
        
        
        if behaviour == "1": # starting
            self.follow_face = True
            self.comm_expr.set_gaze((0,10,0), duration=1.0)
            self.comm_expr.set_neck((.0, .0, .0), duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , 0.0))")
            self.comm_expr.sendDB_waitReply()
        if behaviour == "2A": # waiting for teacher to choose a topic
            self.follow_face = False
            self.comm_expr.set_gaze((0,10,0), duration=1.0)
            self.comm_expr.set_neck((.0, .0, .0), duration=1.0)
            self.comm_expr.sendDB_waitReply()
            signs = [1.0, -1.0]
            sign_mod = signs[ran.randint(0,1)]
                
            self.comm_expr.set_gaze((PARAM_GAZE_X*sign_mod,1.0,-PARAM_GAZE_Y), duration=1.5)
            self.comm_expr.set_spine('shoulderr', (0.0, .0, .0), 'o', duration=1.5)
            self.comm_expr.set_instinct("gaze-control:target=((%2f, 0.0 , -.7))" % (-.6*sign_mod))
            self.comm_expr.sendDB_waitReply()
            
            if self.robot_speech:
                self.statement_history.append(self.robot_speech)
            self.robot_speech = []                                  # reset
            statement = self.get_next_round_statement()             # get speech
            self.robot_speech.append(statement)                     # record
            self.comm_expr.set_text(statement)                      # speak
            self.comm_expr.send_datablock()                         # we are not waiting for the text to finish
            
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
            self.expect_user_input = True
            self.user_timer = time.time()
        if behaviour == "2B": # trying to indicate preferred topic to teacher
            self.follow_face = False
            self.comm_expr.set_gaze((0,10,0), duration=1.0)
            self.comm_expr.sendDB_waitReply()
            signs = [1.0, -1.0]
            sign_mod = signs[ran.randint(0,1)]
                
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=1.5)
            self.comm_expr.set_gaze((PARAM_GAZE_X*sign_mod,1.0,-PARAM_GAZE_Y), duration=1.5)
            self.comm_expr.set_spine('shoulderr',(0.0, .0, .0), 'o', duration=2.0)
            self.comm_expr.set_instinct("gaze-control:target=((%2f, 0.0 , -.6))" % (-.6*sign_mod))
            self.comm_expr.sendDB_waitReply()
            
            if self.robot_speech:
                self.statement_history.append(self.robot_speech)
            self.robot_speech = []                                  # reset
            statement = self.get_next_round_active_statement()      # get speech
            self.robot_speech.append(statement)                     # record
            self.comm_expr.set_text(statement)                      # speak
            self.comm_expr.send_datablock()                         # we are not waiting for the text to finish
            
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
        
            statement = self.get_active_choice_statement()          # get speech
            self.robot_speech.append(statement)                     # record
            self.comm_expr.set_text(statement)                      # speak
            self.comm_expr.set_fExpression("evil_grin", intensity=.8, duration=1.0)
            self.comm_expr.set_gaze(  ( -PARAM_GAZE_X + (gaze_target*PARAM_GAZE_X), 1.0, -PARAM_GAZE_Y), duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=[[%2f, 0.0, -.4]]" % (.6 - (gaze_target*.6)))
            self.comm_expr.sendDB_waitReply()
            
            self.follow_face = True
            self.gaze_target = gaze_target
            self.look_at_target = True
            
            self.comm_expr.set_gaze(  ( -PARAM_GAZE_X + (self.gaze_target*PARAM_GAZE_X), 1.0, -PARAM_GAZE_Y), duration=.3)
            self.comm_expr.sendDB_waitReply()
            
        if behaviour == "3": # don't know word
            self.expect_user_input = False
            self.look_at_target = False
            self.follow_face = True
            statement = self.get_dont_know_statement(teacher_word)  # get speech
            self.robot_speech.append(statement)                     # record
            self.comm_expr.set_text(statement)                      # speak
            self.comm_expr.set_fExpression("surprised", intensity=.6,)
            self.comm_expr.set_neck((.0, .1, .0), duration=.3)
            self.comm_expr.sendDB_waitReply()
        if behaviour == "4": # learns word
            self.follow_face = False
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=2.0)
            tar_values = ( -PARAM_GAZE_X + (gaze_target*PARAM_GAZE_X), 1.0, -PARAM_GAZE_Y)
            self.comm_expr.set_gaze(self.gaze_around_target(tar_values) , duration=.2)
            self.comm_expr.set_instinct("gaze-control:target=[[%2f, 0.0, -.6]]" % (.5 - (gaze_target*.5)))
            self.comm_expr.set_neck((.0, .0, .0), duration=.3)
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_gaze(self.gaze_around_target(tar_values) , duration=.3)
            self.comm_expr.sendDB_waitReply()

            statement = self.get_learning_statement(teacher_word)   # get speech
            self.robot_speech.append(statement)                     # record
            self.comm_expr.set_text(statement)                      # speak
            self.comm_expr.send_datablock()                         # we are not waiting for the text to finish
            self.comm_expr.set_gaze(self.gaze_around_target(tar_values) , duration=.3)
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_gaze(self.gaze_around_target(tar_values) , duration=.3)
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_gaze(self.gaze_around_target(tar_values) , duration=.3)
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_gaze(self.gaze_around_target(tar_values) , duration=.3)
            self.comm_expr.sendDB_waitReply()
            
            self.follow_face = True
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , -.3))")
            self.comm_expr.sendDB_waitReply()
   
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=1.0)
            self.comm_expr.sendDB_waitReply()
            self.to_gq.put(["done"], None)
        if behaviour == "5": # guessing an animal
            self.expect_user_input = False
            self.follow_face = False
            signs = [1.0, -1.0]
            sign_mod = signs[ran.randint(0,1)]
             
            statement = self.get_guessing1_statement(teacher_word)  # get speech
            self.robot_speech.append(statement)                     # record
            self.comm_expr.set_text(statement)                      # speak
            self.comm_expr.send_datablock()                         # we are not waiting for the text to finish
            self.comm_expr.set_gaze((PARAM_GAZE_X*sign_mod,1.0,-PARAM_GAZE_Y), duration=1.5)
            
            self.comm_expr.set_spine('shoulderr', (0.0, .0, .0), 'o', duration=1.5)
            self.comm_expr.set_instinct("gaze-control:target=((%2f, 0.0 , -.7))" % (-.6*sign_mod))
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_gaze((0.0,1.0,-PARAM_GAZE_Y), duration=1.0)
            self.comm_expr.set_spine('shoulderr',(0.0, .0, .0), 'o', duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , -0.7))")
            self.comm_expr.sendDB_waitReply()
            self.comm_expr.set_gaze((-PARAM_GAZE_X*sign_mod,1.0,-PARAM_GAZE_Y), duration=1.0)
            self.comm_expr.set_spine('shoulderr',(0.0, .0, .0), 'o', duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((%2f, 0.0 , -0.7))"% (.6*sign_mod))
            self.comm_expr.sendDB_waitReply()
            
            statement = self.get_guessing2_statement(teacher_word)  # get speech
            self.robot_speech.append(statement)                     # record
            self.comm_expr.set_text(statement)                      # speak
            dur = .5 + ((len(statement)-23)*.01)
            self.comm_expr.set_gaze(  ( -PARAM_GAZE_X + (gaze_target*PARAM_GAZE_X), 1.0, -PARAM_GAZE_Y), duration=dur)
            
            
            self.comm_expr.set_fExpression("neutral", intensity=.8, duration=.5)
            self.comm_expr.set_instinct("gaze-control:target=[[%2f, 0.0, -.4]]" % (.6 - (gaze_target*.6)))
            self.follow_face = True
            self.gaze_target = gaze_target
            self.look_at_target = True
            self.comm_expr.sendDB_waitReply()
            
            #self.comm_expr.set_spine('shoulderr',(0.0, .0, .0), 'o', duration=1.0)
            #self.comm_expr.set_instinct("gaze-control:target=[[%2f, 0.0, -.4]]" % (.5 - (gaze_target*.5)))
            #self.comm_expr.sendDB_waitReply()
            
        if behaviour == "6": # guessed right
            self.look_at_target = False
            statement = self.get_correct_statement()                # get speech
            self.robot_speech.append(statement)                     # record
            self.comm_expr.set_text(statement)                      # speak
            self.comm_expr.set_gaze((0.0,1.0,0.0), duration=.5)
            self.comm_expr.set_fExpression("smiling", 1.0, duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , -.3))")
            self.comm_expr.sendDB_waitReply()
            self.to_gq.put(["done"], None)
        if behaviour == "7": # guessed wrong
            self.look_at_target = False
            statement = self.get_wrong_statement()                  # get speech
            self.robot_speech.append(statement)                     # record
            self.comm_expr.set_text(statement)                      # speak
            self.comm_expr.set_gaze((0.0,1.0,0.0), duration=.5)
            self.comm_expr.set_fExpression("disgust1", 1.0, duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , -.3))")
            self.comm_expr.sendDB_waitReply()
            self.to_gq.put(["done"], None)
        if behaviour == "8": # language game over
            print "LG over"
            statement = "We are finished now. Thank you, and bye bye"    # get speech
            if self.robot_speech:
                self.robot_speech.append(statement)                      # record
            self.comm_expr.set_text(statement)                           # speak
            self.statement_history.append(self.robot_speech)
            self.comm_expr.set_fExpression("smiling", 1.0)
            self.comm_expr.set_neck((.0, .0, .0), duration=1.0)
            self.comm_expr.set_instinct("gaze-control:target=((0.0, 0.0 , 0.0))")
            self.comm_expr.sendDB_waitReply()
            self.to_gq.put(["statement_hist", self.statement_history], None)
            


    def get_next_round_statement(self):
        if self.cycle < 6:
            stats = ("think of " + self.cat_text[2] + ", and tell me its category name",
                     "mentally choose " + self.cat_text[2] + ", and tell me its category name",
                     "picture " + self.cat_text[2] + " in your mind, and let me know which category it belongs to!",
                     "decide on " + self.cat_text[2] + ", and click on the category it belongs to!",
                     "choose " + self.cat_text[2] + " that you want me to guess, and click its category")
            statement = stats[ran.randint(0, len(stats)-1)]
        elif self.cycle < 30:
            stats = ("Lets do another round",
                     "Right, lets go again",
                     "here are some more " + self.cat_text[3],
                     "what about these?",
                     "lets do some more!",
                     "another guessing round",
                     "let me do some more guessing",
                     "tell me the " + self.cat_text[1] + " category",
                     "lets guess some more",
                     "here we go again",
                     "next round")
        elif self.cycle < 50:
            stats = ("Lets do another round",
                     "Right, lets go again",
                     "here are some more " + self.cat_text[3],
                     "what about these?",
                     "lets do some more!",
                     "another guessing round",
                     "I want to learn more",
                     "tell me a category, and I will guess",
                     "let me do some more guessing",
                     "tell me the " + self.cat_text[1] + " category",
                     "I think this is interesting",
                     "Just wondering about this",
                     "lets guess some more",
                     "I hope you are not tired yet, lets guess some more",
                     "so far so good. More to guess",
                     "Here we go again",
                     "Next round")
            statement = stats[ran.randint(0, len(stats)-1)]
        else:
            statement = "this is the last round"
        return statement
    
    
    def get_next_round_active_statement(self):
        if self.cycle < 6:
            stats = ("I would like to learn another " + self.cat_text[1] + ", tell me its category",
                     "think of " + self.cat_text[2] + ", and tell me its category",
                     "picture " + self.cat_text[2] + " in your mind, and let me know which category it belongs to!",
                     "mentally select " + self.cat_text[2] + ", and click on the category it belongs to!",
                     "decide upon " + self.cat_text[2] + " that you want to teach me, and click its category")
            statement = stats[ran.randint(0, len(stats)-1)]
        elif self.cycle < 30:
            stats = ("Lets do another round",
                     "Right, lets go again",
                     "here are some more " + self.cat_text[3],
                     "what about these?",
                     "lets do some more!",
                     "another guessing round",
                     "let me do some more guessing",
                     "tell me the " + self.cat_text[1] + " category",
                     "lets guess some more",
                     "here we go again",
                     "next round")
        elif self.cycle < 50:
            stats = ("Lets do another round",
                     "Right, lets go again",
                     "here are some more " + self.cat_text[3],
                     "what about these?",
                     "lets do some more!",
                     "another guessing round",
                     "I want to learn more",
                     "tell me a category, and I will guess",
                     "let me do some more guessing",
                     "tell me the " + self.cat_text[1] + " category",
                     "I think this is interesting",
                     "Just wondering about this",
                     "lets guess some more",
                     "I hope you are not tired yet, lets guess some more",
                     "so far so good. More to guess",
                     "Here we go again",
                     "Next round")
            statement = stats[ran.randint(0, len(stats)-1)]
        else:
            statement = "this is the last round"
        return statement
        
        
    def get_active_choice_statement(self):
        stats = ("I would like to learn this one",
                 "could you teach me this one?",
                 "this one looks interesting",
                 "now, what about this one?",
                 "this is interesting",
                 "em, what about this one?",
                 "ok, what do we have here?",
                 "yes, this looks interesting",
                 "what about this one?",
                 "em, I would like to know what this is")
        return stats[ran.randint(0, len(stats)-1)]
            
            
    
    def get_dont_know_statement(self, teacher_word):
        stats = ("uum, I don't know what " + self.cat_text[4] + teacher_word + " is, click on the " + self.cat_text[1],
                 "I don't have a clue what " + self.cat_text[4] + teacher_word + " might be, click on the correct " + self.cat_text[1],
                 "Never heard off " + teacher_word + " before, let me know what " + self.cat_text[1] + " this is",
                 "don't know " +teacher_word + ", tell me what it is",
                 teacher_word + "?, I don't really know, click on the correct " + self.cat_text[1] + " so I can learn",
                 teacher_word + "? I don't know that one. click on the " + self.cat_text[1],
                 self.cat_text[4] + teacher_word+ "? No clue. click on the correct " + self.cat_text[1]) 
        return stats[ran.randint(0, len(stats)-1)]
    
    
    def get_learning_statement(self, teacher_word):
        stats = ("ah, so this is " + self.cat_text[4] + teacher_word,
                 "so this is what " + self.cat_text[4] + teacher_word + " looks like",
                 "right, good to know",
                 "allright, now I know what " + self.cat_text[4] + teacher_word + " looks like",
                 "ok, so " + self.cat_text[4] + teacher_word + " looks like this")
        return stats[ran.randint(0, len(stats)-1)]
    
    
    def get_guessing1_statement(self, teacher_word):
        stats = (self.cat_text[4] + teacher_word + ", right, lets see",
                 self.cat_text[4] + teacher_word + "?, em",
                 teacher_word + "?, I should be able to guess",
                 "I know what " + self.cat_text[4] + teacher_word + " is",
                 teacher_word + "?, lets see what you mean",
                 "ok, I should know" + self.cat_text[4] + teacher_word,
                 self.cat_text[4] + teacher_word + "?, that should not be too hard",
                 "Yes, I am familiar with " + self.cat_text[4] + teacher_word,
                 "you have taught " + teacher_word + " so I should be able to guess")
        return stats[ran.randint(0, len(stats)-1)]
    
    
    def get_guessing2_statement(self, teacher_word):
        stats = (teacher_word + "? Are you thinking of this one?, click on the " + self.cat_text[1] + " that you had in mind",
                 "is this " + self.cat_text[5] + teacher_word + " you were thinking off? tell me which " + self.cat_text[1] + " you had in mind",
                 teacher_word + "?, yes, are you thinking off this one?",
                 "um, " + self.cat_text[5] + teacher_word + "? You are thinking of this one?",
                 "You are thinking of this one, right?", 
                 "Is this the " + self.cat_text[1] +" you were thinking off?",
                 "Is this the " + self.cat_text[1] +" you had in mind?",
                 "Is this the topic of the guessing game?",
                 "are you thinking of this one?",
                 "Is this " + self.cat_text[1] +" the topic?")
#        stats = ("I'm guessing this is " + self.cat_text[5] + teacher_word + "?, click on the " + self.cat_text[1] + " that you had in mind",
#                 "is this " + self.cat_text[5] + teacher_word + "? tell me which " + self.cat_text[1] + " you had in mind",
#                 "I think this is " + self.cat_text[5] + teacher_word + "?, tell me if I am correct",
#                 "Am I correct in thinking " + self.cat_text[5] + teacher_word + " is this one?, tap on the " + self.cat_text[1] + " that you had in mind",
#                 "um, I think this is " + self.cat_text[5] + teacher_word + ", is that correct?",
#                 self.cat_text[4] + teacher_word + "?, that must be this one!",
#                 "um, I think this is " + self.cat_text[5] + teacher_word+ ", right?",
#                 "yes, I think this is " + self.cat_text[5] + teacher_word+ ", did I guess right?",
#                 "it is this one!, right?",
#                 teacher_word + "?, yes, thats this one")
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
                 "wrong guess again", 
                 "too bad, I thought I knew that one",
                 "sadly, I guessed wrong",
                 "really? I thought otherwise, oh well",
                 "if you say so, I guess I was wrong",
                 "um, I guessed wrong",
                 "is that not the one you thought about?",
                 "I didn't read your mind properly")
        return stats[ran.randint(0, len(stats)-1)]


    def get_urging_statement(self):
        stats = ("let's go!",
                 "are you going to tell me anything?",
                 "you do like to take your time, don't you?",
                 "I wonder what's on TV tonight",
                 "don't rush, take all the time you need",
                 "hum, I'm curious what is going to come next",
                 "shall we continue then?",
                 "I'm waiting",
                 "I don't mind you taking your time, but don't push it",
                 "I'm bored",
                 "awaiting your input")
        return stats[ran.randint(0, len(stats)-1)]


    def do_random_behaviour_small(self):
        var = 100.0
        ran_x, ran_y, ran_z = ran.randint(-50,50)/var, ran.randint(-50,50)/var, ran.randint(-50,50)/(var*2)
        self.comm_expr.set_gaze((ran_x/-2.0, 1.0, ran_z), duration=1.0)
        self.comm_expr.set_spine('shoulderr', (0.0, .0, .0), 'o', duration=1.0)
        self.comm_expr.set_instinct("gaze-control:target=((%2f, 0.0 , %2f))" %(ran_x, ran_z) )
        self.comm_expr.sendDB_waitReply(tag='BOR')
        self.time_last_action = time.time()
    
    
    def gaze_around_target(self, target):
        var = 100.0
        ran_x, ran_y, ran_z = ran.randint(-8,8)/var, ran.randint(-8,8)/var, ran.randint(-8,8)/var
        return (ran_x+target[0], target[1], ran_z+target[2])
    
    
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
                    
                    if self.look_at_target: 
                        if ran.randint(1,100) < 20: #occasionally look at target
                            self.comm_expr.set_gaze(  ( -PARAM_GAZE_X + (self.gaze_target*PARAM_GAZE_X), 1.0, -PARAM_GAZE_Y), duration=.3)
                            self.comm_expr.sendDB_waitReply()
                            time.sleep(2)
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

