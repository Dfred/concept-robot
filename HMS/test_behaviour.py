
import sys, threading, math, Queue, time
    
from HMS import expression_player as ep
from HMS.communication import ThreadedLightHeadComm
from utils import conf, handle_exception, LOGFORMATINFO
from utils.FSMs import SMFSM

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from HMS import cogmod
from cogmod.layout import Ui_MainWindow
from cogmod import graphic


use_gui = 1

########### Tuning params #################
neck_adj_fact_x = 1.0
gaze_adj_fact_x = 1.0
gaze_adj_fact_y = 1.0




class Behaviour_thread(threading.Thread):
    """ class which creates a dedicated thread for a Follow_Behaviour
    """
    
    def __init__(self, comm_queue):
        threading.Thread.__init__(self)
        self.comm_queue = comm_queue
        self.player = Follow_Behaviour(self.comm_queue)
    
    def run(self):
        self.player.run()
        self.player.cleanup()



class Follow_Behaviour(ep.Behaviour_Builder):
    """ FSM which tracks faces and adjust gaze accordingly
    """
    
    def __init__(self, comm_queue):
        
        self.comm_queue = comm_queue
        rules = ((SMFSM.STARTED,self.started), ('DETECT', self.set_gaze_to_target), (SMFSM.STOPPED,self.stopped) )
        machine_def = [ ('test', rules, None) ]
        ep.Behaviour_Builder.__init__(self, machine_def, with_vision=False)
        self.connected = False
        #self.comm_lighthead = ThreadedLightHeadComm(conf.lightHead_server, connection_succeded_function=self.on_connect)
        
        # tuning
        self.gaze_adjust_x = 0.5
        self.gaze_adjust_y = 0.5
        self.neck_adjust_x = 0.5
        self.neck_adjust_y = 0.5
        
        
    def on_connect(self):
        self.connected = True
    
    
    def started(self):
        print 'test started'
        return 'DETECT'
    
    
    def set_pose_default(self):
        print 'test started'
        
        #self.comm_expr.set_neck( rotation=(0.0, 0.0, -.01))
        #self.comm_expr.set_neck( orientation=(0.0, 0.0, .3))
        #self.comm_expr.set_neck( orientation=(0.0, 0.0, 0.0))
        
        #self.comm_expr.send_datablock("Test")
        
        return SMFSM.STOPPED
    
    
    def get_features(self):
        print "getting features"

        while True:
            try:
                item = self.comm_queue.get(False)
            except Queue.Empty:
                item = None
            if item == "quit_fsm":
                return SMFSM.STOPPED
            else:
                self.comm_lighthead.get_snapshot()
                print self.comm_lighthead.snapshot
                time.sleep(1)
                
                
    def set_gaze_neck_to_target(self):
        """ sets the gaze to target pulled from the vision queue
        """
        print "neck follows target"
        
        while True:
            try:    # query the queue
                item = self.comm_queue.get(False)
            except Queue.Empty:
                item = None
                
            if item:
                if item == "quit_fsm":  # if receiving the stop command, move state
                    return SMFSM.STOPPED
                
                elif item[0] == "face":  # face detected
                    (fx, fy, fw, fh) = item[1]
                    nx = fx+(fw/2.0)
                    ny = fy+(fh/2.0)
                    
                    # adjust gaze
                    face_dist = ((-88.5 * math.log(fw)) + 538.5)
                    fx = fx + (fw/2.0)
                    fy = fy + (fh/2.0)
                    x_dist = (((fx/960.0) *-2) +1)*-0.05 # mirror
                    y_dist = (((fy/544.0) *-2) +1)*0.05
    
                    self.comm_expr.set_gaze((gaze_adj_fact_x * x_dist, face_dist/100.0, gaze_adj_fact_y * y_dist))
                    self.comm_expr.send_datablock("GAZE_AJUST")
                    
                    # adjust neck
                    if nx < 320:
                        self.comm_expr.set_neck( (0.0, 0.0, neck_adj_fact_x * (-.5 + (nx/640.0))) )
                        self.comm_expr.send_datablock("NECK_AJUST")
                    if nx < 320:
                        self.comm_expr.set_neck( (0.0, 0.0, neck_adj_fact_x * ( (nx-640)/640.0) ) )
                        self.comm_expr.send_datablock("NECK_AJUST")
                    

        
        
    def set_gaze_to_target(self):
        """ sets the gaze to target pulled from the vision queue
        """
        
        print "detecting"
        
        while True:
            try:    # query the queue
                item = self.comm_queue.get(False)
            except Queue.Empty:
                item = None
                
            if item:
                if item == "quit_fsm":  # if receiving the stop command, move state
                    return SMFSM.STOPPED
                
                elif item[0] == "face_gaze":
                    (fx, fy, fw, fh) = item[1]
                    print "fx, fy: ", fx, fy
                    face_dist = ((-88.5 * math.log(fw)) + 538.5)
                    fx = fx + (fw/2.0)
                    fy = fy + (fh/2.0)
                    if item[2]:
                        self.gaze_adjust_x = item[2][0]/100.0
                        self.gaze_adjust_y = item[2][1]/100.0
                        
                    x_dist = (((fx/960.0) *-2) +1)*-self.gaze_adjust_x # mirror
                    y_dist = (((fy/544.0) *-2) +1)*self.gaze_adjust_y
    
                    self.comm_expr.set_gaze((x_dist, face_dist/100.0, y_dist))
                    self.comm_expr.send_datablock("GAZE_AJUST")
                    
                    
                elif item[0] == "face_neck":
                    (fx, fy, fw, fh) = item[1]
                    nx = fx+(fw/2.0)
                    ny = fy+(fh/2.0)
                    if item[2]:
                        self.neck_adjust_x = item[2][2]/100.0
                        self.neck_adjust_y = item[2][3]/100.0
                        
                    print self.neck_adjust_x, self.neck_adjust_y
                    
#                    if nx < 320:
#                        self.comm_expr.set_neck( (0.0, 0.0, self.neck_adjust_x * (-.5 + (nx/640.0))) )
#                        self.comm_expr.send_datablock("NECK_AJUST")
#                    if nx < 320:
#                        self.comm_expr.set_neck( (0.0, 0.0, self.neck_adjust_x * ( (nx-640)/640.0) ) )
#                        self.comm_expr.send_datablock("NECK_AJUST")
                        
                    
                elif item[0] == "motion":  # motion detected
                    (fx,fy) = item[1]
                    x_dist = (((fx/960.0) *-2) +1)*-0.05 # mirror
                    y_dist = (((fy/544.0) *-2) +1)*0.05
    
                    self.comm_expr.set_gaze((x_dist, 1.0, y_dist))
                    self.comm_expr.send_datablock("GAZE_AJUST")

        
    def stopped(self, arg):
        print 'behaviour ended'
        return
      


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG,**LOGFORMATINFO)
    
    comm_queue = Queue.Queue()
    bt = Behaviour_thread(comm_queue)
    bt.start()
    
    if use_gui:
        app = QApplication(sys.argv)
        mainwindow = graphic.GUI(comm_queue)
        ui = Ui_MainWindow()
        ui.setupUi(mainwindow)
        mainwindow.layout = ui
        mainwindow.set_defaults()
        mainwindow.show()
        app.exec_()
        comm_queue.join()
    
    