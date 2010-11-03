# lexicon.py


class Lexicon():
    """ lexicon
    """
    
    def __init__(self):
        """ initiate variables 
        """
        self.words = []
            
            
    def add_word(self, word_label):
        self.words.append(word_label)
        
    
    def check_word(self, word_label):
        """ checks if a word is in the lexicon
        """
        answer = False
        for i in self.words:
            if i == word_label:
                answer = True
        return answer
