# cs.py

from math import sqrt
import auks, cfg

class CS():
    """ Conceptual Space class
    """
    
    def __init__(self):
        """ initiate variables 
        """
        self.concepts = []              # list of concepts
        self.concept_tags = []          # list of concept tags

            
    def create_pconcept(self, tag, data):
        """ create new concept
        """
        self.concepts.append(P_Concept(tag, data))
        self.concept_tags.append(tag)
            
            
    def get_concept(self, tag):
        """ returns the concept for a given tag
        """
        for i in self.concepts:
            if i.tag == tag:
                return i
            
            
    def get_concept_data(self, tag):
        """ returns the concept data for a given tag
        """
        for i in self.concepts:
            if i.tag == tag:
                return i.get_data()
            
    
    def get_closest_concept_tag(self, object_data):
        """ returns the tag of the closest concept based on given stimulus
        """
        similarities = []
        for i in self.concepts:
            #similarities.append(auks.calculate_similarity(object_data, i.get_data(), cfg.sensitivity))
            # not using similarity but distance at the moment, possibly change
            similarities.append(auks.calculate_distance(object_data, i.get_data()))
        return self.concepts[auks.posMin(similarities)].tag
    
    
    def get_closest_concept_tags_domains(self, object_data):
        """ returns the tag of the closest concept based on given stimulus, one tag for each domain in the object_data
        """
        domain_tags = []
        for j in object_data:
            similarities = []
            for i in self.concepts:
                #similarities.append(auks.calculate_similarity(object_data, i.get_data(), cfg.sensitivity))
                # not using similarity but distance at the moment, possibly change
                similarities.append(auks.calculate_distance([j], i.get_data()))
            domain_tags.append(self.concepts[auks.posMin(similarities)].tag)
        return domain_tags
    
    
    def get_distance(self, object_data):
        """ returns the distance of all concepts in cs to given stimulus
        """
        domain_tags = []
        for j in object_data:
            similarities = []
            for i in self.concepts:
                similarities.append([i.tag, auks.calculate_similarity(object_data, i.get_data(), cfg.sensitivity)])
            domain_tags.append(similarities)
        return domain_tags
    
    
    def get_closest_concept_tags_domains_2nd_best(self, object_data):
        """ returns the tag of the 2nd best concept based on given stimulus, one tag for each domain in the object_data
        """
        domain_tags = []
        for j in object_data:
            similarities = []
            for i in self.concepts:
                #similarities.append(auks.calculate_similarity(object_data, i.get_data(), cfg.sensitivity))
                # not using similarity but distance at the moment, possibly change
                similarities.append(auks.calculate_distance([j], i.get_data()))
            domain_tags.append(self.concepts[auks.posSemiMin(similarities)].tag)
        return domain_tags
    
    
    def get_closest_concept_tagsim(self, object_data):
        """ returns the tag and similarity of the closest concept to the given stimulus
        """
        similarities = []
        for i in self.concepts:
            similarities.append(auks.calculate_similarity(object_data, i.get_data(), cfg.sensitivity))
        max_pos = auks.posMax(similarities)
        return (self.concepts[max_pos].tag, similarities[max_pos])
    
    
    def get_closest_concept_tagdist(self, object_data):
        """ returns the tag and distance of the closest concept to the given stimulus
        """
        similarities = []
        for i in self.concepts:
            similarities.append(auks.calculate_distance(object_data, i.get_data()))
        max_min = auks.posMin(similarities)
        return (self.concepts[max_min].tag, similarities[max_min])
        
        
    def set_concept_disc_use(self, tag, success):
        """ sets the usage of a P_concept for discrimination games, success (0-1) indicates fail/success
        """
        for i in self.concepts:
            if i.tag == tag:
                i.n_disc_games += 1
                i.n_disc_success += success
                
                
    def count_successfull_concepts(self, threshold):
        """ counts the number of concepts successful in discrimination games based on given threshold
        """
        number = 0
        for i in self.concepts:
            if i.n_disc_games > 0:
                if (i.n_disc_success/i.n_disc_games) >= threshold:
                    number += 1
        return number
    
    
    def get_cs(self):
        """ returns data from all concepts in the CS
        """
        all_data = []
        for i in self.concepts:
            all_data.append(self.get_concept_data(i.tag))
        return all_data
    
    def get_cs2(self):
        """ returns data from all concepts in the CS including tag
        """
        all_data = []
        for i in self.concepts:
            all_data.append([i.tag, self.get_concept_data(i.tag)])
        return all_data
            

class P_Concept():
    """ Perceptual Concept class
    """
    
    def __init__(self, tag, values = None):
        """ initiate variables 
        """
        self.domains = []                   # domains in which the concepts has coordinates
        self.tag = tag                      # connection to the sa_network
        self.n_disc_games = 0               # number of discrimination games
        self.n_disc_success = 0             # number of successful discrimination games
        if values:                          # initialise concept for given data
            self.initialise(values) 
        
    def initialise(self, values):
        for i in values:
            self.domains.append(Domain(i[0], i[1]))
            
    def get_data(self):
        """returns the domains containing the data of the concept
        """
        dat = []
        for i in self.domains:
            dat.append([i.name, i.dimensions])
        return dat
    
    def add_data(self, exemplar_data):
        """ adds exemplar data to the percept
            exemplar_data format = [ "domain", [[ "d1", value], [ "d2", value], [ "d3", value]]]
                                   [["c",[["r",1.0],["g",0.0],["b",0.0]]]]
        """
        for i in exemplar_data:
            for j in self.domains:
                if i[0] == j.name:
                    j.add_exemplar_data(i[1])
        
    
    def move_to(self, exemplar_data):
        """ moves the percept in the direction of the given exemplar_data
            exemplar_data format = [ "domain", [[ "d1", value], [ "d2", value], [ "d3", value]]]
                                   [["c",[["r",1.0],["g",0.0],["b",0.0]]]]
        """
        for i in exemplar_data:
            for j in self.domains:
                if i[0] == j.name:
                    j.move_to(i[1])
        
class Domain():
    """ Domain class, containing domain + associated dimensions
        dimensions = [[ "d1", value, SD], [ "d2", value, SD], [ "d3", value, SD]]
    """
    
    def __init__(self, name, coors):
        """ initiate domain 
        """
        self.name = name            # domain name
        self.dimensions = []        # list of dimensions + coors
        self.prototype_data = []    # data from which the prototypes are extracted
        self.init_data(coors)       # sets data on the given coordinates
        
        
    def init_data(self, coors):
        """ initiates data on given coordinates
            coors format = ["d1", value, SD]
        """
        for i in coors:
            self.dimensions.append([i[0], i[1], 0.0])
            self.prototype_data.append([i[0], i[1]])
            
            
    def add_exemplar_data(self, exemplar_data):
        """ adds exemplar data to the domain
            exemplar_data format = [[ "d1", value], [ "d2", value], [ "d3", value]]]
        """
        for i in exemplar_data:
            for j in self.dimensions:
                if i[0] == j[0]:    # if the dimension name match
                    self.prototype_data.append(i)
                    number = 0    
                    # find number of exemplars used for prototype                    
                    for k in self.prototype_data:       
                        if k[0] == i[0]:
                            number += 1
                    difference = (i[1] - j[1])/ number      # calculate difference
                    mean = j[1] + difference
                    # calculate SD: sqrt( sum(x - mean)**2/n )
                    sd = 0
                    for k in self.prototype_data:
                         if k[0] == i[0]:
                            sd = sd + ((k[1] - mean)**2)
                    sd = sqrt(sd / (number))
                    j[1] = mean
                    j[2] = sd
                    
                    
    def move_to(self, exemplar_data):
        """ moves the coordinates in the domain the the direction of the given exemplar data
            cfg.learning_rate determines the strength 
            exemplar_data format = [[ "d1", value], [ "d2", value], [ "d3", value]]]
        """
        for i in exemplar_data:
            for j in self.dimensions:
                if i[0] == j[0]:    # if the dimension name match
                    difference = cfg.move_learning_rate * (i[1] - j[1])     # calculate difference
                    j[1] = j[1] + difference
                    
                    
                    
    def get_data(self):
        return [self.name, self.dimensions]
    
    def get_prototype_data(self):
        return self.prototype_data