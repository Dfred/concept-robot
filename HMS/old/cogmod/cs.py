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

from numpy import *
import auks, cfg
import random as rn
from random import uniform
import time
from xml.etree import ElementTree as ET


class CS():
    """ Conceptual Space class
    """
    
    def __init__(self):
        """ initiate variables 
        """
        self.concepts = {}          # dictionary containing the P_concepts


    def create_pconcept(self, tag, data):
        """ create new concept
        """
        self.concepts[tag] = P_Concept(data)
        
        
    def update_domains(self, domain):
        """ updates the domain list
        """
        if domain not in self.domains:
            self.domains.append(domain)
            
        
    def get_concept(self, tag):
        """ returns the concept for a given tag
        """
        return self.concepts[tag]
    

    def get_concept_data(self, tag):
        """ returns the perceptual data for the given tag
        """
        return self.concepts[tag].get_data()
        
        
    
    def calc_similarity_data(self, pc, data):
        """ calculates the similarity between a pconcept and data from one domain, taking confidence level into account
        """
        sim = 0
        for i in pc.components.keys():
            sim += pc.components[data[0]].confidence * (e**(-auks.calc_distance_euc2(pc.components[data[0]].coordinates, data[1])))
        return sim
    
    
    def calc_similarity_data_no_conf(self, pc, data):
        """ calculates the similarity between a pconcept and data from one domain, not using confidence level
        """
        sim = 0
        for i in pc.components.keys():
            sim += e**(-auks.calc_distance_euc2(pc.components[data[0]].coordinates, data[1]))
        return sim
    
    
    def get_closest_pc(self, data):
        """ returns the key of the best matching pconcept for given data, using similarity measurement
        """
        similarity = []
        concepts = []
        for i in self.concepts:
            sim = 0
            for j in data:
                if j[0] in self.concepts[i].components:
                    sim += self.calc_similarity_data(self.concepts[i], j)
            similarity.append(sim)
            concepts.append(i)
        return concepts[auks.posMax(similarity)]
    
    
    def get_closest_pc_distance(self, data):
        """ returns the key of the best matching pconcept for given data, using distance measurement
        """
        distance = []
        concepts = []
        for i in self.concepts:
            dist = 0
            for j in data:
                if j[0] in self.concepts[i].domains:
                    dist += auks.calc_distance_euc2(self.concepts[i].domains[j[0]].coordinates, j[1])  # no weight on domains
            distance.append(dist)
            concepts.append(i)
        return concepts[auks.posMin(distance)]
    
    
    def get_cs(self):
        dat = []
        for i in self.concepts:
            dat.append(self.concepts[i].get_data())
        return dat


    def get_xml(self):
        """ returns self content as xml
        """
        cs_root = ET.Element("CS")
        for i in self.concepts:
            cs_root.append(self.concepts[i].get_xml(i))
        return cs_root
        
        
        
class P_Concept():
    """ Perceptual Concept class
    """
    
    def __init__(self, init_data):
        """ initiate variables 
        """
        self.components = {}                # components of the concept
        self.initialise(init_data)          # initialise with given data

        
    def initialise(self, init_data):
        """ initialise with given data
            init_data = [ ['domain1', [data]], ['domain2', [data]],...]
        """
        for i in init_data:
            self.components[i[0]] = Domain(i[1])
        
        
    def add_data(self, exemplar_data):
        """ adds exemplar data to existing domains, or puts data in a new domain 
            exemplar_data format = [ ['domain1', [data]], ['domain2', [data]],...]
        """
        for i in exemplar_data:
            if i[0] in self.components:
                self.components[i[0]].add_exemplar_data(i[1])
            else:
                self.components[i[0]] = Domain(i[1])
                
    
    def get_data(self):
        """ returns the associated data from all domains
        """
        dat = []
        for i in self.components:
            dat.append([i, self.components[i].get_data()])
        return dat
            
            
    def get_xml(self, tag):
        """ returns self content as xml
        """
        pconcept_root = ET.Element("P_CONCEPT", id_tag=tag)
        for i in self.components:
            pconcept_root.append(self.components[i].get_xml(i))
        return pconcept_root
        
            
class Domain():
    """ Domain class
    """
    
    def __init__(self, coors):
        """ initiate domain 
        """
        self.coordinates = array(coors, dtype = float32)        # coordinates of prototype
        self.sd = zeros(len(coors), dtype = float32)            # sd of coordinates
        self.sd_av = 0                                          # average measure of sd for domain
        self.confidence = 1.0                                   # initial confidence
        self.prototype_data = array([coors], dtype = float32)   # data from which the prototypes are extracted
            
            
    def add_exemplar_data(self, exemplar_data):
        """ update coordinates based on incoming exemplar data
        """
        ex = array(exemplar_data, dtype=float32)
        self.prototype_data = vstack((self.prototype_data, ex))
        for i in range(len(exemplar_data)):
            diff = (exemplar_data[i] - self.coordinates[i])/len(self.prototype_data)
            mean = self.coordinates[i] + diff
            sd = 0
            for j in self.prototype_data:
                sd = sd + ((j[i] - mean)**2)
            sd = sqrt(sd/len(self.prototype_data))
            self.coordinates[i] = mean
            self.sd[i] = sd
        self.sd_av = (self.sd.sum()/len(self.sd))
        self.confidence = 1 - self.sd_av
        
    def get_data(self):
        return self.coordinates
    
    
    def get_xml(self, dom):
        """ returns self content as xml
        """
        domain_root = ET.Element("DOMAIN", domain=dom)
        coordinates = ET.SubElement(domain_root, "coordinates")
        coordinates.text = str(self.coordinates.tolist())
        sd = ET.SubElement(domain_root, "sd")
        sd.text = str(self.sd)
        sd_av = ET.SubElement(domain_root, "sd_av")
        sd_av.text = str(self.sd_av)
        confidence = ET.SubElement(domain_root, "confidence")
        confidence.text = str(self.confidence)
        prototype_data = ET.SubElement(domain_root, "prototype_data")
        prototype_data.text = str(self.prototype_data)
        return domain_root
    
    
def load_xml(file_name):
    """ returns a new CS loaded from an xml file
    """
    tree = ET.parse(file_name)
    element = tree.getroot()
    cs_elem = element.find('CS')
    new_cs = CS()
    for i in cs_elem:
        dom_elem = i.find('DOMAIN')
        coors = dom_elem.find('coordinates')
        new_cs.create_pconcept(i.attrib["id_tag"], [ [dom_elem.attrib["domain"], eval(coors.text) ] ])
    return new_cs

                    
def run():
    c = CS()
    c.create_pconcept('ball', [ ['rgb', [1, 0, 0]], ['sh', [1]]])
    c.get_concept('ball').add_data([['rgb', [0.1, 0.9, 0]], ['sh', [0.9]]])
    
    c.create_pconcept('red', [ ['rgb', [1, 0, 0]], ['sh', [1]]])
    c.get_concept('red').add_data([['rgb', [0.9, 0.1, 0]], ['sh', [5]]])

    print c.get_closest_pc([['rgb', [1, 0, 0]], ['sh', [2]]])
    print c.get_closest_pc([['sh', [1]]])
 

if __name__ == "__main__":
    run()