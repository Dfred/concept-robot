
import sys, threading, math, Queue, time
    
from HMS import expression_player as ep
from HMS.communication import LightHeadComm
from utils import conf, handle_exception, LOGFORMATINFO
from utils.FSMs import SMFSM

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from HMS import cogmod
from cogmod.layout import Ui_MainWindow
from cogmod import graphic


class Behaviour_thread(threading.Thread):
    """ class which creates a dedicated thread for a Follow_Behaviour
    """
    
    def __init__(self, comm_queue):
        threading.Thread.__init__(self)
        self.player = Follow_Behaviour(comm_queue)
    
    def run(self):
        self.player.run()
        print "check"
        self.player.cleanup()        



class Follow_Behaviour(ep.Behaviour_Builder):
    """ FSM which tracks faces and adjust gaze accordingly
    """
    
    def __init__(self, comm_queue):
        
        self.comm_queue = comm_queue
        rules = ((SMFSM.STARTED,self.started), ('DETECT', self.set_gaze_to_target), (SMFSM.STOPPED,self.stopped) )
        machine_def = [ ('test', rules, None) ]
        ep.Behaviour_Builder.__init__(self, machine_def, with_vision=False)
        self.comm_lighthead = LightHeadComm(conf.lightHead_server)
    

    def started(self):
        print 'test started'
        return 'DETECT'
    
    
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
    
        
    def set_gaze_to_target(self):
        """ sets the gaze to target pulled from the vision queue
        """
        
        print "detecting"
        #self.comm_expr.set_fExpression("neutral", 1.0)
        #self.comm_expr.set_gaze((-0.1, 0.6, 0.0))
        #self.comm_expr.set_datablock("happy:1.0", 1.0, "", (0.0, 0.5, 0.0), (0.1, 0.0, 0.0), (0.0, 0.0, 0.0), "")
        #self.comm_expr.send_datablock("Test")
        #return SMFSM.STOPPED
        
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
                    face_dist = ((-88.5 * math.log(fw)) + 538.5)
                    fx = fx + (fw/2.0)
                    fy = fy + (fh/2.0)
                    x_dist = (((fx/960.0) *-2) +1)*-0.05 # mirror
                    y_dist = (((fy/544.0) *-2) +1)*0.05
    
                    self.comm_expr.set_gaze((x_dist, face_dist/100.0, y_dist))
                    self.comm_expr.send_datablock("GAZE_AJUST")
                    
                elif item[0] == "motion":  # motion detected
                    (fx,fy) = item[1]
                    x_dist = (((fx/960.0) *-2) +1)*-0.05 # mirror
                    y_dist = (((fy/544.0) *-2) +1)*0.05
    
                    self.comm_expr.set_gaze((x_dist, 1.0, y_dist))
                    self.comm_expr.send_datablock("GAZE_AJUST")

        
    def stopped(self, arg):
        print 'test stopped'
        return
      


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG,**LOGFORMATINFO)
    
    comm_queue = Queue.Queue()
    bt = Behaviour_thread(comm_queue)
    bt.start()
    
    app = QApplication(sys.argv)
    mainwindow = graphic.GUI(comm_queue)
    ui = Ui_MainWindow()
    ui.setupUi(mainwindow)
    mainwindow.layout = ui
    mainwindow.set_defaults()
    mainwindow.show()
    sys.exit(app.exec_())
    
    
    