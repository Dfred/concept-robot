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
