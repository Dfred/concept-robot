# lexicon.py
import auks, som3, cfg
from xml.etree import ElementTree as ET


class Lexicon():
    """ lexicon
    """
    
    def __init__(self):
        """ initiate variables 
        """
        self.words = []
        self.word_tags = []
        self.word_coordinates = []
        if cfg.som_representation:
            self.som = self.train_som()
        
        
    def train_som(self):
        return som3.Som(100, 100, 5)
        
        
    def new_word(self):
        if not cfg.som_representation:
            word_tag = auks.generateRandomWord(6)
            new_word = Word(word_tag, 0)
            self.words.append(new_word)
        else:
            word_coors = []
            check_word = True
            while check_word:
                word_coors = auks.generateRandomCoors(5)
                node1 = self.som.find_winner(word_coors)
                word_tag = "word" + str(node1[1]) + str(node1[2])
                if word_tag not in self.word_tags:
                    check_word = False
                self.word_coordinates.append(word_coors)
                self.word_tags.append(word_tag)
            new_word = Word(word_tag, word_coors)
            self.words.append(new_word)
        return new_word
    
    
    def add_word(self, word_coors):
        if cfg.som_representation:
            node1 = self.som.find_winner(word_coors)
            word_tag = "word" + str(node1[1]) + str(node1[2])
            new_word = Word(word_tag, word_coors)
            self.words.append(new_word)
            self.word_tags.append(new_word.tag)
            self.word_coordinates.append(word_coors)
            return new_word
        else:
            new_word = Word(word_coors, 0)
            self.words.append(new_word)
            return new_word
        
    
    def check_word(self, word_tag):
        """ checks if a word is in the lexicon
        """
        answer = False
        for i in self.words:
            if i == word_tag:
                answer = True
        return answer
    
    
    def get_word(self, word_tag):
        word = "unknown"
        for i in self.words:
            if i.tag == word_tag:
                word = i
        return word
    
    
    def get_word_tag(self, word_coors):
        if cfg.som_representation:
            node1 = self.som.find_winner(word_coors)
            word_tag = "word" + str(node1[1]) + str(node1[2])
            return word_tag
        else:
            return word_coors
        
        
    def get_lex(self):
        all = []
        for i in self.words:
            all.append([[i.tag, i.coordinates, i.success/(i.use*1.0)]])
        all.append([self.calc_successful_words(cfg.n_cycles)])
        return all
        
        
    def get_xml(self):
        """ returns self content as xml
        """
        lex_root = ET.Element("LEXICON")
        for i in self.words:
            lex_root.append(i.get_xml())
        n_succesful = ET.SubElement(lex_root, "n_successful")
        n_succesful.text = str(self.calc_successful_words(cfg.n_cycles))
        return lex_root
    

    def update_word_use(self, word_tag):
        for i in self.words:
            if i.tag == word_tag:
                i.use +=1 
    
    
    def update_word_success(self, word_tag):
        for i in self.words:
            if i.tag == word_tag:
                i.success +=1
                
                
    def calc_successful_words(self, cycle, threshold = cfg.successful_word_threshold):
        n_successful = 0
        for i in self.words:
            if ((i.success/(i.use*1.0)) > threshold) and (i.use/(1.0*(cycle+1)) > cfg.successful_word_min_use):
                n_successful += 1
        return n_successful
        
        
class Word():
    
    def __init__(self, tag, coordinates, success = 0):
        """ initiate variables 
        """
        self.tag = tag
        self.coordinates = coordinates
        self.use = 0
        self.success = success
        
        
    def get_xml(self):
        """ returns self content as xml
        """
        pconcept_root = ET.Element(self.tag, coordinates = str(self.coordinates), success = str(self.success/(self.use*1.0)) )
        return pconcept_root
    
    
    
def load_xml(file_name):
    """ returns a new lexicon loaded from an xml file
    """
    tree = ET.parse(file_name)
    element = tree.getroot()
    lex_elem = element.find('LEXICON')
    new_lex = Lexicon()
    for i in lex_elem:
        if i.tag != "n_successful":
            new_word = Word(i.tag, i.attrib["coordinates"], success = i.attrib["success"])
            new_lex.words.append(new_word)
            new_lex.word_tags.append(i.tag)
    return new_lex


