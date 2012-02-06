###################################################################
# cogmod2 version 0.31                                            #
# main.py                                                         #
#                                                                 #
# The CONCEPT project. University of Plymouth, United Kingdom     #
# More information at http://www.tech.plym.ac.uk/SoCCE/CONCEPT/   #
#                                                                 #
# Copyright (C) 2012 Joachim de Greeff (www.joachimdegreeff.eu)   #
#                                                                 #
# This program is free software: you can redistribute it and/or   #
# modify it under the terms of the GNU General Public License as  # 
# published by the Free Software Foundation, either version 3 of  #
# the License, or (at your option) any later version.             #
#                                                                 #
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    # 
# GNU General Public License for more details.                    #
###################################################################


import cfg, lg
import globals as gl
import gnuplot_out as go


def run():
    out, out2 = [], []
    
#    gl.gnuplot_title = "baseline"
#    lg_outcome = lg.run_language_game(cfg.n_cycles, cfg.context_size, cfg.n_agents)
#    out.append(lg_outcome[0])
#    out2.append(lg_outcome[0][0][-1]+[lg_outcome[0][-1]])
    
#    gl.gnuplot_title = "random"
#    cfg.cone_proportions = "random"
#    lg_outcome = lg.run_language_game(cfg.n_cycles, cfg.context_size, cfg.n_agents)
#    out.append(lg_outcome[0])
#    out2.append(lg_outcome[0][0][-1]+[lg_outcome[0][-1]])
    
#    gl.gnuplot_title = "random2"
#    cfg.cone_proportions = "random2"
#    lg_outcome = lg.run_language_game(cfg.n_cycles, cfg.context_size, cfg.n_agents)
#    out.append(lg_outcome[0])
#    out2.append(lg_outcome[0][0][-1]+[lg_outcome[0][-1]])
    
    #go.output(out, x_label="interactions per agent", y_label="% success", filename="_comm_success")
    
    #go.plot_bar_charts(out2, y_label="% success", filename="test")
    #go.output([lg_outcome[1]], "# interactions", "n _words", "_word_success", y_range=[0, 100])
    
    print lg.run_discrimination_game(cfg.dg_base_n, cfg.context_size)

    

if __name__ == "__main__":
    run()
