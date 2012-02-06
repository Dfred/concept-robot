
from xml.etree import ElementTree as ET
import colour_perception as cp
import cfg, cs, lexicon, matrix, auks, gnuplot_out


class Agent():
    """ Agent consisting of SA_network, conceptual space and lexicon
    """
    
    def __init__(self, name, base="cs", cone_proportions = cfg.cone_proportions):
        """ initiate variables 
            initial_knowledge = (type: l/a, data)
        """
        self.agent_name = name                  # agent name
        self.base = base                        # perceptual base of agent, "cs" is default
        self.pretrained_discrimination = False  # agent has learnt to discriminate
        self.cs = cs.CS()                       # agents conceptual space
        self.lex = lexicon.Lexicon()            # agents lexicon
        self.cs_lex = matrix.Matrix("cs_lex")   # concept-lexicon association matrix
        self.n_percepts = 0
        self.n_words = 0
        self.cone_proportions = cone_proportions # proportion of cone receptors: [S, M, L] -> adds up to 1
        
        #language game variables
        self.has_run_lg_games = False   # indicates if agent has run lg games, i.e. if it should have word labels
        self.n_discrimination_games = 0
        self.n_success_dg = 0
        self.discrimination_success = 0
        self.n_guessing_games = 0
        self.n_success_gg = 0
        self.guessing_success = 0
        self.test_succes = []
        
        
    def load_percepts(self, dat):
        """ load P_concepts based on given data
        """
        for i in dat:
            cs_tag = "no_tag"
            while ((cs_tag == "no_tag") or (cs_tag in self.cs.concepts)): # make sure the cs_tag is unique
                cs_tag = auks.generateRandomTag(6)
            self.cs.create_pconcept(cs_tag, i)
            
            
    def load_som(self, som):
        """ load a som which serves as basic perception
        """
        self.base = "som"
        self.som = som
        
        
    def perceive_context(self, context):
        """ perceive a given context, return a subjective version
        """
        response = []
        for i in context:
            if cfg.training_data == 2:
                if cfg.use_cone_opponency:
                    response.append([cp.cone_opponency(i[0][1][0], self.cone_proportions)])                
                else:
                    response.append([cp.response_to_wavelength(i[0][1][0], self.cone_proportions)])
        return response
            
        
        
    def perceive_wavelength(self, wavelength):
        """ perception function which calculates 
            the subjective perception for a given wavelength
        """
        pass
        
        
    def learn_concept(self, concept):
        word = concept[0]
        percept_data = concept[2]
        """ learn a concept (word + percept)
        """
        # if word is already know, update perceptual data
        if self.lex.check_word(word):
            cs_tag = self.cs_lex.get_h_tag(word)
            self.cs.get_concept(cs_tag).add_data(percept_data)
        
        # if word is not known, create new concept
        else:
            self.lex.add_word(word)                 # create word in lexicon
            cs_tag = "no_tag"
            while ((cs_tag == "no_tag") or (cs_tag in self.cs.concepts)): # make sure the cs_tag is unique
                cs_tag = auks.generateRandomTag(6)
            self.cs.create_pconcept(cs_tag, percept_data)      # create pconcept in CS  
            self.cs_lex.add_link(cs_tag, word)      # add link between lex and cs matrix
            
            self.n_percepts = len(self.cs.concepts)     # update numbers
            self.n_words = len(self.lex.words)
            
            
    def name_object(self, object_data):
        """ returns the associated word for given object data
            strength of association matrix determines activation of nodes
        """
        cs_tag = self.get_closest_percept(object_data)
        if self.has_run_lg_games:   # agent should have words
            return self.get_word(cs_tag)
        else:   
            return cs_tag
    
    
    def get_word(self, cs_tag):
        """ returns the associated word for a given cs_tag
        """
        if cs_tag not in self.cs_lex.horizontal_tags:
            word = self.lex.new_word()             # create word in lexicon
            self.cs_lex.add_link(cs_tag, word.tag)  # add link between lex and cs node
        else:
            word_tag = self.cs_lex.get_v_tag(cs_tag)    # returns word_tag based on strongest connection
            word = self.lex.get_word(word_tag)
        if cfg.som_representation:
            word_response = word.coordinates       # word is based on its coordinates
        else:
            word_response = word.tag               # word is based on tag
        return word_response
    
    
    def get_percept(self, word):
        """ returns the associated percept for the given word
            strength of association matrix determines activation of nodes
        """
        if word not in self.lex.words:
            return "unknown_word"
        else:
            percept_tag = self.get_percept_tag(word)
            return self.cs.get_concept(percept_tag)
    
    
    def get_percept_tag(self, word):
        """ returns the percept tag with highest association for given word
        """
        if cfg.som_representation:
            word_tag = self.lex.get_word_tag(word)
        else:
            word_tag = word
        return self.cs_lex.get_h_tag(word_tag)
    
    
    def get_closest_percept(self, dat):
        """ returns the percept tag that is closest to given data
        """
        if cfg.base != "som":
            percept_tag = self.cs.get_closest_pc(dat)
        else:
            node1 = self.som.find_winner(dat[0][1])
            percept_tag = "tag" + str(node1[1]) + str(node1[2])
        return percept_tag
    
    
    def answer_gg(self, word, context):
        """ Guessing game answer. Agent uses the incoming word labels and the associated 
            concept to identify the topic from the context, 
            the presumed topic index is communicated to the other agent.
        """
        percept_tag = self.get_percept_tag(word)
        if percept_tag == "label_unknown":
            return "unknown_word"
        else:
            distances = []
            for i in context:
                if cfg.base != "som":
                    distances.append(auks.calc_distance_euc2(i[0][1], self.cs.concepts[percept_tag].components[i[0][0]].coordinates))
                else:
                    distances.append(auks.calc_distance_euc2(i[0][1], self.som.get_node_weights(percept_tag)))
            return [auks.posMin(distances), percept_tag]
        
        
    def increase_strength(self, word_coors, cs_tag, amount = cfg.word_learning_rate):
        """ increases the strength of the link between word_tag and cs_tag
        """
        if cfg.som_representation:
            word_tag = self.lex.get_word_tag(word_coors)
        else:
            word_tag = word_coors
        self.cs_lex.increase_strength(word_tag, cs_tag, amount)
        
        
    def decrease_strength(self, word_coors, cs_tag, amount = cfg.word_learning_rate):
        """ decreases the strength of the link between word_tag and cs_tag
        """
        if cfg.som_representation:
            word_tag = self.lex.get_word_tag(word_coors)
        else:
            word_tag = word_coors
        self.cs_lex.decrease_strength(word_tag, cs_tag, amount)
        
        
    def save_xml(self, filename):
        """ saves the agent to an xml file
        """
        agent_root = ET.Element(self.agent_name)
        agent_root.append(self.cs.get_xml())
        agent_root.append(self.lex.get_xml())
        agent_root.append(self.cs_lex.get_xml())
        tree = ET.ElementTree(agent_root)
        tree.write("output/" + self.agent_name + "_" + filename + ".xml")
        
        
    def load_xml(self, file_name):
        """ load the agent from an xml file
        """
        tree = ET.parse(file_name)
        element = tree.getroot()
        self.agent_name = element.tag
        self.cs = cs.load_xml(file_name)
        self.lex = lexicon.load_xml(file_name)            
        self.cs_lex = matrix.load_xml(file_name)   
        self.n_percepts = len(self.cs.concepts)
        self.n_words = len(self.lex.words)
        
        
    def plot_cs(self):
        """ saves the agent CS into an 3D plot
        """
        dat = []
        for i in self.cs.get_cs():
            dat.append(list(i[0][1]))
        gnuplot_out.plot_CS(dat)
