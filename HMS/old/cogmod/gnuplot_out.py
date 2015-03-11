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

# output functions for generating graphs with Gnuplot

import Gnuplot
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import cfg

def output(data, x_label="x_label", y_label="y_label", filename="gnuplot_output", y_range=[0.0, 1.0], comment=None):
    """ data format = [ [data, x_title], [data, x_title]]
    """
    gp = Gnuplot.Gnuplot(persist = 1)
    gp('set style data lines')
    #gp('set key outside horiz bot center')
    gp('set key right bottom')
    gp('set xlabel " %s"' % x_label)
    gp( 'set ylabel " %s"' % y_label)
    if comment:
        gp('set label "%s" at %d, 0.3' % (comment, (cfg.n_cycles - (cfg.n_cycles*0.3))))
    gp('set ytics ' + str(y_range[1]/10.0) )
    gp('set yrange ' + "[" + str(y_range[0]) + ":" + str(y_range[1]) + "]")
    #gp('set y2range [0:100]')
    #gp('set y2tics 0, 10')
    #gp('set ytics nomirror')
    
    xtics = ""
    for i in range(1,11):
        xtics = xtics + "\"" + str(int(i*(cfg.interactions_per_agent/10.0))) + "\" " + str(i*(cfg.n_cycles/10.0)) + ","
    xtics = xtics[:-1]
    xtics = "(" + xtics + ")"
    
    gp('set xtics %s' % xtics)
    
    plots = []
    for i in data:
        x_title = i[1]
        output1 = []
        errorbars = False
        for x, j in enumerate(i[0]):
            if len(j) == 2:                         # if error bar data is present
                output1.append([x, j[0], j[1]])
                errorbars = True 
            else:
                output1.append([x, j[0]])
        plots.append(Gnuplot.PlotItems.Data(output1, with_="lines", smooth="bezier", title=x_title )) # draw the line
        if errorbars:
            gp('set style line 10 lt 1 lc rgb "black" pt 0')    # define linestyle 10 for error bars, no record indicator
            plots.append(Gnuplot.PlotItems.Data(output1, every= str(cfg.n_cycles/10), with_="errorbars linestyle 10"))   # add errorbars
        
        if cfg.set_value:
            gp('set size 1.1,1')
            gp('set rmargin 25')
            x_coor, y_coor = round(cfg.n_cycles + (cfg.n_cycles*0.05), 2), round(output1[len(output1) -1][1], 2)
            gp('set label "value = %s" at %d, %f' % (y_coor, x_coor, y_coor ) )
    
    gp.plot(*plots)
    gp('set terminal png size 1000, 600')
    gp.hardcopy("output/" + filename + '.png', terminal = 'png')
    gp.hardcopy("output/" + filename + '.eps', eps=True, color=True)
    
    
def plot_CS(cs_data):

    fig = plt.figure()
    
    X, Y, Z = [], [], []    
    for i in cs_data:
        X.append(i[0])
        Y.append(i[1])
        try:
            Z.append(i[2])
        except IndexError:
            pass
         
    if Z == []:  #2D plot
        ax = fig.add_subplot(111)
        ax.scatter(X, Y, c='r', marker='o')
        ax.set_xlabel('red-green')
        ax.set_ylabel('blue-yellow')
        
    else:   #3D plot
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter(X, Y, Z, c='r', marker='o')
        ax.set_xlabel('S cones')
        ax.set_ylabel('M cones')
        ax.set_zlabel('L cones')
    
    plt.show()
    
    
def plot_bar_charts(data, x_label="x_label", y_label="y_label", filename="bar_chart", y_range=[0.0, 1.0]):
    """ data format = [ [mean, sd, group_label], [data, sd, group_label]]
    """
    means, sd, groups = [], [], []
    for i in data:
        means.append(i[0])
        sd.append(i[1])
        groups.append(i[2])
    ind = np.arange(len(means))  # the x locations for the groups
    width = 0.35       # the width of the bars
    plt.subplot(111)
    rects1 = plt.bar(ind, means, width, color='r', yerr=sd, error_kw=dict(elinewidth=1, ecolor='black'))
    plt.ylabel(y_label)
    plt.xticks(ind+width, groups)
    plt.show()
        
        
#N = 5
#menMeans = (20, 35, 30, 35, 27)
#menStd =   (2, 3, 4, 1, 2)
#
#ind = np.arange(N)  # the x locations for the groups
#width = 0.35       # the width of the bars
#
#
#plt.subplot(111)
#rects1 = plt.bar(ind, menMeans, width, color='r', yerr=menStd, error_kw=dict(elinewidth=1, ecolor='black'))
#
#womenMeans = (25, 32, 34, 20, 25)
#womenStd =   (3, 5, 2, 3, 3)
#rects2 = plt.bar(ind+width, womenMeans, width,
#                    color='y',
#                    yerr=womenStd,
#                    error_kw=dict(elinewidth=1, ecolor='black'))
#
## add some
#plt.ylabel('Scores')
#plt.title('Scores by group and gender')
#plt.xticks(ind+width, ('G1', 'G2', 'G3', 'G4', 'G5') )
#
#plt.legend( (rects1[0], rects2[0]), ('Men', 'Women') )
#
#def autolabel(rects):
#    # attach some text labels
#    for rect in rects:
#        height = rect.get_height()
#        plt.text(rect.get_x()+rect.get_width()/2., 1.05*height, '%d'%int(height),
#                ha='center', va='bottom')
#
##autolabel(rects1)
##autolabel(rects2)
#
#plt.show()