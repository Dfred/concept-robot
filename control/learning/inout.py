# io.py
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
    filename = "out_" + name + ".csv"
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
    filename = name + ".csv"
    out_file = csv.writer(open(filename, 'w'), delimiter=',', quotechar='|')
    for i in output:
        out_file.writerow(i)
        
        
def write_out_average(name, output):
    """ calculates average values and saves into file
    """
    filename = name + ".csv"
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
    filename =  agent_name + matrix_name + ".csv"
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
    text_file = open(agent_name + "_ggobi_" + ".csv", "w")
    text_file.write(" ,dom0,dim0,dim1,dim2 \n")
    for x, i in enumerate(cs):
        text_file.write(str(x) + ",1," + str(i[0][1][0][1]) + "," + str(i[0][1][1][1]) + "," + str(i[0][1][2][1]) + "\n" )
    
        

def save_knowledge(agent):
    """ saves all knowledge structures for a given agent
    """
    save_matrix(agent.agent_name, agent.cs_cs.matrix.name, agent.cs_cs.matrix)
    save_matrix(agent.agent_name, agent.lex_lex.matrix.name, agent.lex_lex.matrix)
    save_gdf(agent.agent_name, agent.cs_cs)
    save_gdf(agent.agent_name, agent.lex_lex)
    save_matrix(agent.agent_name, agent.cs_lex.name, agent.cs_lex)
    write_out(agent.agent_name + "_cs", agent.cs.get_cs())
    save_cs_ggobi(agent.agent_name + "_cs", agent.cs.get_cs())
    write_out(agent.agent_name + "_lex", [agent.lex.words])
    

def save_gdf(agent_name, san):
    """ saves a given SAN in gdf format
    """
    text_file = open(agent_name + "_" + str(san.name) + ".gdf", "w")
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
    
    
