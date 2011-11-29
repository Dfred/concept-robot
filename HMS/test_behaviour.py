
import sys, threading, math, Queue, time, random
    
from HMS import expression_player as ep
from HMS.communication import ThreadedExpressionComm, ThreadedLightHeadComm
from utils import conf, handle_exception, LOGFORMATINFO
from utils.FSMs import SMFSM

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from HMS import cogmod
from cogmod.layout import Ui_MainWindow
from cogmod import graphic


use_gui = 1
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


class Base_behaviour(ep.Behaviour_Builder):
    """ Base FSM which listens for state changes from gui and triggers behaviours accordingly
    """
    
    def __init__(self, from_gui_q, from_beh_q):
        self.from_gui_q = from_gui_q
        self.from_beh_q = from_beh_q
        BASE_PLAYER_DEF = ((SMFSM.STARTED,self.started), ('AWAIT_COMMAND', self.wait_for_command),\
                           ('FOLLOW_TARGET', self.set_gaze_neck_to_target), ('RUN_DEMO', self.run_demo_behaviour), \
                           ('FACE_GROW', self.face_grow_behaviour),('FACE_SHRINK', self.face_shrink_behaviour), \
                           ('WAVE', self.wave_behaviour), ('MOVE_LIMIT', self.move_limit_behaviour),
                           (SMFSM.STOPPED,self.stopped) )
        machine_def = [ ('base_player', BASE_PLAYER_DEF, None)]
        ep.Behaviour_Builder.__init__(self, machine_def, with_vision=False)
        
        self.connected = False
        self.comm_send_tags = []
        # for snapshots, not used atm
        #self.comm_lighthead = lightHeadComm(conf.lightHead_server, connection_succeded_function=self.on_connect)
        
        # tuning
        self.gaze_adjust_x = 0.5
        self.gaze_adjust_y = 0.5
        self.neck_adjust_x = 0.5
        self.neck_adjust_y = 0.5
        
        self.last_emo_change = time.time()
        self.last_emotion = "neutral"
        
    def on_connect(self):
        self.connected = True
        
        
################# Behaviours ##################################
        
        
    def started(self):
        print 'STATE: test started'
        self.from_beh_q.put(('STATE: test started'), None)
        return 'AWAIT_COMMAND'
    
    
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
                    self.comm_expr.send_datablock("NECK_ADJUST")
                
                elif item[0] == "face_gaze":
                    if item[2]:
                        self.gaze_adjust_x = item[2][0]/200.0
                        self.gaze_adjust_y = item[2][1]/200.0
                    self.set_gaze(item[1])
                    if show_emo:

                        emo = ["happy", "neutral"]
                        if (time.time() - 5) > self.last_emo_change:
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
                        
                elif item[0] == "motion":  # motion detected
                    (fx,fy) = item[1]
                    x_dist = (((fx/960.0) *-2) +1)*-0.05 # mirror
                    y_dist = (((fy/544.0) *-2) +1)*0.05
    
                    self.comm_expr.set_gaze((x_dist, 1.0, y_dist))
                    self.comm_expr.send_datablock("GAZE_AJUST")
                    
                    
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
        
        
    def set_neck(self, target_coors):
        """ set neck based on given target coordinates
        """
        (fx, fy, fw, fh) = target_coors
        nx = fx+(fw/2.0)
        ny = fy+(fh/2.0)

        if (nx < 400 or nx > 560) or (ny < 232 or ny > 312):    # only move when detected face is a bit off centre
        
            if (self.comm_send_tags == []  or self.comm_expr.neck_adjust_tag in self.comm_send_tags): #only move when previous move is finished
                if self.comm_expr.neck_adjust_tag in self.comm_send_tags:
                    self.comm_send_tags.remove(self.comm_expr.neck_adjust_tag)
                
                x_value = self.neck_adjust_y * ((ny/544) - 0.5)
                z_value = -self.neck_adjust_x * ((nx/960) - 0.5)
                
                self.comm_expr.set_neck((x_value, 0.0, z_value))
                self.comm_send_tags.append(self.comm_expr.send_datablock("NECK_ADJUST"))
        

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
    
    from_gui_queue = Queue.Queue()
    from_behaviours_queue = Queue.Queue()
    bt = Behaviour_thread(from_gui_queue, from_behaviours_queue)
    bt.start()
    
    if use_gui:
        app = QApplication(sys.argv)
        mainwindow = graphic.GUI(from_gui_queue, from_behaviours_queue)
        ui = Ui_MainWindow()
        ui.setupUi(mainwindow)
        mainwindow.layout = ui
        mainwindow.set_defaults()
        mainwindow.show()
        app.exec_()
        from_gui_queue.join()
        from_behaviours_queue.join()
    
    