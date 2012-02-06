
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import Queue, time, datetime
import globals as gl
import cfg


class GUI(QMainWindow):
    """ main window
    """
    def __init__(self, parent=None):
        QMainWindow.__init__(self)
        
        self.parent = parent
        self.layout = None
        self.language_game_running = False
        self.interaction_running = False
        self.fps = 0
        self.last_time = 0.0
        self.get_colour = False
        self.get_target = False
        self.mouse_x = 0
        self.mouse_y = 0

        self.lg_queue = Queue.Queue()
        self.lg_thread = LanguageGame(self.lg_queue, self)

        self.timer = QTimer()
        QObject.connect(self.timer, SIGNAL("timeout()"), self.update_lg)
        self.connect(self.lg_thread, SIGNAL("update(PyQt_PyObject)"), self.update_lg)
        self.connect(self.lg_thread, SIGNAL("stop(PyQt_PyObject)"), self.stop_lg)
        self.counter = 0

        self.statusBar().showMessage("Configuration set to default")
        self.painter = QPainter()
        gl.draw_attention = False

        self.current_agent = None           # agent that is currently active
        self.current_sensory_input = None   # current sensory input
        self.current_object_name = None     # current object name as given by agent based on sensory input
        # for movement2
        
        
    def set_layout(self):
        self.layout.lineEdit.setText(str(cfg.n_agents))
        self.layout.lineEdit_2.setText(str(cfg.n_cycles))
        self.layout.lineEdit_3.setText(str(cfg.replicas))
        self.layout.lineEdit_4.setText(str(cfg.context_size))
        self.set_parameters_default()
        
        
    def set_parameters_default(self):   # need to match with gui items as defined in layout
        self.layout.checkBox.setChecked(cfg.detect_faces)
        self.layout.checkBox_2.setChecked(cfg.detect_edge)
        self.layout.checkBox_70.setChecked(cfg.gaze_follows_target)
        self.layout.checkBox_71.setChecked(cfg.neck_follows_target)
        
        
    def modify_parameters(self):
        source = self.sender()
        if source.text() == "Detect faces":
            cfg.detect_faces = source.isChecked()
        if source.text() == "histogram filter":
            cfg.histogram_filter = source.isChecked()
        if source.text() == "Gaze follows target":
            cfg.gaze_follows_target = source.isChecked()
        if source.text() == "Neck follows target":
            cfg.neck_follows_target = source.isChecked()
        if source.text() == "Edge Detection":
            cfg.detect_edge = source.isChecked()
            
            
    def test_function(self):
        print "test"
        
        
    def about(self):
        now = datetime.datetime.now()
        about_text = "CONVIZ (CONcept VIZualisation tool) allows for the visualisation\
                      of agents conceptual knowledge spaces. It is part of the CONCEPT\
                      project ran at the university of Plymouth, UK.<br><br>\
                      Author: Joachim de Greeff <br>\
                      Date: " + now.strftime("%d-%m-%Y") + "<br><br>\
                      More information at http://www.tech.plym.ac.uk/SoCCE/CONCEPT"
        QMessageBox.about(self, self.tr("About CONVIZ"), self.tr(about_text))
        
        
    def aboutQt(self):
        QMessageBox.aboutQt(self, self.tr(""))
        
        
    def close(self):
        if gl.from_gui_q:
            gl.from_gui_q.put("quit_fsm", False)
        quit()
        
        
    def start_main_loop(self):
        self.parent.start_camera()
        
################### Interaction ###################
        
    def start_interaction(self):
        if self.interaction_running == False:
            self.start_camera()
            self.get_colour = True
            self.circle_detection = True
            gl.draw_attention = True
        else:
            self.start_camera()
            self.circle_detection = False
            self.get_colour = False 
            gl.draw_attention = False
            
            
    def set_get_colour(self):
        if not self.get_colour:
            self.get_colour = True
            gl.draw_attention = True
        else:
            self.get_colour = False
            gl.draw_attention = False
            
            
    def set_get_target(self):
        if not gl.get_target:
            gl.get_target = True
        else:
            gl.get_target = False
            
            
    def set_gaze_tune(self):
        gl.gaze_tune_x = self.layout.horizontalSlider_7.value()
        gl.gaze_tune_y = self.layout.horizontalSlider_8.value()
        gl.neck_tune_x = self.layout.horizontalSlider_28.value()
        gl.neck_tune_y = self.layout.horizontalSlider_29.value()
        
        
        
################### Behaviour control ###################

    def set_robot_behaviour(self):
        behaviour = self.layout.horizontalSlider_11.value()
        if behaviour == 0:
            gl.from_gui_q.put(("AWAIT_COMMAND"), None)
        elif behaviour == 1:
            gl.from_gui_q.put(("FOLLOW_TARGET"), None)
        elif behaviour == 2:
            gl.from_gui_q.put(("RUN_DEMO"), None)
        elif behaviour == 3:
            gl.from_gui_q.put(("RESPONSE_BEH"), None)
        self.update_behaviour_status()
        
        
    def update_behaviour_status(self):
        if gl.from_beh_q:
            try:    # query the queue
                item = gl.from_beh_q.get(None)
            except Queue.Empty:
                item = None
            if item:
                self.layout.label_32.setText(item)
        

        
    def adjust_robot_gaze(self):
        source = self.sender()
        gaze_command = None
        if source.text() == 'X':
            gaze_command = (0.01, 0.0, 0.0)
        if source.text() == '-X':
            gaze_command = (-0.01, 0.0, 0.0)
        if source.text() == 'Y':
            gaze_command = (0.0, 0.01, 0.0)
        if source.text() == '-Y':
            gaze_command = (0.0, -0.01, 0.0)
        if source.text() == 'Z':
            gaze_command = (0.0, 0.0, 0.01)
        if source.text() == '-Z':
            gaze_command = (0.0, 0.0, -0.01)
        if gl.from_gui_q:
            gl.from_gui_q.put(("adjust_gaze", gaze_command, None))
            
    def adjust_robot_neck(self):
        source = self.sender()
        neck_command = None
        if source.text() == 'X':
            neck_command = (0.01, 0.0, 0.0)
        if source.text() == '-X':
            neck_command = (-0.01, 0.0, 0.0)
        if source.text() == 'Y':
            neck_command = (0.0, 0.01, 0.0)
        if source.text() == '-Y':
            neck_command = (0.0, -0.01, 0.0)
        if source.text() == 'Z':
            neck_command = (0.0, 0.0, 0.01)
        if source.text() == '-Z':
            neck_command = (0.0, 0.0, -0.01)
        if gl.from_gui_q:
            gl.from_gui_q.put(("adjust_neck", neck_command, None))
        
    def adjust_robot_position(self):
        source = self.sender()
        pass
        
################### Language Games ###################
        
    def language_game(self):
        """displays info about the current agents knowledge base
        """
        if self.language_game_running == False:
            self.language_game_running = True
            self.layout.pushButton.setText("Stop")
            self.lg_thread.stop = False
            self.lg_thread.start()
            self.timer.start(100)
            self.statusBar().showMessage("Running " + self.layout.comboBox_2.currentText())
            
        else:
            self.lg_thread.stop = True
            self.language_game_running = False
            self.layout.pushButton.setText("Run")
            self.layout.label_12.data = []  # reset data for graph drawing
            
            
    def update_lg(self):#update_lg(self, gg_succcess):
        #self.layout.label_12.data.append(gg_succcess)
        try:
            self.layout.label_12.data = self.lg_queue.get_nowait()
        except Queue.Empty:
            pass
        self.layout.label_12.repaint()
        
        
    def stop_lg(self, gg_success):
        self.lg_thread.stop = True
        self.language_game_running = False
        self.layout.pushButton.setText("Run")
        self.layout.label_12.data = []  # reset data for graph drawing
        self.statusBar().showMessage(self.layout.comboBox_2.currentText() + " final result: " + str(gg_success))
        
        
    def load_agent(self):
        """loads a pretrained agent
        """
        fname = QFileDialog.getOpenFileName(self, 'Open file')
        if fname:
            ag = agent.Agent("test")
            ag.load_xml(fname)
            self.layout.label_17.setText("Agent '" + str(ag.agent_name) + "' loaded" \
                                        "\n concept size: " + str(len(ag.cs.concepts)))
            self.current_agent = ag
    
    
            
    ################### Visual detection functions ###################
            
    def get_fps(self):
        self.current_time = time.time()
        self.fps += 1
        if (self.current_time - self.last_time) > 1.0:
            fps_return = self.fps
            self.fps = 0
            self.last_time = self.current_time
            return fps_return
        else:
            return 0
    

    

################### Language Games ###################

class LanguageGame(QThread):
    def __init__(self, queue, parent = None):
        QThread.__init__(self, parent)
        self.queue = queue
        self.exiting = False
        self.stop = False
        self.parent = parent

    def __del__(self):
        self.exiting = True
        self.wait()

    def run(self):
        if self.parent.layout.comboBox_2.currentText() == "Language Game":
            out1 = lg.run_language_game(cfg.n_cycles, cfg.context_size, cfg.n_agents, self)
        if self.parent.layout.comboBox_2.currentText() == "Guessing Game":
            out1 = lg.run_guessing_game(cfg.n_cycles, cfg.context_size, self)
        if self.parent.layout.comboBox_2.currentText() == "Discrimination Game":
            out1 = lg.run_discrimination_game(self, cfg.n_cycles, cfg.context_size)

