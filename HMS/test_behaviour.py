
import sys
import Queue
import threading
from HMS import cogmod
    
from HMS import expression_player as ep
from utils import conf, handle_exception, LOGFORMATINFO
from utils.FSMs import SMFSM
from HMS.communication import ExpressionComm

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from cogmod.layout import Ui_MainWindow
from cogmod import graphic


class Behaviour_thread(threading.Thread):
    
    def __init__(self, comm_queue):
        threading.Thread.__init__(self)
        self.player = FollowBehaviour_Builder(comm_queue)
    
    def run(self):
        self.player.run()
        
    def end(self):
        self.player.cleanup()



class FollowBehaviour_Builder(ep.Behaviour_Builder):
    """
    """
    
    def __init__(self, comm_queue):
        
        self.comm_queue = comm_queue
        rules = ((SMFSM.STARTED,self.started), ('DETECT',  self.detect), (SMFSM.STOPPED,self.stopped) )
        machine_def = [ ('test', rules, None) ]
        ep.Behaviour_Builder.__init__(self, machine_def, with_vision=False)
    

    def started(self):
        print 'test started'
        return 'DETECT'
        
        
    def detect(self):
        print "detecting"
        
        self.comm_expr.set_gaze((0.1, 0.5, 0.0))
        self.comm_expr.send_datablock("Test")
                
        while True:
            
            try:
                item = self.comm_queue.get(False)
            except Queue.Empty:
                item = None
                
            if item == "quit_fsm":
                return SMFSM.STOPPED
            elif item:
                print item
                
        
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
    
    
    