
import sys
from HMS import cogmod
    
from HMS import expression_player as ep
from utils import conf, handle_exception, LOGFORMATINFO
from utils.FSMs import SMFSM
from HMS.communication import ExpressionComm


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from cogmod.layout import Ui_MainWindow
from cogmod import cfg, agent, lg, graphic



class TestBehaviour_Builder(ep.Behaviour_Builder):
    """
    """
    def start(self):
        print 'test started'
        return 'DETECT'
        
        
    def detect(self):
#        app = QApplication(sys.argv)
#        mainwindow = graphic.GUI()
#        ui = Ui_MainWindow()
#        ui.setupUi(mainwindow)
#        mainwindow.layout = ui
#        mainwindow.set_defaults()
#        mainwindow.show()
#        sys.exit(app.exec_())

        print self.comm_expr.status

        return SMFSM.STOPPED
        
          
    def stopped(self, arg):
        print 'test stopped'
        return
      
    def __init__(self):
        rules = ((SMFSM.STARTED,self.start), ('DETECT',  self.detect), (SMFSM.STOPPED,self.stopped) )
        machine_def = [ ('test', rules, None) ]
        ep.Behaviour_Builder.__init__(self, machine_def, with_vision=False)


if __name__ == '__main__':
    #import logging
    #logging.basicConfig(level=logging.DEBUG,**LOGFORMATINFO)
    player = TestBehaviour_Builder()
    player.run()
    player.cleanup()
    
    
    