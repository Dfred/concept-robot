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

from math import *
import random as ran
import cfg, auks, matrix, inout


class SA_network():
    """ Spreading activation network
    """
    
    def __init__(self, name):
        """ initiate variables 
        """
        self.name = name
        self.n_nodes = 0
        self.nodes = []
        self.run_update = True
        self.iterations = 0
        self.matrix = matrix.Matrix(self.name)
        
        
    def load_SAN(self, tags, data):
        """ load existing SAN data
            format = ["name", [nodes], matrix]
            matrix format = [ [["tag1", weight"], ["tag2", weight"], ..] for each node
        """
        self.name = data[0]
        for x, i in enumerate(tags):
            self.create_node(i)
            for j in data[1][x]:
                self.matrix.add_link(i, j[0])
                self.matrix.set_strength(j[0], i, j[1])
        


    def create_node(self, tag):
        """ creates a new node
        """
        for i in self.nodes:
            if tag == i.tag:
                pass
        self.nodes.append(Node(tag))
        self.n_nodes += 1
        
        
    def add_link(self, tag1, tag2):
        self.matrix.add_link(tag1, tag2)
     
        
    def set_strength(self, v_tag, h_tag, strength):
        self.matrix.set_strength(v_tag, h_tag, strength)
           
                            
    def update(self):
        """ calculates update
        """
        self.iterations = 0
        while self.run_update and self.iterations < cfg.distance_constraint:    # optional use of distance constraint
            self.run_update = False
            self.iterations += 1
            for i in self.nodes:
                if i.activation > cfg.firing_threshold and not i.has_fired:
                    self.run_update = True
                    i.has_fired = True
                    weights = self.matrix.get_v_tag_values(i.tag)
                    if (cfg.fan_out_constraint > 0) and (len(weights) >= cfg.fan_out_constraint):   # optional use of fan-out constraint
                        pass
                    else:
                        for x, j in enumerate(self.nodes):
                            weight = 0.0
                            for k in weights:   # find weight
                                if k[0] == j.tag:
                                    weight = k[1]
                                    break
                            j.input += i.activation * weight * cfg.decay
            for i in self.nodes:
                i.activation += i.input
                if i.activation > 1.0:  # pruning
                    i.activation = 1.0
                if i.activation < 0.0:
                    i.activation = 0.0
                i.input = 0.0
                
        for i in self.nodes:    # reset network for new round
            i.has_fired = False
        self.iterations = 0
        self.run_update = True
            
            
    def update_links(self, tag1, tag2):
        """update link strength between 2 tags using Hebbian learning, if they exist in the matrix
        """
        try:
            self.matrix.increase_strength(tag1, tag2, cfg.new_link_strength)
        except ValueError:
            pass
        try:
            self.matrix.increase_strength(tag2, tag1, cfg.new_link_strength)
        except ValueError:
            pass

            
    def get_node(self, net_tag):
        """returns a node based on given tag
        """
        for i in self.nodes:
            if i.tag == net_tag:
                return i
            
            
    def get_activated_node(self):
        """returns the node with the highest activation
        """
        activations = []
        for i in self.nodes:
            activations.append(i.activation)
        return self.nodes[auks.posMax(activations)]
    
    
    def get_semi_activated_node(self):
        """returns the node with the 2nd highest activation
        """
        activations = []
        for i in self.nodes:
            activations.append(i.activation)
        return self.nodes[auks.posSemiMax(activations)]
    
    
    def get_related_active_node(self):
        """probabilistically returns a node with is related (based on activation) to the activated node
        """
        activations = []
        while len(activations) == 0: 
            for i in self.nodes:
                if i.activation > 0 and i.activation >= ran.random():
                    activations.append(i)
        return activations[ran.randint(0, len(activations)-1)]

    
    def get_nodes_activation(self):
        """returns a list of all nodes + activation
        """
        nodes = []
        for i in self.nodes:
            nodes.append([i.tag, i.activation])
        return nodes
            
            
    def set_activation(self, tag, activation):
        """sets the activation of the node for the given tag
           value is added to existing activation
           return value specifies if words are known
        """
        known_words = False
        for i in self.nodes:
            if i.tag == tag:
                i.activation += activation
                known_words = True
        return known_words
                
                
    def gui_spread_activation(self):
        """spreads activation after a node has been activated in the gui
        """
        self.reset()
        for i in self.nodes:
            if i.selected:
                i.activation = 1.0
        self.update()
                
                
    def get_network(self):
        """returns an image of the whole network (nodes + links)
           format =  [success_rate, node_number, activation,], links[]
                     e.g. [0, 0.5], [[1, 0.6], [2, 0.6], [5, 0.4]]
        """
        network = []
        for i in self.nodes:
            if i.n_gg_games > 0:
                success_rate = i.gg_success/i.n_gg_games
            else:
                success_rate = 1
            network.append([success_rate, i.number, i.activation])
        return (network, self.links)
        
        
    def get_links(self, node_tag, threshold = None):
        """returns all links for a given node, threshold for weight is optional
            format = [[link_tag, weight]....]
        """
        links = self.matrix.get_v_tag_values(node_tag)
        response = []
        for i in links:
            if len(i) > 1:
                if i[1] > threshold:
                    response.append(i)
        return response
                
                             
    def reset(self):     
        """resets the activation of all nodes to 0.0 and enables them to fire again
        """
        for i in self.nodes:
            i.activation = 0.0
                       
                       
    def deselect_all(self, node = None):     
        """deselects all nodes in SAN except for given
        """
        for i in self.nodes:
            if i is not node:
                i.selected = False
                    
                                
    def print_nodes(self):
        """print the nodes of the network
        """
        print "*********** network activation ***********"
        for i in self.nodes:
            print "Node #: " + str(i.number) + ", activation: " + str(i.activation)


    def print_links(self):
        """print the links of the network
        """
        self.matrix.print_matrix()
        

    def save_links(self):
        """saves the links of the network to a text file
        """
        self.matrix.save_matrix()
        

    def save_links2(self):
        """saves the links of the network to a text file
        """
        inout.save_matrix("agent", self.name, self.matrix)
            
            
    def set_node_usage(self, net_tag):
        """updates nodes usage for guessing gamges
        """
        for i in self.nodes:
            if i.tag == net_tag:
                i.n_gg_games += 1
                
    def set_node_success(self, net_tag):
        """updates nodes usage for guessing gamges
        """
        for i in self.nodes:
            if i.tag == net_tag:
                i.gg_success += 1

        
        
class Node():
    """ SA node
    """
    
    def __init__(self, tag, activation = 0.0, has_fired = False):
        """ initiate variables 
        """
        self.tag = tag                  # tag linking to lexicon and CS
        self.activation = activation    # activation
        self.has_fired = has_fired      # node has fired or not
        self.input = 0                  # input from connecting nodes
        self.n_gg_games = 0             # number of usages in guessing games
        self.gg_success = 0             # success rate of node in language game interaction
        self.selected=False             # specifies if a node is selected (in GUI)
        