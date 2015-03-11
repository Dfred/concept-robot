################################################################################
# The CONCEPT project. University of Plymouth, United Kingdom.                 
# More information at http://www.tech.plym.ac.uk/SoCCE/CONCEPT/                
#                                                                              
# Copyright (C) 2010 Joachim de Greeff (www.joachimdegreeff.eu)                
#                                                                              
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later 
# version.
#
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of  
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    
# GNU General Public License for more details.                    
################################################################################

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import globals as gl
import cfg
import random


class selection_widget(QLabel):
    """ widget to display a attention cube on top of a video stream
    """
    def __init__(self, parent):
        QLabel.__init__(self, parent)
        self.parent = parent
    
    def paintEvent(self, event):
        
        if gl.draw_attention:
            paint = QPainter()
            paint.begin(self)
            
            paint.setBrush(QColor(255,0,0,100))
            paint.drawRect(gl.attention_point[0]-15, gl.attention_point[1]-15, 30, 30)
    
            paint.end()
        
        
    def mousePressEvent(self, event):
        self.mouse_x = event.x()
        self.mouse_y = event.y()
        gl.attention_point[0] = self.mouse_x
        gl.attention_point[1] = self.mouse_y
        
        if gl.get_target:
            if gl.from_gui_q:
                gl.from_gui_q.put(("face_gaze", (gl.attention_point[0], gl.attention_point[1], 50, 50), (gl.gaze_tune_x, gl.gaze_tune_y,  gl.neck_tune_x, gl.neck_tune_y)), False)
        self.repaint()
        
        
        
class lg_view_widget(QLabel):
    """ widget to display progress of language games
    """
    def __init__(self, parent):
        QLabel.__init__(self, parent)
        self.lenght = 531/(cfg.n_cycles*1.0)#531/(cfg.n_cycles/100.0)
        self.data = []
    
    def paintEvent(self, event):
        paint = QPainter()
        paint.begin(self)
        
#        paint.setBrush(QColor(255,0,0,100))
#        paint.drawRect(random.randint(300,350), random.randint(200,250), 30, 30)
        
        paint.setBrush(QColor(255,0,0,255))
        prev_x = 0
        prev_y = self.height()

        for i in self.data:
            y_pos2 = self.height() - (i*self.height())
            paint.drawLine(prev_x, prev_y, prev_x + self.lenght, y_pos2)
            prev_x += self.lenght
            prev_y = y_pos2

        paint.end()
        

