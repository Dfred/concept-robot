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

# input/output file

from __future__ import division
import csv
import numpy
from copy import deepcopy
import cfg


def write_output(name, output):
    """ write output file
        output = [ [value1, value2, value n], ...[value1, value2, value n] ]
    """
    filename = "output/out_" + name + ".csv"
    out_file = csv.writer(open(filename, 'w'), delimiter=',', quotechar='|')
    count = 0
    out = []
    while count < cfg.n_cycles:
        count2 = 0
        out2 = []
        while count2 < cfg.replicas:
            out2.append(output[count2][count])
            count2 += 1
        out.append(out2)
        count += 1
    for i in out:
        out_file.writerow(i)
        
        
def write_out(name, output):
    """ general output function
    """
    filename = "output/" + name + ".csv"
    out_file = csv.writer(open(filename, 'w'), delimiter=',')
    for i in output:
        out_file.writerow(i)
        
        
def write_out_average(name, output):
    """ calculates average values and saves into file
    """
    filename = "output/" + name + ".csv"
    out_file = csv.writer(open(filename, 'w'), delimiter=',', quotechar='|')
    if len(output) > 1:
        out = [0]*len(output[0])
        for i in output:
            for x, j in enumerate(i):
                out[x] += j
        size = len(output) * 1.0
        for x, i in enumerate(out):
            out[x] = out[x]/size
        out_file.writerow(out)
    else:
        out_file.writerow(output[0])
        
        
def save_matrix(agent_name, matrix_name, mat):
    """ saves the association matrix of an agent to a file
    """
    filename =  "output/" + agent_name + matrix_name + ".csv"
    out_file = csv.writer(open(filename, 'w'), delimiter=',', quotechar='|')
    h_tags = deepcopy(mat.horizontal_tags)
    h_tags.insert(0,"")
    out_file.writerow(h_tags)
    for count, i in enumerate(mat.matrix):
        output = numpy.hstack((mat.vertical_tags[count], i))
        out_file.writerow(output)
        

def save_cs_ggobi(agent_name, cs):
    """ saves the cs of an agent to a csv file for usage in ggobi
    """
    text_file = "output/" + open(agent_name + "_ggobi_" + ".csv", "w")
    text_file.write(" ,dom0,dim0,dim1,dim2 \n")
    for x, i in enumerate(cs):
        text_file.write(str(x) + ",1," + str(i[0][1][0][1]) + "," + str(i[0][1][1][1]) + "," + str(i[0][1][2][1]) + "\n" )
    
        

def save_knowledge(agent, filename = ""):
    """ saves all knowledge structures for a given agent
    """
    save_matrix(agent.agent_name, agent.cs_lex.name, agent.cs_lex)
    write_out(agent.agent_name + "_cs", agent.cs.get_cs())
    write_out(agent.agent_name + "_lex", agent.lex.get_lex())
    if cfg.save_agent_xml:
        agent.save_xml(filename)
    if cfg.agent_plot_cs:
        agent.plot_cs()
    
    

def save_gdf(agent_name, san):
    """ saves a given SAN in gdf format
    """
    text_file = open("output/" + agent_name + "_" + str(san.name) + ".gdf", "w")
    text_file.write("nodedef>name VARCHAR,label VARCHAR, activation DOUBLE\n")
    node_data = []
    for i in san.nodes:
        node_data.append([i.tag, i.activation])
    for i in node_data:
        text_file.write(str(i[0]) + "," + str(i[0]) + "," + str(i[1]) + "\n")
    text_file.write("edgedef>node1 VARCHAR,node2 VARCHAR,directed BOOLEAN, weight DOUBLE\n")
    for i in node_data:
        links = san.get_links(i[0], 0.1)
        for j in links:
            text_file.write(str(i[0]) + "," + str(j[0]) + ",true," + str(j[1]) + "\n")
    text_file.close()
    
    
def read_file(filename):
    """ reads a given filename and returns content as a list
    """
    in_file = open(filename, "r")
    return in_file.readlines()


def read_file_csv_basic(filename):
    """ reads a given csv filename and returns content as a list
    """
    reader = csv.reader(open(filename, "rb"))
    return_data = []
    for row in reader:
        for i in range(0, len(row)):
            row[i] = float(row[i])    # cast to float
        return_data.append(row)
    return return_data


def read_file_csv(filename):
    """ reads a given csv filename and returns content as a list
    """
    reader = csv.reader(open(filename, "rb"))
    return_data = []
    for row in reader:
        for i in range(0, len(row)):
            row[i] = float(row[i])    # cast to float
        return_data.append([['rgb', row]])
    return return_data
    
