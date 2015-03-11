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

# configuration file

# teaching
teacher_type = "a"            # type of teacher; "a" = artificial, "h" = human
teaching_type = "direct instruction"     # "direct instruction" or "language game"

# training data
n_cycles = 2000                  # number of training interactions
training_type = "c2"           # type of training data, "c1" = rgb_colour, "c2" = hsv_colour, "a1" = random artificial, "a2" = fixed artificial
SAN_clusters = False          # specifies is there are clusters generated in the SAN

# testing
n_tests = 10                   # number of tests ran
test_type = "language game"         # type of test; "language game" = Language game like fashion (context + topic, agent needs to point to topic based on given word)
                              # "direct" = direct fashion (1 object, both agents give their name for it)
test_2nd_word = False         # if True, tested agent is allowed to name the two best fitting words
correct = False               # if True, the teaching agent corrects the learning agent when the test is wrong by offering a learning experience
                                
# replicas
replicas = 1                  # number of replicas


#visuals
show_in_panda = False         # show agents percepts in panda world


# SA network
firing_threshold = 0.50
decay = 0.75
sensitivity = 1.0
new_link_strength = 0.1       # default strength of a new link
fan_out_constraint = 0        #TODO: proper implementation, check for number of connections is not right at the moment  # prevents nodes with the set number of connections to spread
distance_constraint = 3       # number of connections to which spreading activation is constrained

# Associative learning
associative_word_learning = True    # use associative learning
associative_object_learning = False    # use associative learning
learning_rate = 0.05            # learning rate

#language game learning
context_size = 4               # number of stimuli in the context, including the topic
adapt_threshold = 0.9
word_learning_rate = 0.1
move_learning_rate = 0.3             # learning rate determines how much categories shift
lateral_inhibition = 1
training_data = 0               # 0 = colour only; 1 = shape only; 2 = colour and shape; 3 = artificial domains
sample_minimum_distance = 0.35   # minimum distance between stimuli in the context
alternate_words = 0


# various
no_dim_match_penalty = 2        # sets a distance penalty if no dimensions match for 