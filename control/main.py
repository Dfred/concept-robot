#!/usr/bin/python

###################################################################
# robot_control.py                                                #
#                                                                 #
# The CONCEPT project. University of Plymouth, United Kingdom     #
# More information at http://www.tech.plym.ac.uk/SoCCE/CONCEPT/   #
#                                                                 #
# Copyright (C) 2010 Joachim de Greeff (www.joachimdegreeff.eu)   #
#                                                                 #
# This program is free software: you can redistribute it and/or   #
# modify it under the terms of the GNU General Public License as  # 
# published by the Free Software Foundation, either version 3 of  #
# the License, or (at your option) any later version.             #
#                                                                 #
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    # 
# GNU General Public License for more details.                    #
###################################################################



import sys, os, threading, time, random, math, optparse
import communication, vision, agent, inout, config


def main():
    """ main
    """
    # parse arguments
    parser = optparse.OptionParser()
    parser.add_option("-c", "--control", dest="control",
                      default="keyboard", type="string",
                      help="specifies type of control. Options are: " + str(config.control_options)  )
    parser.add_option("-g", "--gui",
                      action="store_true", dest="gui", default=True,
                      help="specifies if a GUI is used")

    (options, args) = parser.parse_args()
    if options.control in config.control_options:
        config.control = options.control
    else:
        print "Please specify a valid control option. \n"\
              "Options are: " + str(config.control_options)
        exit(1)
    config.use_gui = options.gui
    
    # create appropriate connections
    connections = connect()                 
    
    # create robot control        
    rb = RobotControl(connections[0])       
    rb.start()
    
    #print connections[1].get_snapshot()



def connect():
    """ connect to the appropriate sources
    """
    if config.use_comm_expression:
        comm_expression = communication.CommBase(config.expression_server, config.expression_port)
        if not comm_expression.connected_to_server:
            comm_expression = None
    else:
        comm_expression = None
        
    if config.use_comm_features:
        comm_features = communication.CommBase(config.features_server, config.features_port)
        if not comm_features.connected_to_server:
            comm_features = None
    else:
        comm_features = None
        
    return (comm_expression, comm_features)



class RobotControl(threading.Thread):
    """ main robot control
    """
    
    def __init__(self, comm):
        
        threading.Thread.__init__(self)
        self.comm = comm
        self.camera = vision.CaptureVideo(self.comm)
        self.camera.start()
        self.camera_ball = None
        self.learning_agent = agent.Agent("agent", "learner")
        self.record = RobotRecord()
        self.behaviour = None
        self.behaviour_change = True
        self.go = True
        
        # length, width, height of the room
        self.environment = (7, 3, 2.5)
        self.robot_pos = (3.5, 0.75, 0.75)

        
    def run(self):

        #TODO: set checks for missing comm
        while self.go:  # main behaviour
            if self.behaviour == "idle":
                if self.behaviour_change:
                    print "behaviour is idle"
                    self.record.behaviour_transition("idle")
                    self.behaviour_change = False                
                config.idle_go = True
                config.cam_shift = False
                config.follow_face_neck = False
                self.run_idle()
                
            elif self.behaviour == "thanks":
                if self.behaviour_change:
                    print "behaviour is thanks"
                    self.record.behaviour_transition("thanks")
                    self.behaviour_change = False
                    self.comm.set_neck_orientation("(0,0,0)")
                    time.sleep(0.2)
                    self.comm.set_neck_orientation("(0.15,0,0)")
                    time.sleep(0.01)
                    self.comm.set_neck_orientation("(0,0,0)")
                    self.comm.set_gaze(str(config.gaze_pos[0]) + "," + str(config.gaze_pos[1]) + "," + str(config.gaze_pos[2]))
                config.cam_shift = False
                config.follow_face_gaze = False
                config.follow_face_neck = False
                config.follow_ball_neck = False
                config.follow_ball_gaze = False
                config.colour_to_find = None
                self.behaviour_change = False
                self.comm.set_expression("neutral", "*", 0.5)
                self.behaviour = None

                    
            elif self.behaviour == "follow_face":
                if self.behaviour_change:
                    print "behaviour is follow_face"
                    self.record.behaviour_transition("follow_face")
                    self.behaviour_change = False
                config.cam_shift = True
                config.follow_face_gaze = True
                config.follow_face_neck = True


            elif self.behaviour == "find_face":
                print "behaviour is find_face"
                config.face_d = True
                if self.behaviour_change:
                    self.record.behaviour_transition("find_face")
                    self.behaviour_change = False
                
            elif self.behaviour == "find_ball":
                if self.behaviour_change:
                    self.comm.set_expression("staring", "happy", 0.5)
                    print "behaviour is find_ball"
                    config.follow_ball_neck = True
                    config.follow_ball_gaze = True
                    #self.comm.set_neck_orientation("(0.7, 0, 0)", "LB")
                    #config.neck_pos[0] += 0.7    # keep track of position
                    self.record.behaviour_transition("find_ball")
                    self.behaviour_change = False
                    #config.command = 'q'
                    #time.sleep(1)
                    #self.camera_ball = vision.CaptureVideo(config, self.comm)
                    #self.camera.start()
                config.circle_d = True

                
            else:
                #self.end()
                
                # preview of keyboard input_control...
        		import select
        		if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
        		    if sys.stdin.read(1) == 'f':
        		        self.find_face()
                #time.sleep(1)
                #print "waiting"

        print "RobotControl closed"
        
        
    def run_idle(self):
        counter = 0
        while config.idle_go:
            time.sleep( random.randrange(0, 500, 1)/500.0 )
            counter += 1
            sequence = []
            tilt = str( (random.randrange(-3, 3, 1)/100.0)*math.pi)
            rot = str(0) #str( (random.randrange(-20, 20, 1)/100.0)*math.pi)
            seq = "(" + tilt + "," + rot + ","
            if random.randint(0,1): #go right
                if random.randint(0,1):
                    sequence.append( seq + str( (random.randrange(0, 26, 1)/100.0)*0.5*math.pi) + ")")
                    sequence.append( seq + str( (random.randrange(26, 51, 1)/100.0)*0.5*math.pi) + ")")
                else:
                    sequence.append( seq + str( (random.randrange(26, 51, 1)/100.0)*0.5*math.pi) + ")")
                    sequence.append( seq + str( (random.randrange(0, 26, 1)/100.0)*0.5*math.pi) + ")")
            else: #go left
                if random.randint(0,1):
                    sequence.append( seq + str( (random.randrange(0, 26, 1)/-100.0)*0.5*math.pi) + ")")
                    sequence.append( seq + str( (random.randrange(26, 51, 1)/-100.0)*0.5*math.pi) + ")")
                else:
                    sequence.append( seq + str( (random.randrange(26, 51, 1)/-100.0)*0.5*math.pi) + ")")
                    sequence.append( seq + str( (random.randrange(0, 26, 1)/-100.0)*0.5*math.pi) + ")")
            
            for x, i in enumerate(sequence):
                time.sleep( random.randrange(0, 500, 1)/500.0 )
                self.comm.set_neck_orientation(str(i), str(x))
#                x_gaze = random.randrange(0,30,1)/100.0
#                y_gaze = random.randrange(0,30,1)/100.0
#                z_gaze = random.randrange(0,30,1)/100.0
#                set_gaze(str(x_gaze) + "," + str(y_gaze) + "," str(z_gaze))
                while self.comm.last_ack != "tag_NK_OR_" + str(x):
                    pass # wait for acknowledgement
                    
        
    def find_face(self):
        self.behaviour = "find_face"
        config.idle_go = False
        
        
    def learn_colour(self, word3):
        config.detect_colour = True
        config.idle_go = False
        time.sleep(0.1)
        percept_data = self.camera.return_colour()
        if percept_data:
            #per_dat = [["c",[["h",percept_data[0]],  ["s",percept_data[1]], ["v",percept_data[2]]]]]
            per_dat = [["c",[["r",percept_data[0]],  ["g",percept_data[1]], ["b",percept_data[2]]]]]
            self.learning_agent.learn_concept(word3, per_dat)
            print "\n learning " + word3
            inout.save_knowledge(self.learning_agent)
        else:
            print "I didn't get it, please repeat"
        
        
    def show_colour(self, word2):
        config.idle_go = False
        percept = self.learning_agent.get_percept([word2])
        if percept == "no_known_words":
            print "I don't know " + word2
        else:
            self.behaviour = "find_ball"
            config.follow_ball_neck = False
            config.colour_to_find = percept.get_data()
            
    def forget(self):
        print "I have forgotten everything"
        self.learning_agent = agent.Agent("agent", "learner")
        self.end()
            
            
    def end(self):
        config.idle_go = False
        self.behaviour = None
        print "ending"
        config.circle_d = False
        config.face_d = False
        config.edge_d = False
        config.detect_colour = False
        config.colour_to_find = None
        config.colour_s = False
        config.save_video = False
        config.follow_face = False
        config.follow_ball_neck = False
        if config.circle_d:
            config.circle_d = False
        
    def close(self):
        config.idle_go = False
        config.command = 'q'
        self.comm.close()
        self.go = False
        
        
class RobotRecord():
    """ records of all behaviour and movements during one session
    """
    
    def __init__(self):
        self.behaviour_list = []    # list of behaviours + timestamp initiated
        self.idle_counter = 0
        self.follow_face_counter = 0
        self.search_counter = 0
        self.intial_position = 0
        self.positions_list = []    # list of position + timestamp initiated
        
    def behaviour_transition(self, behaviour):
        if behaviour == "idle":
            self.behaviour_list = [["idle" + str(self.idle_counter), time.time()]]
            self.idle_counter += 1
        if behaviour == "follow_face":
            self.behaviour_list = [["follow_face" + str(self.idle_counter), time.time()]]
            self.follow_face_counter += 1
        
        

if __name__ == "__main__":
    main()
