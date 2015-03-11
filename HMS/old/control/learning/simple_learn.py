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

import sys, time
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import gnuplot_out as go
import random as ran
import cfg, agent, auks, inout, data, lg, graphic
import globals as gl


def run_simple_learn(thread=None):
    if cfg.teaching_type == "direct instruction":
        output = run_direct_instruction(thread)
    elif cfg.teaching_type == "language game":
        output = lg.run_guessing_game(thread, cfg.n_cycles, cfg.context_size)
    return output
        


def run_direct_instruction(thread):
    """ runs direct instruction from teaching agent to learning agent for given number of cycles
    """
    if cfg.teacher_type == "h":
        run_human_teaching(cfg.n_cycles)
    
    if cfg.teacher_type == "a":
        count = 0
        agent2_similarity = []
        agent2_test_succes = []
        while count < cfg.replicas:
            training_data = []
            if cfg.training_type == "a1":
                #generate_artificial_knowledge(n_dom, av_dimensions, avn_exemplars, av_words, av_associations, av_cluster_size = None)
                a_data = auks.generate_artificial_knowledge(1, 3, 10, 10, 3, 3)
                gl.agent1 = agent.Agent("agent1", "teacher", ('a', a_data))
                training_data = auks.generate_training_data_simple(cfg.n_cycles)
            elif cfg.training_type == "a2":
                a_data = auks.create_knowledge_with_a_data(data.artificial_percepts, data.artificial_san_percepts, data.artificial_words, data.artificial_san_words, data.artificial_matrix)
                gl.agent1 = agent.Agent("agent1", "teacher", ('a', a_data))
                training_data = auks.generate_training_data_simple(cfg.n_cycles)
            elif cfg.training_type == "c1":
                gl.agent1 = agent.Agent("agent1", "teacher", ('l', data.colour_data))
                training_dat = auks.generate_training_data_colour(cfg.n_cycles, 1)
                for i in training_dat:
                    training_data.append(i[0])  # remove one list level for compatibility
            elif cfg.training_type == "c2":
                gl.agent1 = agent.Agent("agent1", "teacher", ('l', data.colour_data_hsv))
                training_dat = auks.generate_training_data_colour(cfg.n_cycles, 1)
                for i in training_dat:
                    training_data.append(i[0])  # remove one list level for compatibility
            inout.save_knowledge(gl.agent1)
            gl.agent2 = agent.Agent("agent2", "learner")
            
            agent2_numbers = [["words","percepts"]]
            agent2_sim = []
            for x, i in enumerate(training_data):
                a1_word = gl.agent1.name_object(i)
                gl.agent2.learn_concept(a1_word, i)

                #learning
                if cfg.associative_word_learning:
                    a1_word_related = gl.agent1.name_object_related(i)
                    #print a1_word, a1_word_related
                    gl.agent2.learn_word_association(a1_word, a1_word_related)
                if cfg.associative_object_learning:
                    pass # to be implemented
                agent2_numbers.append([gl.agent2.n_words, gl.agent2.n_percepts])
                
                #testing
                if cfg.test_type == "direct": # direct test
                    gl.agent2.test_succes.append(run_objects_test(gl.agent1, gl.agent2, cfg.n_tests))
                elif cfg.test_type == "language game": # language game test
                    gl.agent2.test_succes.append(run_guessing_game_test(gl.agent1, gl.agent2, cfg.n_tests, cfg.context_size))
                agent2_sim.append(calc_similarity_agents(gl.agent1, gl.agent2))
                
                # visuals
                if cfg.show_in_panda:
                    if thread.stop:
                        break
                    thread.emit(SIGNAL("update()"))
                    time.sleep(0.05)
                    
                if x % 10 == 0:
                    print x
            count += 1
            agent2_similarity.append(agent2_sim)
            agent2_test_succes.append(gl.agent2.test_succes)
            print "replica " + str(count)
            
        # stats
        inout.save_knowledge(gl.agent2)
        inout.write_out("agent2_numbers", agent2_numbers)
        inout.write_out("teaching=" + cfg.teaching_type + " test=" + cfg.test_type + " 2nd word=" + str(cfg.test_2nd_word), [auks.calc_mean(agent2_test_succes)])
        #inout.write_out_average("agent2_test_correct_clusters=" + str(cfg.SAN_clusters) + "_domain=" + str(cfg.training_type) + "_alearning=" + str(cfg.associative_word_learning), agent2_correct)
        #inout.write_out_average("agent2_similarity_clusters=" + str(cfg.SAN_clusters) + "_domain=" + str(cfg.training_type) + "_alearning=" + str(cfg.associative_word_learning), agent2_similarity)
        #go.output([auks.calc_mean(agent2_correct)], "test success", "# interactions", "% correct", "agent2_test_succes")  
        #go.output([auks.calc_mean(agent2_comm_succes)], "communicative success", "# interactions", "% correct", "agent2_comm_succes")
        return [[auks.calc_mean(agent2_test_succes), gl.test_title], [auks.calc_mean(agent2_similarity), "similarity"]]
        
        
def run_objects_test(agent1, agent2, n_test_objects):
    """ runs tests between two agents, returns percentage correct
    """
    test_data = []
    if cfg.training_type == "a1":
        test_data = auks.generate_training_data_simple(n_test_objects)
    elif cfg.training_type == "c":
        test_dat = auks.generate_training_data_colour(n_test_objects, 1)
        for i in test_dat:
            test_data.append(i[0])  # remove one list level for compatibility
    n_correct = 0
    for i in test_data:
        if cfg.test_2nd_word and len(agent2.lex.words) > 1:
            a1_word = agent1.name_object(i)
            a2_answers = []
            a2_answers.append(agent2.name_object(i))
            a2_answers.append(agent2.name_object_2nd_best(i))
            if a1_word in a2_answers:
                n_correct += 1
        else:
#            a1_word = agent1.name_object_alt(i)
#            a2_word = agent2.name_object_alt(i)
            a1_word = agent1.name_object(i)
            a2_word = agent2.name_object(i)
            if a1_word == a2_word:
                n_correct += 1
            else:
                if cfg.correct:
                    agent2.learn_concept(a1_word, i)
    return n_correct/len(test_data)


def run_guessing_game_test(agent1, agent2, n_test_objects, context_size):
    """ runs guessing game tests between two agents, returns communicative success
        no learning
    """
    if cfg.training_data == 0:
        test_data = auks.generate_training_data_colour(n_test_objects, context_size)
    elif cfg.training_data == 2:
        test_data = auks.generate_training_data_colour_shape(n_test_objects, context_size)
    elif cfg.training_data == 3:
        test_data = auks.generate_training_data_artificial(n_test_objects, context_size)
    guessing_game_result = 0
    for i in test_data:
        topic_index = ran.randint(0, context_size-1)
        a1_cs_tags = agent1.cs.get_closest_concept_tags_domains(i[topic_index])
        a1_words = agent1.get_word2(a1_cs_tags)
        a2_guessing_game_answer = agent2.answer_gg([a1_words], i)
        
        if a2_guessing_game_answer[0] == topic_index:
            guessing_game_result += 1
    return guessing_game_result/n_test_objects


def calc_similarity_agents(agent1, agent2):
    """ calculates the difference between two agents knowledge structure
    """
    similarity = 0
    for i in agent2.cs.concepts:
        similarity += agent1.cs.get_closest_concept_tagsim(i.get_data())[1]
        #similarity += agent1.cs.get_closest_concept_tagdist(i.get_data())[1]
    return similarity/len(agent2.cs.concepts)
    
    
def run_human_teaching(n_training_objects):
    """ runs direct instruction with user input to learning agent
    """
    gl.agent2 = agent.Agent("agent2", "learner")
    app = QtGui.QApplication(sys.argv)
    myapp = graphic.human_teacher(gl.agent2)
    myapp.show()
    sys.exit(app.exec_())
                