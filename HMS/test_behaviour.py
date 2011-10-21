
import sys
cogmod_root = '/home/joachim/PhD@Plymouth/Concept_project/workspace/weighted_cs/src/'
concept_dir = '/home/joachim/PhD@Plymouth/Concept_project/workspace/concept-robot/'
sys.path.append(cogmod_root)
sys.path.append(concept_dir)
    
from HMS import expression_player as ep
from utils import conf, handle_exception
from utils.FSMs import SMFSM
from HMS.communication import ExpressionComm

from PyQt4.QtGui import *
from layout import Ui_MainWindow
import graphic


class TestBehaviour_Builder(ep.Behaviour_Builder):
    """
    """
    def start(self):
        print 'test started'
        return 'DETECT'
        
        
    def detect(self):
        app = QApplication(sys.argv)
        mainwindow = graphic.GUI()
        ui = Ui_MainWindow()
        ui.setupUi(mainwindow)
        mainwindow.layout = ui
        mainwindow.set_defaults()
        mainwindow.show()
        sys.exit(app.exec_())
        return SMFSM.STOPPED
        
          
    def stopped(self):
        print 'test stopped'
        return
      
    def __init__(self):
        rules = ((SMFSM.STARTED,self.start), ('DETECT',  self.detect), (SMFSM.STOPPED,self.stopped) )
        machine_def = [ ('test', rules, None) ]
        ep.Behaviour_Builder.__init__(self, machine_def, with_vision=False)


if __name__ == '__main__':
    
    player = TestBehaviour_Builder()
    player.run()
    player.cleanup()
    
    
    