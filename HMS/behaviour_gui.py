
import threading, math, Queue, time, random
    
from utils import conf, handle_exception, LOGFORMATINFO
from utils.FSMs import SMFSM

from HMS.cogmod import vision, cfg
from HMS.behaviour_builder import BehaviourBuilder
from HMS.communication import ThreadedExpressionComm, ThreadedLightheadComm

show_emo = 1


class Behaviour_thread(threading.Thread):
    """ class which creates a dedicated thread for a Base_behaviour
    """
    
    def __init__(self, from_gui_queue, from_behaviours_queue):
        threading.Thread.__init__(self)
        self.from_gui_q = from_gui_queue
        self.from_beh_q = from_behaviours_queue
        self.base_player = Base_behaviour(self.from_gui_q, self.from_beh_q)
    
    def run(self):
        self.base_player.run()
        self.base_player.cleanup()


class Base_behaviour(BehaviourBuilder):
    """ Base FSM which listens for state changes from gui and triggers behaviours accordingly
    """
    
    def __init__(self, from_gui_q, from_beh_q):
        self.from_gui_q = from_gui_q
        self.from_beh_q = from_beh_q
        BASE_PLAYER_DEF = ( (SMFSM.STARTED,self.started),
                            ('FOLLOW_TARGET', self.set_gaze_neck_to_target),
                            ('RUN_DEMO', self.run_demo_behaviour),
                            ('FACE_GROW', self.face_grow_behaviour),
                            ('FACE_SHRINK', self.face_shrink_behaviour),
                            ('WAVE', self.wave_behaviour),
                            ('MOVE_LIMIT', self.move_limit_behaviour),
                            (SMFSM.STOPPED,self.stopped)
                          )
        machine_def = [ ('base_player', BASE_PLAYER_DEF, None)]
        BehaviourBuilder.__init__(self, machine_def)
        
        self.connected = False
        self.comm_send_tags = []
        # for snapshots, not used atm
        #self.comm_lighthead = Lightheadcomm(conf.lightHead_server, connection_succeded_fct=self.on_connect)
        
        # tuning
        self.gaze_adjust_x = 0.5
        self.gaze_adjust_y = 0.5
        self.neck_adjust_x = 0.5
        self.neck_adjust_y = 0.5
        
        self.last_emo_change = time.time()
        self.last_emotion = "neutral"
        
        self.last_neck_move = None
        
    def on_connect(self):
        self.connected = True
        
        
################# Behaviours ##################################
        
        
    def started(self):
        print 'STATE: test started'
        self.from_beh_q.put(('STATE: test started'), None)
        return 'FOLLOW_TARGET'
    
    
    def wait_for_command(self):
        print 'STATE: awaiting command'
        self.from_beh_q.put(('AWAIT_COMMAND'), None)
        item = None
        while not item:
            try:    # query the queue
                item = self.from_gui_q.get()
            except Queue.Empty:
                item = None
        if item == "quit_fsm":  # if receiving the stop command, move to stop state
            return SMFSM.STOPPED
        else:
            self.from_beh_q.put((item), None)
            return item

        
    def set_gaze_neck_to_target(self):
        """ sets the gaze and or neck to target pulled from the vision queue
        """
        
        print "STATE: setting gaze and neck to target"
        
        self.comm_send_tags = []
        
        while True:
            try:    # query the queue
                item = self.from_gui_q.get()
            except Queue.Empty:
                item = None
                
            if item:
                if item == "quit_fsm":  # if receiving the stop command, move to stop state
                    return SMFSM.STOPPED
                
                elif item == "AWAIT_COMMAND":  # move to AWAIT_COMMAND state
                    return 'AWAIT_COMMAND'
                
                elif item[0] == "adjust_gaze":
                    gaze = item[1]
                    self.comm_expr.set_gaze(gaze)
                    self.comm_expr.send_datablock("GAZE_ADJUST")
                
                elif item[0] == "adjust_neck":
                    rotation = item[1]
                    self.comm_expr.set_neck(rotation)
                    self.comm_send_tags.append(self.comm_expr.send_datablock("NECK_ADJUST"))
                    
                    
                elif item[0] == "adjust_neck_zero":
                    self.comm_expr.set_neck(orientation=(0, 0, 0))
                    self.comm_send_tags.append(self.comm_expr.send_datablock("NECK_ADJUST"))
                
                elif item[0] == "face_gaze":
                    if item[2]:
                        self.gaze_adjust_x = item[2][0]/200.0
                        self.gaze_adjust_y = item[2][1]/200.0
                        
                    self.set_gaze(item[1])
                    #self.set_gaze_640(item[1])
                    if show_emo:

                        emo = ["happy", "neutral"]
                        if (time.time() - 30) > self.last_emo_change:
                            self.comm_expr.set_fExpression(emo[random.randint(0,1)])
                            self.comm_expr.send_datablock("EXPRESSION_ADJUST")
                            self.last_emo_change = time.time()
#                        if (time.time() - 5) > self.last_emo_change:
#                            if self.last_emotion == "happy":
#                                self.comm_expr.set_fExpression("neutral")
#                                self.last_emotion = "neutral"
#                                self.comm_expr.send_datablock("EXPRESSION_ADJUST")
#                                self.last_emo_change = time.time()
#                            if self.last_emotion == "neutral":
#                                self.comm_expr.set_fExpression("happy")
#                                self.last_emotion = "happy"
#                                self.comm_expr.send_datablock("EXPRESSION_ADJUST")
#                                self.last_emo_change = time.time()
                    
                    
                elif item[0] == "face_neck":
                    if item[2]:
                        self.neck_adjust_x = item[2][2]/250.0
                        self.neck_adjust_y = item[2][3]/250.0
                    self.set_neck(item[1])
                    #self.set_neck_640(item[1])
                        
                elif item[0] == "motion":  # motion detected
                    (fx,fy) = item[1]
                    x_dist = (((fx/960.0) *-2) +1)*-0.05 # mirror
                    y_dist = (((fy/544.0) *-2) +1)*0.05
    
                    self.comm_expr.set_gaze((x_dist, 1.0, y_dist))
                    self.comm_expr.send_datablock("GAZE_AJUST")
                    
                elif item[0] == "set_expression":
                    expression = item[1]
                    self.comm_expr.set_fExpression(str(expression))
                    self.comm_expr.send_datablock("EXPRESSION_ADJUST")
                    
                elif item[0] == "send_expr_message":
                    self.comm_expr.send_msg(item[1])
                    self.comm_expr.send_datablock("EXPRESSION_MESSAGE")
                    
                    
                    
    def run_demo_behaviour(self):
        """ behaviour to run a responsive demo
        """
        
        print 'STATE: run_demo_behaviour'
        self.from_beh_q.put(('run_demo_behaviour'), None)
        
        item = None
        while not item:
            try:    # query the queue
                item = self.from_gui_q.get()
            except Queue.Empty:
                item = None
        if item == "quit_fsm":  # if receiving the stop command, move to stop state
            return SMFSM.STOPPED
        else:
            self.from_beh_q.put((item), None)
            return item
        
        

    def face_grow_behaviour(self):
        """ behaviour executed when detected face is growing
        """
        
        print 'STATE: face_grow_behaviour'
        self.from_beh_q.put(('face_grow_behaviour'), None)
        
        
    def face_shrink_behaviour(self):
        """ behaviour executed when detected face is shrinking
        """
        
        print 'STATE: face_shrink_behaviour'
        self.from_beh_q.put(('face_shrink_behaviour'), None)
        
        
    def wave_behaviour(self):
        """ behaviour executed when handwave is detected
        """
        
        print 'STATE: wave_behaviour'
        self.from_beh_q.put(('wave_behaviour'), None)
        
        
    def move_limit_behaviour(self):
        """ behaviour executed robot body limits are reached
        """
        
        print 'STATE: move_limit_behaviour'
        self.from_beh_q.put(('move_limit_behaviour'), None)
        
        return 
        
        
    def stopped(self, arg):
        print 'behaviour ended'
        return


################# robot comm ##################################

    def set_gaze(self, target_coors):
        """ set gaze based on given target coordinates
        """
        (fx, fy, fw, fh) = [float(i) for i in target_coors]
        face_dist = ((-88.5 * math.log(fw)) + 538.5)
        fx = fx + (fw/2.0)
        fy = fy + (fh/2.0)
            
        x_dist = self.gaze_adjust_x * (((fx/960.0) *-2) +1)
        y_dist = self.gaze_adjust_y * (((fy/544.0) *-2) +1)

        self.comm_expr.set_gaze((x_dist, face_dist/100.0, y_dist))
        self.comm_expr.send_datablock("GAZE_ADJUST")
        
        
    def set_gaze_640(self, target_coors):
        """ set gaze based on given target coordinates
        """
        (fx, fy, fw, fh) = [float(i) for i in target_coors]
        face_dist = ((-88.5 * math.log(fw)) + 538.5)
        fx = fx + (fw/2.0)
        fy = fy + (fh/2.0)
            
        x_dist = self.gaze_adjust_x * (((fx/640.0) *-2) +1)
        y_dist = self.gaze_adjust_y * (((fy/360.0) *-2) +1)

        self.comm_expr.set_gaze((x_dist, face_dist/100.0, y_dist))
        self.comm_expr.send_datablock("GAZE_ADJUST")
        
        
    def set_neck(self, target_coors):
        """ set neck based on given target coordinates
        """
        
        (fx, fy, fw, fh) = target_coors
        nx = fx+(fw/2.0)
        ny = fy+(fh/2.0)


        if (nx < 400 or nx > 560) or (ny < 232 or ny > 312):    # only move when detected face is a bit off centre
        
            if (self.comm_send_tags == []  or self.check_send_expressions()): #only move when previous move is finished

#                if self.comm_expr.neck_adjust_tag in self.comm_send_tags:
#                    self.comm_send_tags.remove(self.comm_expr.neck_adjust_tag)
                
                x_value = self.neck_adjust_y * ((ny/544) - 0.5)
                z_value = -self.neck_adjust_x * ((nx/960) - 0.5)
                
                self.comm_expr.set_neck((x_value, 0.0, z_value))
                self.comm_send_tags.append(self.comm_expr.send_datablock("NECK_ADJUST"))
                self.last_neck_move = time.time()
                
                
    def set_neck_640(self, target_coors):
        """ set neck based on given target coordinates
        """
        
        (fx, fy, fw, fh) = target_coors
        nx = fx+(fw/2.0)
        ny = fy+(fh/2.0)

        #640,360
        if (nx < 200 or nx > 440) or (ny < 120 or ny > 240):    # only move when detected face is a bit off centre
        
            if (self.comm_send_tags == []  or self.check_send_expressions()): #only move when previous move is finished

#                if self.comm_expr.neck_adjust_tag in self.comm_send_tags:
#                    self.comm_send_tags.remove(self.comm_expr.neck_adjust_tag)
                
                x_value = self.neck_adjust_y * ((ny/360) - 0.5)
                z_value = -self.neck_adjust_x * ((nx/640) - 0.5)
                
                self.comm_expr.set_neck((x_value, 0.0, z_value))
                self.comm_send_tags.append(self.comm_expr.send_datablock("NECK_ADJUST"))
                self.last_neck_move = time.time()
        
        
    def check_send_expressions(self):
        response = False
        print " adjust tags received: ", self.comm_expr.neck_adjust_tags
        print "adjust tags send: ", self.comm_send_tags
        
        if time.time() - 10 > self.last_neck_move:   #clear tags send list if robot has not moved for 5 seconds
            self.comm_send_tags = []
            print "send tags cleared"
        
        tags_to_remove =[]
        
        for i in self.comm_send_tags:
            if i in self.comm_expr.neck_adjust_tags:
                tags_to_remove.append(i)
                response = True
        for i in tags_to_remove:
            self.comm_send_tags.remove(i)
            self.comm_expr.neck_adjust_tags.remove(i)
                
#        for i in self.comm_expr.neck_adjust_tags:
#            if i in self.comm_send_tags:
#                response = True
#                self.comm_send_tags.remove(i)
        return response
        

#    def get_features(self):
#        print "STATE: getting features"
#
#        while True:
#            try:
#                item = self.from_gui_q.get()
#            except Queue.Empty:
#                item = None
#            if item == "quit_fsm":
#                return SMFSM.STOPPED
#            else:
#                self.comm_lighthead.get_snapshot()
#                print self.comm_lighthead.snapshot
#                time.sleep(1)
                
                
      
#    def set_pose_default(self):
#        print 'STATE: set default pose'
#        
#        #self.comm_expr.set_neck( rotation=(0.0, 0.0, -.01))
#        #self.comm_expr.set_neck( orientation=(0.0, 0.0, .3))
#        #self.comm_expr.set_neck( orientation=(0.0, 0.0, 0.0))
#        
#        #self.comm_expr.send_datablock("Test")x
#        
#        return SMFSM.STOPPED



if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG,**LOGFORMATINFO)

    conf.set_name('lightHead')
    from_gui_q = Queue.Queue()
    from_behaviours_q = Queue.Queue()
    bt = Behaviour_thread(from_gui_q, from_behaviours_q)
    bt.start()
        
    vis = vision.Vision(cfg.use_gui, from_gui_q=from_gui_q, from_beh_q=from_behaviours_q)
    vis.start_camera()


    

    
