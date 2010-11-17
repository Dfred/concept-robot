# lg.py
# language game module

from __future__ import division
import random as ran
import time
import gnuplot_out as go
from PyQt4.QtCore import *
import agent, auks, cfg, inout, data
import globals as gl


def run_discrimination_game(n_cycles, context_size):
    """ runs a discrimination game for a number of cycles
    """
    count = 0
    output = []
#    output2 = []
    while count < cfg.replicas:
        agent1 = agent.Agent("agent", "learner")
        if cfg.training_data == 0:
            training_data = auks.generate_training_data_colour(n_cycles, context_size)
        elif cfg.training_data == 2:
            training_data = auks.generate_training_data_colour_shape(n_cycles, context_size)
        elif cfg.training_data == 3:
            training_data = auks.generate_training_data_artificial(n_cycles, context_size)
        gl.cycle = 0
        discrimination_success = []
        n_concepts = []
        while gl.cycle < n_cycles:
            discrimination_game(agent1, training_data[cycle], ran.randint(0, context_size-1))
            discrimination_success.append(agent1.discrimination_success)
            n_concepts.append(agent1.cs.count_successfull_concepts(0.2))
            gl.cycle += 1
            if gl.cycle % 100 == 0:
                print gl.cycle
        print "replica " + str(count+1) + " disc_success=" + str(agent1.discrimination_success)
        output.append(discrimination_success)
#        output2.append(n_concepts)
        count += 1
    name = "_replicas=" + str(cfg.replicas)+ "_cycle=" + str(cfg.n_cycles) + "_dist=" + str(cfg.sample_minimum_distance)
    inout.write_output("discrimination_game_" + name, output)
#    inout.write_output("n_concepts", output2)
#    inout.save_matrix(agent1, "cs_cs", agent1.cs_cs.matrix)
#    inout.save_matrix(agent1, "cs_lex", agent1.cs_lex)
#    inout.save_matrix(agent1, "lex_lex", agent1.lex_lex.matrix)
    
    
def run_guessing_game(thread, n_cycles, context_size):
    """ runs a guessing game for a number of cycles
    """
    count = 0
    output = []
    test_succes = []
    while count < cfg.replicas:
        gl.agent2 = agent.Agent("agent2", "learner")
        if cfg.training_type == "c1":   # rgb colour data
            if cfg.training_data == 0:
                training_data = auks.generate_training_data_colour(n_cycles, context_size)
                gl.agent1 = agent.Agent("agent1", "teacher", ["l", data.colour_data])
            elif cfg.training_data == 2:
                training_data = auks.generate_training_data_colour_shape(n_cycles, context_size)
                gl.agent1 = agent.Agent("agent1", "teacher", data.la_colour_shape)
            elif cfg.training_data == 3:
                training_data = auks.generate_training_data_artificial(n_cycles, context_size)
                gl.agent1 = agent.Agent("agent1", "teacher", data.artificial_data2)
        if cfg.training_type == "c2":   # hsv colour data
                training_data = auks.generate_training_data_colour(n_cycles, context_size, "hsv")
                gl.agent1 = agent.Agent("agent1", "teacher", ["l", data.colour_data_hsv])
        gl.cycle = 0
        guessing_success = []
        test_success = []
        while gl.cycle < n_cycles:
            guessing_game(gl.agent1, gl.agent2, training_data[gl.cycle], ran.randint(0, context_size-1))
            if cfg.test_type == "direct":
                gl.agent2.test_succes.append(test_knowledge(gl.agent1, gl.agent2, cfg.n_tests))
            elif cfg.test_type =="language game":
                gl.agent2.test_succes.append(gl.agent2.guessing_success)
            gl.cycle += 1
            
            # visuals
            if cfg.show_in_panda:
                if thread.stop:
                    break
                thread.emit(SIGNAL("update()"))
                time.sleep(0.02)
                                   
            if gl.cycle % 100 == 0:
                print gl.cycle
        print "replica " + str(count+1) + " gg_success=" + str(gl.agent2.guessing_success)
        test_succes.append(gl.agent2.test_succes)
        count += 1
#    name = "learning=" + str(cfg.associative_word_learning) + "_context=" + str(cfg.context_size) + "_replicas=" + str(cfg.replicas)+ "_cycle=" + str(cfg.n_cycles) + "_dist=" + str(cfg.sample_minimum_distance)
#    inout.write_output("guessing_game_" + name, output)
#    inout.write_output("test_success_" + name, success_output)
#    inout.save_matrix(gl.agent2.agent_name, "cs_cs", gl.agent2.cs_cs.matrix)
#    inout.save_matrix(gl.agent2.agent_name, "cs_lex", gl.agent2.cs_lex)
#    inout.save_matrix(gl.agent2.agent_name, "lex_lex", gl.agent2.lex_lex.matrix)
    inout.save_knowledge(gl.agent2)
    inout.write_out("teaching=" + cfg.teaching_type + " test=" + cfg.test_type, [auks.calc_mean(test_succes)])
    return [[auks.calc_mean(test_succes), "teaching=" + cfg.teaching_type + " test=" + cfg.test_type]]
    
    


def guessing_game(agent1, agent2, context, topic_index):
    """ Guessing game which is played by two agents. Agent1 knows the topic, finds the closest
        matching concept and communicates the label with the strongest association to agent2.
        Agent2 uses this label and the associated concept to identify the topic from the context.
        If agent2 is able to identify the topic correctly, the guessing game succeeds.
    """
    #a1_cs_tag= discrimination_game(agent1, context, topic_index)
    #a1_cs_tag = agent1.cs.get_closest_concept_tag(context[topic_index]) # no discrimination game for teacher
    a1_cs_tags = agent1.cs.get_closest_concept_tags_domains(context[topic_index]) # get cs tag for each domain
    if cfg.alternate_words:
        if len(a1_cs_tags) == 2:
            a1_cs_tags = [a1_cs_tags[ran.randint(0,1)]]
    a1_words = agent1.get_word2(a1_cs_tags)
#    agent1.used_words.append(a1_words)
    a2_guessing_game_answer = agent2.answer_gg([a1_words], context)
    
    # if agent2 correctly points to the topic the guessing game succeeds
    if a2_guessing_game_answer[0] == topic_index:
        guessing_game_result = 1
        agent2.increase_strength(a1_words, a2_guessing_game_answer[1])
        agent2.cs.get_concept(a2_guessing_game_answer[1]).add_data(context[topic_index])
        #agent2.cs.get_concept(a2_guessing_game_answer[1]).move_to(context[topic_index])
        
        if cfg.associative_object_learning:
            if len(context[topic_index]) == 2:  # if there are two percepts
                agent2.learn_percept_association(context[topic_index])

    # if agent2 does not know the communicated word
    elif a2_guessing_game_answer == "no_known_words":
        guessing_game_result = 0
        # add communicated word to lexicon
        a2_cs_tag = discrimination_game(agent2, context, topic_index)
        agent2.lex.add_word(a1_words)                     # create word in lexicon
        agent2.lex_lex.create_node(a1_words)              # create lex node in lex_lex matrix
        agent2.lex_lex.add_link(a1_words, a1_words)    # add link between lex and lex node
        agent2.cs_lex.add_link(a2_cs_tag, a1_words)       # add link between lex and cs node


    # if agent2 knows the label, but points to the wrong topic
    else:
        guessing_game_result = 0
        agent2.decrease_strength(a1_words, a2_guessing_game_answer[1])
        a2_cs_tag = discrimination_game(agent2, context, topic_index)       # get best cs tag
        #word = a1_words[ran.randint(0, len(a1_words)-1)]                    # if multiple words, a random one is chosen                           
        agent2.cs_lex.add_link(a2_cs_tag, a1_words)
                
    # statistics
    agent2.n_guessing_games += 1
    if guessing_game_result:
        agent2.n_success_gg += 1
    agent2.guessing_success = agent2.n_success_gg/agent2.n_guessing_games
        
        
    
def discrimination_game(agent, context, topic_index):
    """ Discrimination game in which an agent has to distinguish the topic
        from the context. The game succeeds if the agent has a concept 
        which uniquely matches the topic and no other stimuli from the context.
        If this is not the case, a new concept is build, or the existing concepts
        are shifted.
        context = sets of data [  [[ "domain", [ [d1, value], [d2, value], ..., [dn, value] ]], ..., ]]
                               [  [["c", [ ["r",1.0], ["g",0.0], ["b",0.0]]]]]
    """
    # if agent knowledge is empty, create new percept and concept
    if agent.cs.concepts == []:
        cs_tag = auks.generateRandomTag(6)
        agent.cs.create_pconcept(cs_tag, context[topic_index])
        agent.cs_cs.create_node(cs_tag)              # create cs node in cs_cs matrix
        agent.cs_cs.add_link(cs_tag, cs_tag)         # add link between cs and cs nod
        answer = cs_tag
    else:
        best_matching_percepts = []
        for i in context:
            best_matching_percepts.append(agent.cs.get_closest_concept_tag(i))
            
        # determine the outcome of the discrimination game
        if best_matching_percepts.count(best_matching_percepts[topic_index]) == 1:
            success = True
            agent.n_success_dg += 1.0
            answer = best_matching_percepts[topic_index]
            agent.cs.set_concept_disc_use(best_matching_percepts[topic_index], 1)
        else:
            agent.cs.set_concept_disc_use(best_matching_percepts[topic_index], 0)
            # if agent discrimination success is below threshold a new percept is created
            if agent.discrimination_success < cfg.adapt_threshold:
                cs_tag = auks.generateRandomTag(6)
                agent.cs.create_pconcept(cs_tag, context[topic_index])
                agent.cs_cs.create_node(cs_tag)              # create cs node in cs_cs matrix
                agent.cs_cs.add_link(cs_tag, cs_tag)         # add link between cs and cs nod
                answer = cs_tag
            # else, the best matching percept is shifted towards the topic
            else:
                cs_tag = best_matching_percepts[topic_index]
                agent.cs.get_concept(cs_tag).add_data(context[topic_index])
                #agent.cs.get_concept(cs_tag).move_to(context[topic_index])
                answer = cs_tag
        agent.n_discrimination_games += 1
        agent.discrimination_success = agent.n_success_dg/agent.n_discrimination_games
    return answer
            
            
def test_knowledge(agent1, agent2, n_tests):
    """ Test the knowledge of an agent. A random test sample is drawn, and both agents name it
        using the closest matching word label. If the word labels match the test is successful
        success rate is returned
    """
    counter, success = 0, 0
    while counter < n_tests:
        sample = auks.generate_training_data_colour(1, 1)
        a1_cs_tag = [agent1.cs.get_closest_concept_tag(sample[0][0])]
        a2_cs_tag = [agent2.cs.get_closest_concept_tag(sample[0][0])]
        a1_word = agent1.get_word2(a1_cs_tag)
        a2_word = agent2.get_word2(a2_cs_tag)
        if a1_word == a2_word:
            success += 1
        counter +=1
    return success/n_tests
        
        
        
        
        
        
            
