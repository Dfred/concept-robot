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

# this file implements various colour perception models
import math
import inout, cfg
import sys
from PyQt4 import QtGui, QtCore

def response_S_cone(wavelength):
    """ perception function which calculates the response of S-cones
    """
    a1 = 0.9889
    b1 = 447.2
    c1 = 33.4
    return a1*math.exp(-((wavelength-b1)/c1)**2)


def response_M_cone(wavelength):
    """ perception function which calculates the response of M-cones
    """
    a1 = 0.9989
    b1 = 545.2
    c1 = 52.69
    return a1*math.exp(-((wavelength-b1)/c1)**2)


def response_L_cone(wavelength):
    """ perception function which calculates the response of L-cones
    """
    a1 = 1
    b1 = 567.9
    c1 = 64.78
    return a1*math.exp(-((wavelength-b1)/c1)**2)
    
    
def response_to_wavelength(w, cone_proportions):
    pr_s, pr_m, pr_l = cone_proportions
    return ["cone", [pr_s * response_S_cone(w), pr_m * response_M_cone(w), pr_l * response_L_cone(w)]]


def cone_opponency(w, cone_proportions):
    pr_s, pr_m, pr_l = cone_proportions
    rs = pr_s * response_S_cone(w)
    rm = pr_m * response_M_cone(w)
    rl = pr_l * response_L_cone(w)
    red_green = rl - rm
    blue_yellow = (rs - ((0.5*rl) + (0.5*rm)))
    return ["cone_opp", [red_green, blue_yellow]]


def save_values_to_file(w_range=[400, 700], increment=20):
    output = []
    for i in range(0, w_range[1]-w_range[0], increment):
        w_value = w_range[0]+i
        output.append([w_value, response_S_cone(w_value), response_M_cone(w_value), response_L_cone(w_value)])
    inout.write_out("response_to_wavelength", output)
    
    
def save_values_to_file_opponency(w_range=[400, 700], increment=20):
    output = []
    for i in range(0, w_range[1]-w_range[0], increment):
        w_value = w_range[0]+i
        rs, rm, rl = response_S_cone(w_value), response_M_cone(w_value), response_L_cone(w_value)
        red_green = rl - rm
        blue_yellow = (rs - ((0.5*rl) + (0.5*rm)))
        output.append([w_value, red_green, blue_yellow])
    inout.write_out("response_to_wavelength", output)
    

def query_agent_wave(agent, w_range=[400,700], increment=1):
    result = []
    for i in range(0, w_range[1]-w_range[0], increment):
        w_value = w_range[0]+i
        if cfg.use_cone_opponency:
            response = cone_opponency(w_value, agent.cone_proportions)
        else:
            response = response_to_wavelength(w_value, agent.cone_proportions)
        result.append([w_value, agent.name_object([response])])
    inout.write_out(agent.agent_name + "_wavelength_words", result)
    return result
        


    
if __name__ == "__main__":
    #save_values_to_file()
    #save_values_to_file_opponency()
    print cone_opponency(484, [1.0, 1.0, 1.0])
    print cone_opponency(695, [1.0, 1.0, 1.0])
        