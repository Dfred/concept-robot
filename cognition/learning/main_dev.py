#!/usr/bin/python
# cogmod2_0.2.556
# **************
# CONCEPT project
# University of Plymouth
# Joachim de Greeff
# More information at http://www.tech.plym.ac.uk/SoCCE/CONCEPT/
# main.py

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
