#! /usr/bin/python -u
# (Note: The -u disables buffering, as else we don't get Julius's output.)
#
# Command and Control Application for Julius
#
# How to use it:
#  julius -quiet -input mic -C julian.jconf 2>/dev/null | ./command.py
#
# Copyright (C) 2008, 2009 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import sys, os, threading, time
import robot_control, communication


#variables
class Params():
    def __init__(self):
        self.use_gui = True
        self.use_comm = False           # communicate with expression server
        self.server = '141.163.186.5'   # server address
        self.port = 4242                # server port
        self.command = '0'
        self.show = True
        self.face_d = True
        self.detect_threshold = 35
        self.follow_face_gaze = True
        self.follow_face_neck = False
        self.search_for_face = False
        self.eye_d = False
        self.edge_d = False
        self.edge_d_non_vision = True
        self.circle_d = False
        self.detect_colour = False
        self.colour_to_find = None
        self.colour_s = False
        self.save_video = False
        self.kalm = False
        self.quit = False
        self.check = True
        self.size = False
        self.game_coors = "10.0, 50.0, 0.0"
        self.x_search = -0.5
        self.print_d = False
        self.cam_shift = False
        self.slow_adjust = True
        self.face_x = None
        self.face_y = None
        self.gain = 0.2
        self.neck_pos = [0.0, 0.0, 0.0]
        self.gaze_pos = [0.0, 0.5, 0.0]
        self.idle_go = True
        self.follow_ball_neck = True
        self.follow_ball_gaze = False
        
        
class Parser:
    
    def __init__(self, robot_control, comm):
        self.rc = robot_control
        self.comm = comm
    
    def parse(self, words):
        if len(words) == 1:
            word1 = words[0]
        if len(words) == 2:
            word1 = words[0]
            word2 = words[1]
        if len(words) == 3:
            word1 = words[0]
            word2 = words[1]
            word3 = words[2]
            

        if (word1 == 'do' and word2 == 'idle') or (word1 == 'free' and word2 == 'time'):
            self.rc.behaviour_change = True
            self.rc.behaviour = "idle"
            return "parsed"
        
        elif (word1 == 'track' or word1 == 'look') and word2 == 'face':
            self.rc.behaviour_change = True
            self.rc.p.search_for_face = True
            self.comm.set_expression("idle", "happy", 1.0)
            self.rc.behaviour = "follow_face"
            self.rc.p.idle_go = False
            return "parsed"
 
        elif (word1 == 'find' or word1 == 'look') and word2 == 'ball':
            self.rc.behaviour_change = True
            self.rc.behaviour = "find_ball"
            self.rc.p.idle_go = False
            return "parsed"     
            
        elif word1 == 'colour' and word2 == 'is' and word3:
            self.rc.learn_colour(word3)
            return "parsed"
            
        elif word1 == 'show' and word2:
            self.rc.show_colour(word2)
            return "parsed"
        
        elif word1 == 'system' and word2 == 'forget':
            self.rc.forget()
            return "parsed"
        
        elif word1 == 'system' and word2 == 'end':
            self.rc.end()
            return "parsed"
        
        elif word1 == 'thank' and word2 == 'you':
            self.rc.behaviour_change = True
            self.rc.behaviour = "thanks"
            self.rc.p.idle_go = False
            pass
            return "parsed"
        
        elif word1 == 'system' and word2 == 'quit':
            self.rc.close()
            sys.exit(0)
            print "stopping"
            
        elif word1 == 'bye' and word2 == 'bye':
            self.rc.close()
            sys.exit(0)
            print "stopping"
        
        else:
            return "no"


class VoiceCommand:
    
    def __init__(self, file_object):
        
        self.params = Params()
        self.comm = communication.CommBase(self.params) 
        
        self.rc = robot_control.RobotControl(self.params, self.comm)
        self.rc.start()
        self.parser = Parser(self.rc, self.comm)

        startstring = 'sentence1: <s> '
        endstring = ' </s>'
        
        print "please give voice command"
        
        while 1:
            line = file_object.readline()
            if not line:
                break
            if 'missing phones' in line.lower():
                print 'Error: Missing phonemes for the used grammar file.'
                sys.exit(1)
            if line.startswith(startstring) and line.strip().endswith(endstring):
                self.parse(line.strip('\n')[len(startstring):-len(endstring)])
    
    def parse(self, line):
        # Parse the input
        params = [param.lower() for param in line.split() if param]
        if not '-q' in sys.argv and not '--quiet' in sys.argv:
            print 'Recognized input:', ' '.join(params).capitalize()
            #self.rb.voice_received()
            #self.comm.send_msg(";;;;-blink;;tag_SPEECH")
        
        # Execute the command, if recognized/supported
        result = self.parser.parse(params)
        if result == "parsed":
            pass
            #self.comm.send_msg("acknowledging;*;1;;;;tag_SPEECH")
        
        elif not '-q' in sys.argv and not '--quiet' in sys.argv:
            print 'Command not supported'
            

if __name__ == '__main__':
    try:
        VoiceCommand(sys.stdin)
    except KeyboardInterrupt:
        sys.exit(1)
