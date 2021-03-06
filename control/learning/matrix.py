# matrix.py

import numpy
from numpy import *
import auks, cfg



class Matrix():
    """ Matrix for the storage of weights between tags
        old matrix version "tags" = horizontal_tags, "labels" = vertical_tags
    """
    
    def __init__(self, name):
        """ initiate variables """
        self.name = name               # name of the matrix
        self.horizontal_tags = []      # list of labels
        self.vertical_tags = []        # list of tags
        self.matrix = numpy.array([])  # matrix
        
            
    def add_link(self, h_tag, v_tag):
        """ adds a new link to the repertoire, and/or updates the associative matrix """
        # if label and tag are not known
        if (h_tag not in self.horizontal_tags and v_tag not in self.vertical_tags):
            # create new matrix if none exists
            if len(self.matrix) == 0:   
                self.matrix = [[0.5]]
            # update matrix with new connection
            else:                       
                length_h= len(self.horizontal_tags)
                length_v = len(self.vertical_tags)
                #new_zeros = numpy.zeros(length_labels)
                new_zeros = numpy.array([0.0] * length_v)
                new_zeros.shape = (length_v, 1)
                try:
                    self.matrix = numpy.hstack((self.matrix, new_zeros))
                except ValueError:
                    pass
                #new = numpy.append(numpy.zeros(length_tags), 0.5)
                new = numpy.append(numpy.array([0.0] * length_h), 0.5)
                try:
                    self.matrix = numpy.vstack((self.matrix,new))
                except ValueError:
                    pass
            # add label and tag
            self.vertical_tags.append(v_tag)
            self.horizontal_tags.append(h_tag)
        # if h_tag is already known, a new v_tag is added
        elif v_tag not in self.vertical_tags and h_tag in self.horizontal_tags:
            new = numpy.array([0.0] * len(self.horizontal_tags))
            for count, i in enumerate(new):
                if count == self.horizontal_tags.index(h_tag):
                    new[count] = 0.5
            self.matrix = numpy.vstack((self.matrix,new))
            self.vertical_tags.append(v_tag)
        # if v_tag is already known, a new h_tag is added
        elif h_tag not in self.horizontal_tags and v_tag in self.vertical_tags:
            new = numpy.array([])
            for count, i in enumerate(self.matrix):
                if count != self.vertical_tags.index(v_tag):
                    new = numpy.hstack((new, [0.0]))
                else:
                    new = numpy.hstack((new, [0.5]))
            new.shape = len(self.vertical_tags), 1
            self.matrix = numpy.hstack((self.matrix, new))
            self.horizontal_tags.append(h_tag)
        # if both tag and label are known, matrix is updated with a new connection
        else:
            v_index = self.vertical_tags.index(v_tag)
            h_index = self.horizontal_tags.index(h_tag)
            self.matrix[v_index][h_index] = 0.5
            
            
    def increase_strength(self, v_tag, h_tag, amount):
        """ increases the association strength between the given label and tag
            if lateral_inhibition is used, other associations are weakened
        """
        v_index = self.vertical_tags.index(v_tag)
        h_index = self.horizontal_tags.index(h_tag)
        if self.matrix[v_index][h_index] <= (1 - amount):
            self.matrix[v_index][h_index] += amount
        #decrease competing connections if lateral_inhibition is used
        if cfg.lateral_inhibition:
            for count2, i in enumerate(self.matrix):
                if count2 != v_index:
                    for count, j in enumerate(i):
                        if count == h_index:
                            if self.matrix[count2][count] >= (0 + amount):
                                self.matrix[count2][count] -= amount
            for count, i in enumerate(self.matrix[v_index]):
                if count != h_index:
                    if self.matrix[v_index][count] >= (0 + amount):
                        self.matrix[v_index][count] -= amount
        
        
    def decrease_strength(self, v_tag, h_tag, amount):
        """ decreases the association strength between the given label and tag
        """
        v_index = self.vertical_tags.index(v_tag)
        h_index = self.horizontal_tags.index(h_tag)
        if self.matrix[v_index][h_index] >= (0 + amount):
            self.matrix[v_index][h_index] -= amount
            
            
    def set_strength(self, v_tag, h_tag, strength):
        """ set the association strength between the given label and tag
        """
        v_index = self.vertical_tags.index(v_tag)
        h_index = self.horizontal_tags.index(h_tag)
        self.matrix[v_index][h_index] = strength
        
            
    def get_h_tag(self, v_tag):
        """ retrieves the h_tag with the highest association for the given v_tag 
            if there are more than one h_tags with the highest association value, 
            the first one will be returned
        """
        v_index = -1
        for count, i in enumerate(self.vertical_tags):
            if i == v_tag:
                v_index = count
                break
        if v_index == -1:
            return "label_unknown"
        else:
            max = auks.posMax(self.matrix[v_index])
            return self.horizontal_tags[max]
    
    
    def get_v_tag(self, h_tag, inaccuracy=None):
        """ retrieves the v_tag with the highest association for the given h_tag 
            if there are more than one v_tags with the highest association value, 
            the first one will be returned
            if inaccuracy == True/1, the v_tag with the 2nd highest association is returned
        """
        h_index = -1
        for count, i in enumerate(self.horizontal_tags):
            if i == h_tag:
                h_index = count
                break
        if h_index == -1:
            return "tag_unknown"
        else:
            value_list = []
            for i in self.matrix:
                for count, j in enumerate(i):
                    if count == h_index:
                        value_list.append(j)
            if inaccuracy:
                return self.vertical_tags[auks.posSemiMax(value_list)]
            else:
                return self.vertical_tags[auks.posMax(value_list)]


    def get_v_tag_values(self, h_tag, inaccuracy=None):
        """ returns the range of v_tags + values for the given h_tag
        """
        h_index = -1
        for count, i in enumerate(self.horizontal_tags):
            if i == h_tag:
                h_index = count
                break
        if h_index == -1:
            return "tag_unknown"
        else:
            value_list = []
            for x, i in enumerate(self.matrix):
                for count, j in enumerate(i):
                    if count == h_index:
                        value_list.append([self.vertical_tags[x],j])
            return value_list
        

    def get_h_tag_values(self, v_tag, inaccuracy=None):
        """ returns the range of h_tags + values for the given v_tag
        """
        v_index = -1
        for count, i in enumerate(self.vertical_tags):
            if i == v_tag:
                v_index = count
                break
        if v_index == -1:
            return "tag_unknown"
        else:
            for x, i in enumerate(self.matrix):
                if x == v_index:
                    value_list = []
                    for count, j in enumerate(self.horizontal_tags):
                        value_list.append([j, self.matrix[x][count]])
            return value_list


        
    def print_matrix(self):
        """ prints  matrix """
        print str(self.name) + " matrix:"
        print "        ",  self.horizontal_tags
        j = 0
        for i in self.vertical_tags:
            print "'", i,"'", 
            for k in self.matrix[j]:
                    print " ",  '%.2f'% k, "     ", 
            print "\n"
            j += 1
            
            
    def get_matrix(self):
        """ returns  matrix 
        """
        return self.matrix
    
    
    def save_matrix(self, agent_name):
        """ saves the  matrix 
        """
        savetxt(agent_name + "_" + self.name + ".txt", self.matrix , fmt="%12.6G")    # save to file
        

