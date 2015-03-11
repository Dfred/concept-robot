#!/usr/bin/python

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

from __future__ import division
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import gnuplot_out as go
from layout import Ui_MainWindow
import lg, cfg, graphic, data, agent, auks, inout
import simple_learn as sl
import globals as gl

gl.version = "0.2.556"


def run():

    gl.test_title = "correct=" + str(cfg.correct)
    out1 = sl.run_simple_learn()

    go.output([out1[0]], "# interactions", "% correct", "agent2_test_succes")

#run()
    

if __name__ == "__main__":
    #run()
    app = QApplication(sys.argv)
    gl.mainwindow = graphic.GUI(gl.agent1)
    ui = Ui_MainWindow()
    ui.setupUi(gl.mainwindow)
    gl.mainwindow.layout = ui
    gl.mainwindow.show()
    sys.exit(app.exec_())
