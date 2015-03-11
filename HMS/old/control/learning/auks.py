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
import time, copy
import random as ran
import data, cfg, sa_network, matrix
import globals as gl


def posMax(list):
    """ returns the index of the highest value of a given list
        if multiple highest values exist, the first is returned
    """
    m = list[0]
    index = 0
    for i, x in enumerate(list):
        if x > m:
            m = x
            index = i
    return index


def posSemiMax(list):
    """ returns the index of the semi-highest value of a given list
        if multiple values exist, the first is returned
    """
    list_copy = copy.deepcopy(list)
    m = list_copy[0]
    index1 = 0
    for i, x in enumerate(list_copy):
        if x > m:
            m = x
            index1 = i
    list_copy.pop(index1)
    m = list_copy[0]
    index2 = 0
    for i, x in enumerate(list_copy):
        if x > m:
            m = x
            index2 = i
    if index1 <= index2:
        index2 += 1
    return index2


def posMin(list):
    """ returns the index of the lowest value of a given list
        if multiple highest values exist, the first is returned
    """
    m = list[0]
    index = 0
    for i, x in enumerate(list):
        if x < m:
            m = x
            index = i
    return index


def posSemiMin(list):
    """ returns the index of the semi-lowest value of a given list
        if multiple values exist, the first is returned
    """
    list_copy = copy.deepcopy(list)
    m = list_copy[0]
    index1 = 0
    for i, x in enumerate(list_copy):
        if x < m:
            m = x
            index1 = i
    list_copy.pop(index1)
    m = list_copy[0]
    index2 = 0
    for i, x in enumerate(list_copy):
        if x < m:
            m = x
            index2 = i
    if index1 <= index2:
        index2 += 1
    return index2


def generateRandomTag(length):
    """ generates a random alphanumeric tag with a given length 
    """
    i = 0
    tag = ""
    while i < length:
        tag += str((ran.choice(data.alphanumeric_set)))
        i += 1
    return tag


def calculate_distance(point1, point2):
    """ calculates distance between 2 given points 
        point1 = [ [ "domain", [ ["d1", value], ["d2", value]]], ...]
        point2 = [ [ "domain", [ ["d1", value, SD], ["d2", value, SD]]], ...]
        possible existing SD's in points are ignored
    """
    #return (abs(point1[0]-point2[0]) + abs(point1[1]-point2[1]))
    distance = 0
    no_dim_match = True
    for i in point1:
        for j in point2:
            if i[0] == j[0]:    # if domains match
                no_dim_match = False
                dist = 0
                for count, k in enumerate(i[1]):
                    dist += (i[1][count][1] - j[1][count][1])**2
                distance += sqrt(dist)
                #normalise
                #TODO: make nicer implementation of normalise, this is ad-hoc
                if i[0] == "c":
                    distance = distance/1.73205080757
                if i[0] == "sh":
                    distance = distance/3.0
    return distance + (no_dim_match * cfg.no_dim_match_penalty)


def calculate_distance_hsv(point1, point2):
    """ calculates distance between 2 given points 
        point1 = [ [ "domain", [ ["d1", value], ["d2", value]]], ...]
        point2 = [ [ "domain", [ ["d1", value, SD], ["d2", value, SD]]], ...]
        possible existing SD's in points are ignored
        modified distance calculation for hsv coding, where h is mapped from -180 to 180
    """
    #return (abs(point1[0]-point2[0]) + abs(point1[1]-point2[1]))
    distance = 0
    no_dim_match = True
    for i in point1:
        for j in point2:
            if i[0] == j[0]:    # if domains match
                no_dim_match = False
                dist = 0
                for count, k in enumerate(i[1]):
                    #dist += (i[1][count][1] - j[1][count][1])**2
                    n1 = i[1][count][1]
                    n2 = j[1][count][1]
                    if count == 0:  # special case for h value ranging from -180 to 180
                        if n1 >= n2:
                            big = n1
                            small = n2
                        else:
                            big = n2
                            small = n1
                        d1 = big - small
                        d2 = small + (360 - big)
                        if d1 <= d2:
                            dist += d1
                        else:
                            dist += d2            
                    else:
                        dist += abs(n1 - n2)
                #normalise
                #TODO: make nicer implementation of normalise, this is ad-hoc
                if i[0] == "c":
                    dist = dist/1.73205080757
                if i[0] == "sh":
                    dist = dist/3.0
    return dist + (no_dim_match * cfg.no_dim_match_penalty)
                
    

def calculate_similarity(point1, point2, sensitivity = 1.0):
    """ calculates the similarity between two given points
        based on the distance and the sensitivity (when distance is 0, similarity is 1.0 (max))
        after Nosofsky (1986)
        point = [ [d1, value], [d2, value], ..., [dn, value] ]
        sensitivity = float
    """
    distance = calculate_distance(point1, point2)
    return e**(-sensitivity * (distance**2))


def generate_training_data_colour(n_sets, context_size, type = "rgb"):
    """ generates training data for language games in colour domain
    """
    training_dataset = []
    count = 0
    start_time = time.time()
    while count < n_sets:
        count2 = 0
        set = []
        while count2 < context_size:
            check = True
            while check:
                if type == "rgb":
                    stimulus = [["c", [["r", ran.random()], ["g", ran.random()], ["b", ran.random()]]]]
                if type == "hsv":
                    stimulus = [["c", [["h", ran.random()], ["s", ran.random()], ["v", ran.random()]]]]
                if set == []:
                    check = False
                else:   # check if distance is big enough
                    sequence = []
                    for i in set:
                        if cfg.sample_minimum_distance < calculate_distance(i, stimulus):
                            sequence.append("1")
                        else:
                            sequence.append("0")
                    if "0" not in sequence:
                        check = False
            set.append(stimulus)
            count2 += 1
        training_dataset.append(set)
        count += 1
#        if count % (n_sets/5) == 0:
#            print str((count/n_sets)*100) + "% of stimuli sets generated (" + str( round(time.time()-start_time, 2)) + " sec)"
#            start_time = time.time()
    return training_dataset


def generate_training_data_colour_shape(n_sets, context_size):
    """ generates training data for language games in colour and/or shape domain
    """
    training_dataset = []
    count = 0
    start_time = time.time()
    while count < n_sets:
        count2 = 0
        set = []
        while count2 < context_size:
            check = True
            while check:
                stimulus = []
                
#                stimulus.append(["c", [["r", ran.random()], ["g", ran.random()], ["b", ran.random()]]])
#                shape_dist = []
#                for i in data.shape_coors:
#                    shape_dist.append(calculate_distance(stimulus, i))
#                stimulus.append(["sh", [["sh", posMin(shape_dist)]] ])
# random
                stimulus.append(["c", [["r", ran.random()], ["g", ran.random()], ["b", ran.random()]]])
                if ran.randint(0,1): # 50% chance of adding related shape data   
                    shape_dist = []
                    for i in data.shape_coors:
                        shape_dist.append(calculate_distance(stimulus, i))
                    stimulus.append(["sh", [["sh", posMin(shape_dist)]] ])
                if set == []:
                    check = False
                else:   # check if distance is big enough
                    sequence = []
                    for i in set:
                        if cfg.sample_minimum_distance < calculate_distance(i, stimulus):
                            sequence.append("1")
                        else:
                            sequence.append("0")
                    if "0" not in sequence:
                        check = False
            set.append(stimulus)
            count2 += 1
        training_dataset.append(set)
        count += 1
#        if count % (n_sets/5) == 0:
#            print str((count/n_sets)*100) + "% of stimuli sets generated (" + str( round(time.time()-start_time, 2)) + " sec)"
#            start_time = time.time()
    return training_dataset


def generate_training_data_artificial(n_sets, context_size):
    """ generates training data for language games in artificial domain 
     [ ["art_con1", [ ["c",[["r",0.33],["g",0.33],["b",0.33]]]], ["a", [["ad1", 0.25],["ad2", 0.25]] ] ],
    """
    training_dataset = []
    count = 0
    start_time = time.time()
    while count < n_sets:
        count2 = 0
        set = []
        while count2 < context_size:
            check = True
            while check:
                if ran.randint(0,1):    # 50% chance of creating stimulus in 2 domains
                    if ran.randint(0,1):
                        stimulus = [ ["a", [["ad1", ran.random()],["ad2", ran.random()]] ]  ]
                    else:
                        stimulus = [ ["c", [["r", ran.random()], ["g", ran.random()], ["b", ran.random()]]]  ]
                else:
                    stimulus = [ ["c", [["r", ran.random()], ["g", ran.random()], ["b", ran.random()]]]  ]
                    art_dist = []
                    # find related artificial data
                    for i in data.artificial_data1: 
                        art_dist.append(calculate_distance(stimulus, i[1]))
                    stimulus.append(data.artificial_data1[posMin(art_dist)][2])
                if set == []:
                    check = False
                else:   # check if distance is big enough
                    sequence = []
                    for i in set:
                        if cfg.sample_minimum_distance < calculate_distance(i, stimulus):
                            sequence.append("1")
                        else:
                            sequence.append("0")
                    if "0" not in sequence:
                        check = False
            set.append(stimulus)
            count2 += 1
        training_dataset.append(set)
        count += 1
#        if count % (n_sets/5) == 0:
#            print str((count/n_sets)*100) + "% of stimuli sets generated (" + str( round(time.time()-start_time, 2)) + " sec)"
#            start_time = time.time()
    return training_dataset


def generate_training_data_simple(n_objects):
    """ generates simple training data for direct instruction in artificial domain 
        n_objects = number of objects to generate
         [ ["dom0",[["dim0",0.33],["dim1",0.33],["dim2",0.33]]], ["a", [["ad1", 0.25],["ad2", 0.25]] ] 
    """
    training_data = []
    n_domains = len(gl.domain_structure)
    while len(training_data) < n_objects:
        domain = ran.randint(0, n_domains-1)
        object = ["dom" + str(domain)]
        dat = []
        for i in gl.domain_structure[domain][1]:
            dat.append([i[0], ran.random()])
        object.append(dat)
        training_data.append([object])
    return training_data


def generate_artificial_knowledge(n_dom, av_dimensions, avn_exemplars, av_words, av_associations, av_cluster_size = None):
    """ generates artificial conceptual knowledge, consisting of prototypes in CS, Lexicon and SAN weights
        CS dimensions are all [0.0 - 1.0]
        data format = [ [percepts], [CS_SAN], [words], [Lex_SAN], [matrix_weights]]
    """
    gl.domain_structure = generate_domains(n_dom, av_dimensions)
    percepts = fill_domains(gl.domain_structure, avn_exemplars)
    cs_cs = sa_network.SA_network("cs_cs")                  # concept-concept association
    lex_lex = sa_network.SA_network("lex_lex")              # word-word association
    words = generate_words(av_words)
    
    all_percepts = []   # create flat percept structure
    for i in percepts:
        for j in i:
            all_percepts.append(j[0])
    
    if cfg.SAN_clusters:
        create_associations(cs_cs, all_percepts, av_associations, av_cluster_size)
        create_associations(lex_lex, words, av_associations, av_cluster_size)
    else:
        create_associations(cs_cs, all_percepts, av_associations)
        create_associations(lex_lex, words, av_associations)
    cs_lex = matrix.Matrix("cs_lex")              # concept-lexicon association matrix
    set_links(cs_lex, all_percepts, words, 3)     # create links between percepts and words
    return [ percepts, cs_cs, words, lex_lex, cs_lex ]



def generate_domains(n_dom, av_dimensions):
    """ generate domain structure """
    domains = []
    dom_counter = 0
    dim_counter = 0
    while dom_counter < n_dom:
        #n_dim = int(ran.normalvariate(av_dimensions, 2))
        # number of dimensions is not random at the moment
        n_dim = av_dimensions 
        if n_dim < 1: 
            n_dim = 1
        n_dim_local = 0
        dims = []
        while n_dim_local < n_dim:  # create dimensions
            dims.append(["dim" + str(dim_counter)])
            n_dim_local += 1
            dim_counter += 1
        domains.append(["dom" + str(dom_counter), dims])
        dom_counter += 1
    return domains



def fill_domains(domains, avn_exemplars):
    """ fill the generated domain structure with exemplars """
    structure = []
    tag_list = []
    for i in domains:
        exemplars = []
        n_exemplars = 0
        while n_exemplars == 0:
            n_exemplars = int(ran.normalvariate(avn_exemplars, 2))
        while len(exemplars) < n_exemplars:
            ex_coors = []
            for j in i[1]:
                ex_coors.append([j[0], ran.random()])
            tag = "no_tag"
            while ((tag == "no_tag") or (tag in tag_list)): # make sure the cs_tag is unique
                tag = generateRandomTag(6)
            exemplars.append([tag, [i[0], ex_coors]])
            tag_list.append(tag)
        structure.append(exemplars)
    return structure



def generate_words(av_words):
    """ generate words"""
    n_words = int(ran.normalvariate(av_words, 2))
    words = []
    while len(words) < n_words:
        words.append("word" + str(len(words)))
    return words



def create_associations(san, data_original, av_associations, av_cluster_size = None):
    """ create associations in a given SAN + data
        san = SAN, data = array of strings, av_associations = average associations, av_clusters = average cluster size
    """
    data = copy.deepcopy(data_original)
    for i in data:
        san.create_node(i)              # create node
    if av_cluster_size: # av_cluster size is used to generate clusters
        form_clusters = True
        cluster_connectors = []
        while form_clusters:
            n_cluster = -1
            while n_cluster < 1:    # make sure n_cluster is >= 0
                n_cluster = int(ran.normalvariate(av_cluster_size, 2)) # determine cluster size
            if len(data) >= n_cluster:
                cluster = ran.sample(data, n_cluster)              # create cluster
                for i in cluster:                                  # remove cluster nodes from data
                    for j in data:
                        if i == j:
                            data.remove(j)
            elif len(data) > 0:
                cluster = data
                form_clusters = False
            else:
                form_clusters = False
                break
            #n_links = ran.randint(0, len(cluster))                 # determine number of cluster connectors
            n_links = 1
            if n_links:
                cluster_connectors = cluster_connectors + ran.sample(cluster, n_links)
#            n_associations = ran.randint(0, len(cluster))
#            associations = ran.sample(cluster, n_associations)
            for i in cluster:                                      # create links in cluster
                for j in cluster:
                    if i is j:
                        pass                                       # don't create link to self
                    else:
                        san.add_link(i, j)
                        san.set_strength(j, i, ran.random())
        for i in cluster_connectors:                               # create links between clusters
            for j in cluster_connectors:
                if i is j:
                    pass
                else:
                    san.add_link(i, j)
                    san.set_strength(j, i, ran.random())
    else: # no av_cluster size is given, structure is random
        for i in data:
            n_associations = ran.randint(0, int(len(data)/2))
            associations = ran.sample(data, n_associations)
            for j in associations:
                san.add_link(i, j)
                san.set_strength(j, i, ran.random())    
        
        
def set_links(matrix, percepts, words, av_links):
    """ create links between words and percepts
    """
    for i in percepts:
        for j in words:
            if ran.randint(0,1) == 1:   # 50% chance of creating a link
                matrix.add_link(i, j)
                matrix.set_strength(j, i, ran.random())
            else:
                pass
    for i in words:
        for j in percepts:
            if ran.randint(0,1) == 1:   # 50% chance of creating a link
                matrix.add_link(j, i)
                matrix.set_strength(i, j, ran.random())
            else:
                pass            
            
            
            
def create_knowledge_with_a_data(percepts, cs_san, words, lex_san, mat):
    """ generates artificial conceptual knowledge, consisting of prototypes in CS, Lexicon and SAN weights
        CS dimensions are all [0.0 - 1.0]
        data format = [ [percepts], [CS_SAN], [words], [Lex_SAN], [matrix_weights]]
    """
    cs_cs = sa_network.SA_network("cs_cs")                  # concept-concept association
    tags = []
    for i in percepts:
        tags.append(i[0])
    cs_cs.load_SAN(tags, cs_san)
    lex_lex = sa_network.SA_network("lex_lex")              # word-word association
    lex_lex.load_SAN(words, lex_san)
    cs_lex = matrix.Matrix("matrix")
    for x, i in enumerate(mat):
        for y, j in enumerate(words):
            cs_lex.add_link(tags[x], j)
            cs_lex.set_strength(j, tags[x], mat[x][y][1])
    return [[percepts], cs_cs, words, lex_lex, cs_lex]
        
        
        
        
def calc_associations(dat1):
    """ calculates associations"""
    shape_coors = [ [["c",[["r",0.75],["g",0.25],["b",0.5]]]],
                   [["c",[["r",0.75],["g",0.75],["b",0.5]]]],
                   [["c",[["r",0.25],["g",0.75],["b",0.5]]]],
                   [["c",[["r",0.25],["g",0.25],["b",0.5]]]] ]
    links = []
    max = 1.73205080757
    for i in dat1:
        link = []
        for x, j in enumerate(shape_coors):
            link.append([10+x, 1-((calculate_distance(i[3], j))/max)])
        i[1] = link
    return dat1


def calc_mean(dat):
    """returns the mean values for a collection of data lists
       dat = [ [x1,x2,...,xn], [y1, y2,...,yn]]
    """
    tot = [0] * len(dat[0])
    for i in dat:
        for x, j in enumerate(i):
            tot[x] += j
    for x, i in enumerate(tot):
        tot[x] = tot[x]/len(dat)
    return tot
        
        
def rgb2hsv(dat):
    """converts rgb data to hsv
       dat = [r, g, b]
    """
    
    
if __name__ == "__main__":
    point1 = [ [ "domain", [ ["h", 10], ["d2", 88]]]]
    point2 = [ [ "domain", [ ["h", 200], ["d2", 44]]]]
    print calculate_distance_hsv(point1, point2)
    
