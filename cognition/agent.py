# agent.py

from __future__ import division
import auks, cs, lexicon, sa_network, cfg, matrix



class Agent():
    """ Agent consisting of SA_network, conceptual space and lexicon
    """
    
    def __init__(self, name, type, initial_knowledge = None):
        """ initiate variables 
            initial_knowledge = (type: l/a, data)
        """
        self.agent_name = name                              # agent name
        self.agent_type = type                              # agent type: "learner" or "teacher"
        self.cs = cs.CS()                                   # agents conceptual space
        self.lex = lexicon.Lexicon()                        # agents lexicon
        self.cs_cs = sa_network.SA_network("cs_cs")         # concept-concept association
        self.cs_lex = matrix.Matrix("cs_lex")               # concept-lexicon association matrix
        self.lex_lex = sa_network.SA_network("lex_lex")     # lexicon-lexicon association
        if initial_knowledge:                               # optional load of initial knowledge
            if initial_knowledge[0] == 'l':
                self.load_initial_knowledge(initial_knowledge[1])
            if initial_knowledge[0] == 'a':
                self.load_artificial_data(initial_knowledge[1])      # load artificial data                   
            
            
        #language game variables
        self.n_discrimination_games = 0
        self.n_success_dg = 0
        self.discrimination_success = 0
        self.n_guessing_games = 0
        self.n_success_gg = 0
        self.guessing_success = 0
        self.used_words = []
        self.comm_success = []
        
        #direct instruction variables
        self.n_words = 0
        self.n_percepts = 0
        self.n_correct = []
        
        # test variables
        self.test_succes = []


    def load_initial_knowledge(self, dat):
        """ load of initial knowledge
        """
        for i in dat:
            cs_tag = auks.generateRandomTag(6)
            self.cs.create_pconcept(cs_tag, i[1])       # create pconcept in CS  
            self.cs_cs.create_node(cs_tag)              # create cs node in cs_cs
            self.cs_cs.add_link(cs_tag, cs_tag)         # add link between cs and cs node
            self.lex.add_word(i[0])                     # create word in lexicon
            self.lex_lex.create_node(i[0])              # create lex node in lex_lex
            self.lex_lex.add_link(i[0], i[0])           # add link between lex and lex node
            self.cs_lex.add_link(cs_tag, i[0])          # add link between lex and cs matrix
            
            
    def load_artificial_data(self, a_data):
        """ load artificial data
            data format = [ [percepts], [CS_SAN], [words], [Lex_SAN], [matrix_weights]]
        """
        for i in a_data[0]:
            for j in i:
                self.cs.create_pconcept(j[0], [j[1]])       # create pconcept in CS
        self.n_percepts = len(self.cs.concepts)
        self.cs_cs = a_data[1]
        for i in a_data[2]:
            self.lex.add_word(i)
        self.n_words = len(self.lex.words)
        self.lex_lex = a_data[3]
        self.cs_lex = a_data[4]
        
            
    def learn_concept(self, word, percept_data):
        """ learn a concept (word + percept)
        """
        # if word is already know, update perceptual data
        if self.lex.check_word(word):
            cs_tag = self.cs_lex.get_h_tag(word)
            self.cs.get_concept(cs_tag).add_data(percept_data)
        
        # if word is not known, create new concept
        else:
            self.lex.add_word(word)                 # create word in lexicon
            self.lex_lex.create_node(word)          # create lex node in lex_lex
            self.lex_lex.add_link(word, word)       # add link between lex and lex node
            cs_list = []                            # create list of percept tags
            for i in percept_data:
                cs_tag = "no_tag"
                while ((cs_tag == "no_tag") or (cs_tag in self.cs.concept_tags)): # make sure the cs_tag is unique
                    cs_tag = auks.generateRandomTag(6)
                cs_list.append(cs_tag)
                self.cs.create_pconcept(cs_tag, [i])      # create pconcept in CS  
                self.cs_cs.create_node(cs_tag)          # create cs node in cs_cs
                self.cs_cs.add_link(cs_tag, cs_tag)     # add link between cs and cs node
                self.cs_lex.add_link(cs_tag, word)      # add link between lex and cs matrix
            
            self.n_percepts = len(self.cs.concepts)     # update numbers
            self.n_words = len(self.lex.words)
                
            if len(cs_list) > 1 and cfg.associative_object_learning:
                while len(cs_list) > 1:
                    self.cs_cs.add_link(cs_list[0], cs_list[1])
                    self.cs_cs.add_link(cs_list[1], cs_list[0])
                    cs_list = cs_list[1:]
        

    def perceive_objects(self, object_data):
        """ perceive an object and activate network accordingly
        """
        net_tags = []
        for i in object_data:
            tagsim = self.cs.get_closest_concept_tagsim(i)
            net_tag = self.cs_net_matrix.get_v_tag(tagsim[0])
            self.network.set_activation(net_tag, (tagsim[1])*3)
            #TODO: redesign similarity calculation, as the *3 is not a nice shortcut to get +/- 1.0 activation
            net_tags.append(net_tag)
        self.network.update()
        if cfg.la_associative_learning:
            self.network.update_links(net_tags)
            
            
    def learn_percept_association(self, object_data):
        """ learn association between two percepts
        """
        tag1 = self.cs.get_closest_concept_tag([object_data[0]])
        tag2 = self.cs.get_closest_concept_tag([object_data[1]])
        self.cs_cs.update_links(tag1, tag2)
        
        
    def learn_word_association(self, word1, word2):
        """ learn association between two words
        """
        self.lex_lex.update_links(word1, word2)
        
        
    def perceive_words(self, words):
        """ perceive words and activate network accordingly
            words = list of word strings
        """
        net_tags = []
        for i in words:
            word_tag = self.lex.get_tag(i)
            if word_tag == "0":
                print "word unknown"
            else:
                net_tag = self.lex_net_matrix.get_v_tag(word_tag)
                self.network.set_activation(net_tag, 1.0)
                net_tags.append(net_tag)
        self.network.update()
        if cfg.hlearn:
            self.network.update_links(net_tags)
        
        
    def get_activated_word(self):
        """returns the word associated with the highest activated concept
        """                    
        return None
    
    
    def get_activated_prototype(self):
        """returns the prototype perceptual object associated with the highest activated concept
        """                    
        return None
    
    def name_object(self, object_data):
        """ returns the associated word for given object data
            spreading activation through network is taken into account
            strength of association matrix determines activation of nodes
        """
        cs_tags = self.cs.get_closest_concept_tags_domains(object_data) # get cs tag for each domain
        return self.get_word2(cs_tags)
    
    
    def name_object_alt(self, object_data):
        """ returns the associated word for given object data
            activation of SAN is based on distance from object to all prototypes
            spreading activation through network is taken into account
            strength of association matrix determines activation of nodes
        """
        cs_distances = self.cs.get_distance(object_data)
        for i in cs_distances[0]:   # assuming one domain only, change this for multidomain use
            self.cs_cs.set_activation(i[0], i[1])           # set activation for given percept
        self.cs_cs.update()                                 # propagate activation in cs_cs
        self.propagate_cs_to_lex()                          # propagate activations from cs_cs to lex_lex
        self.lex_lex.update()                               # propagate activation in lex_lex
        word = self.lex_lex.get_activated_node().tag        # get the highest activated word
        self.cs_cs.reset()                                  # reset cs_cs network
        self.lex_lex.reset()                                # reset lex_lex network
        return word
    
    
    def name_object_2nd_best(self, object_data):
        """ returns the associated word for given object data
            spreading activation through network is taken into account
            strength of association matrix determines activation of nodes
        """
        cs_tags = self.cs.get_closest_concept_tags_domains_2nd_best(object_data) # get cs tag for each domain
        return self.get_word2(cs_tags)
    
    
    def name_object_related(self, object_data):
        """ returns a related word for given object data
            spreading activation through network is taken into account
            strength of association matrix determines activation of nodes
        """
        cs_tags = self.cs.get_closest_concept_tags_domains(object_data) # get cs tag for each domain
        return self.get_word2_related(cs_tags)
    
    
    def get_word(self, cs_tag):
        """ returns the associated word for a given cs_tag
            spreading activation is not used
        """
        return self.cs_lex.get_v_tag(cs_tag)    # returns word_tag based on strongest connection
    
    
    def get_word2(self, cs_tags):
        """ returns the associated word for a given cs_tags
            spreading activation through network is taken into account
            strength of association matrix determines activation of nodes
        """
        for i in cs_tags:
            self.cs_cs.set_activation(i, 1.0)               # set activation for given percept
        self.cs_cs.update()                                 # propagate activation in cs_cs
        self.propagate_cs_to_lex()                          # propagate activations from cs_cs to lex_lex
        self.lex_lex.update()                               # propagate activation in lex_lex
        word = self.lex_lex.get_activated_node().tag        # get the highest activated word
        self.cs_cs.reset()                                  # reset cs_cs network
        self.lex_lex.reset()                                # reset lex_lex network
        return word
    
    
    def get_word2_second_best(self, cs_tags):
        """ returns the 2nd best associated word for a given cs_tags
            spreading activation through network is taken into account
            strength of association matrix determines activation of nodes
        """
        for i in cs_tags:
            self.cs_cs.set_activation(i, 1.0)               # set activation for given percept
        self.cs_cs.update()                                 # propagate activation in cs_cs
        self.propagate_cs_to_lex()                          # propagate activations from cs_cs to lex_lex
        self.lex_lex.update()                               # propagate activation in lex_lex
        word = self.lex_lex.get_semi_activated_node().tag   # get the 2nd highest activated word
        self.cs_cs.reset()                                  # reset cs_cs network
        self.lex_lex.reset()                                # reset lex_lex network
        return word
    
    
    def get_word2_related(self, cs_tags):
        """ returns the associated word for a given cs_tags
            spreading activation through network is taken into account
            strength of association matrix determines activation of nodes
        """
        for i in cs_tags:
            self.cs_cs.set_activation(i, 1.0)               # set activation for given percept
        self.cs_cs.update()                                 # propagate activation in cs_cs
        self.propagate_cs_to_lex()                          # propagate activations from cs_cs to lex_lex
        self.lex_lex.update()                               # propagate activation in lex_lex
        #word = self.lex_lex.get_semi_activated_node().tag   # get the 2nd highest activated word
        word = self.lex_lex.get_related_active_node().tag   # probabilistically get an active related node
        self.cs_cs.reset()                                  # reset cs_cs network
        self.lex_lex.reset()                                # reset lex_lex network
        return word
        
    
    def get_percept(self, words):
        """ returns the associated percept for a given set of words
            spreading activation through network is taken into account
            strength of association matrix determines activation of nodes
        """
        #activate words, if non are known, end
        known_words = False
        for i in words:                 
            response = self.lex_lex.set_activation(i, 1.0)
            if response:
                known_words = response        
        if not known_words:     
            return "no_known_words"
        else:
            self.lex_lex.update()                               # propagate activation in lex_lex
            self.propagate_lex_to_cs()                          # propagate activations from lex_lex to cs_cs
            percept_tag1 = self.cs_cs.get_activated_node().tag  # get the highest activated percept_tag
            self.cs_cs.update()                                 # propagate activation in cs_cs
            percept_tag2 = self.cs_cs.get_activated_node().tag
#            if not (percept_tag1 == percept_tag2):
#                print "difference!" 
            self.cs_cs.reset()                                  # reset cs_cs network
            self.lex_lex.reset()                                # reset lex_lex network
            return self.cs.get_concept(percept_tag2) 

    
    def answer_gg(self, words, context):
        """ Guessing game answer. Agent uses the incoming word labels and the associated 
            concept to identify the topic from the context, 
            the presumed topic index is communicated to the other agent.
        """
        percept = self.get_percept(words)
        if percept == "no_known_words":
            return percept
        else:
            context_distances = []
            for i in context:
                distance = auks.calculate_distance(i, percept.get_data())
                context_distances.append(distance)
            return [auks.posMin(context_distances), percept.tag]
        

    def propagate_cs_to_lex(self):
        """ propagates activation from cs_cs to lex_lex through cs_lex matrix
        """
        for i in self.cs_cs.nodes:
            weights = self.cs_lex.get_v_tag_values(i.tag)
            for x, j in enumerate(weights):
                try:
                    self.lex_lex.nodes[x].activation = self.lex_lex.nodes[x].activation + (j[1] * i.activation)
                except IndexError:
                    pass
                if self.lex_lex.nodes[x].activation > 1.0:  # pruning
                    self.lex_lex.nodes[x].activation = 1.0
                if self.lex_lex.nodes[x].activation  < 0.0:
                    self.lex_lex.nodes[x].activation  = 0.0
                
                
    def propagate_lex_to_cs(self):
        """ propagates activation from lex_lex to cs_cs through cs_lex matrix
        """
        for i in self.lex_lex.nodes:
            weights = self.cs_lex.get_h_tag_values(i.tag)
            for x, j in enumerate(weights):
                self.cs_cs.nodes[x].activation = self.cs_cs.nodes[x].activation + (j[1] * i.activation)
                if self.cs_cs.nodes[x].activation > 1.0:  # pruning
                    self.cs_cs.nodes[x].activation = 1.0
                if self.cs_cs.nodes[x].activation  < 0.0:
                    self.cs_cs.nodes[x].activation  = 0.0
    
    
    def increase_strength(self, word_tag, cs_tag, amount = cfg.word_learning_rate):
        """ increases the strength of the link between word_tag and cs_tag
        """
        self.cs_lex.increase_strength(word_tag, cs_tag, amount)
        
        
    def decrease_strength(self, word_tag, cs_tag, amount = cfg.word_learning_rate):
        """ decreases the strength of the link between word_tag and cs_tag
        """
        self.cs_lex.decrease_strength(word_tag, cs_tag, amount)
        
        
    def get_network_labels(self):
        """returns a list with the labels with the highest association for each node in the agents network
        """
        labels = []
        for i in self.network.nodes:
            labels.append(self.lex.get_word(self.lex_net_matrix.get_h_tag(i.tag)))
        return labels
        
        
    def get_percepts_and_words(self):
        """returns a list with percepts + highest activated word
        """
        percepts = self.cs.get_cs2()
        for i in percepts:
            word = self.get_word2([i[0]])
            i[0] = word
        return percepts
    
        