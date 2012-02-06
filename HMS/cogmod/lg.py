# simple language games
import random as ran
import auks, cfg, agent, data, inout, som3
import globals as gl
import time
from PyQt4.QtCore import *
from PyQt4.QtGui import *



def run_language_game(n_cycles, context_size, n_agents, thread=None):
    """ runs a series of language games with a population of agents
    """
    count = 0
    global_guessing_succes = []
    global_success_words = []
    while count < cfg.replicas:
        
        if cfg.training_data == 0:
            training_data = auks.generate_training_data(n_cycles, context_size)
        elif cfg.training_data == 1:
            training_data = auks.generate_training_data_objects(n_cycles, context_size)
        elif cfg.training_data == 2:
            training_data = auks.generate_training_data_wavelength(n_cycles, context_size)
            
        # create population
        population = []
        while len(population) < n_agents:
            ag = agent.Agent("agent" + str(len(population)), cfg.base, cone_proportions = auks.get_cone_proportions())
            load_base(ag)
            ag.pretrained_discrimination = True
            ag.has_run_lg_games = True
            population.append(ag)
        gl.cycle = 0
        gl.words_in_world = []
        gl.gg_succcess = []
        gl.successfull_words = []

        while gl.cycle < n_cycles:
            agents = ran.sample(population, 2)
            guessing_game(agents[0], agents[1], training_data[gl.cycle], ran.randint(0, context_size-1))
            
            gl.gg_succcess.append(agents[1].guessing_success)
            gl.successfull_words.append(calc_average_success_words(population, gl.cycle))
            
            gl.cycle += 1                  
            
            if thread and thread.stop:
                break

            if gl.cycle % 100 == 0:
                if thread:
                    thread.queue.put_nowait(gl.gg_succcess)
                    #thread.emit(SIGNAL("update(PyQt_PyObject)"), agents[1].guessing_success)
                print gl.cycle
        
        count += 1
        global_guessing_succes.append(gl.gg_succcess)
        global_success_words.append(gl.successfull_words)
        print "replica " + str(count) + " gg_success=" + str(agents[1].guessing_success)
        for i in population:
            inout.save_knowledge(i)
        inout.write_out("words_in_world", gl.words_in_world)
    inout.write_out(gl.gnuplot_title + "_all_data", global_guessing_succes)
    if thread:
        thread.emit(SIGNAL("stop(PyQt_PyObject)"), agents[1].guessing_success)
    return [[auks.calc_mean(global_guessing_succes), gl.gnuplot_title], [auks.calc_mean(global_success_words), "successful words"]]



def run_guessing_game(n_cycles, context_size, thread=None):
    """ runs a guessing game for a number of cycles
    """
    count = 0
    test_succes = []
    while count < cfg.replicas:
        gl.agent2 = agent.Agent("agent2", cfg.base)
        if cfg.training_data == 0:
            training_data = auks.generate_training_data(n_cycles, context_size)
        elif cfg.training_data == 1:
            training_data = auks.generate_training_data_objects(n_cycles, context_size)
        gl.agent1 = agent.Agent("agent1", cfg.base)
        for i in cfg.teacher_data:
            gl.agent1.learn_concept(i)
        inout.save_knowledge(gl.agent1)
        gl.cycle = 0
        gl.counter = 0
        
        while gl.cycle < n_cycles:
            guessing_game(gl.agent1, gl.agent2, training_data[gl.cycle], ran.randint(0, context_size-1))
            gl.agent2.test_succes.append(gl.agent2.guessing_success)
            gl.cycle += 1
        
            if thread and thread.stop:
                break
                                   
            if gl.cycle % 100 == 0:
                if thread:
                    thread.emit(SIGNAL("update(PyQt_PyObject)"), gl.agent2.guessing_success)
                print gl.cycle
        print "replica " + str(count+1) + " gg_success=" + str(gl.agent2.guessing_success)
        test_succes.append(gl.agent2.test_succes)
        count += 1

    inout.save_knowledge(gl.agent1)
    inout.save_knowledge(gl.agent2)
    inout.write_out("teacher-learner_", [auks.calc_mean(test_succes)])
    inout.write_out(gl.gnuplot_title + "_all_data", test_succes)
    if thread:
        thread.emit(SIGNAL("stop(PyQt_PyObject)"), gl.agent2.guessing_success)
    return [auks.calc_mean(test_succes), gl.gnuplot_title]





def run_discrimination_game(n_cycles, context_size, ag = None):
    """ runs a discrimination game for a number of cycles
    """
    count = 0
    output = []
    if not ag:
        ag = agent.Agent("agent")
    while count < 1:
        if cfg.training_data == 0:
            training_data = auks.generate_training_data(n_cycles, context_size)
        elif cfg.training_data == 1:
            training_data = auks.generate_training_data_objects(n_cycles, context_size)
        elif cfg.training_data == 2:
            training_data = auks.generate_training_data_wavelength(n_cycles, context_size)
        gl.cycle = 0
        discrimination_success = []
        while gl.cycle < n_cycles:
            discrimination_game(ag, training_data[gl.cycle], ran.randint(0, context_size-1))
            discrimination_success.append(ag.discrimination_success)
            gl.cycle += 1
#            if gl.cycle % 100 == 0:
#                print gl.cycle
        print "replica " + str(count+1) + " disc_success=" + str(ag.discrimination_success)
        output.append(discrimination_success)
        count += 1
    name = "_replicas=" + str(cfg.replicas)+ "_cycle=" + str(cfg.n_cycles) + "_dist=" + str(cfg.sample_minimum_distance)
    #inout.write_output("discrimination_game_" + name, output)
    inout.save_knowledge(ag)
    return len(ag.cs.concepts)


def load_base(ag):
    if cfg.base == "dg":
        cfg.agent_plot_cs = False
        run_discrimination_game(cfg.dg_base_n, cfg.context_size, ag)
    if cfg.base == "kmeans":
        agent_number = ag.agent_name[-1]
        dat = inout.read_file_csv("resources/centroids" + agent_number + ".csv")
        ag.load_percepts(dat)
    if cfg.base == "som":
        som = som3.Som(4, 4, 3)
        som.run()
        ag.load_som(som)


def discrimination_game(agent1, context, topic_index):
    """ Discrimination game in which an agent has to distinguish the topic
        from the context. The game succeeds if the agent has a concept 
        which uniquely matches the topic and no other stimuli from the context.
        If this is not the case, a new concept is build, or the existing concepts
        are shifted.
        context = sets of data [ [[v1, v2, v3]], [[v1, v2, v3]], ...]
    """
    a1_context = agent1.perceive_context(context)
    
    # if agent knowledge is empty, create new percept and concept
    if len(agent1.cs.concepts) == 0:
        cs_tag = auks.generateRandomTag(6)
        agent1.cs.create_pconcept(cs_tag, a1_context[topic_index])
        answer = cs_tag
    else:
        best_matching_percepts = []
        for i in a1_context:
            best_matching_percepts.append(agent1.cs.get_closest_pc(i))
            
        # determine the outcome of the discrimination game
        if best_matching_percepts.count(best_matching_percepts[topic_index]) == 1:
            agent1.n_success_dg += 1.0
            answer = best_matching_percepts[topic_index]
        else:
            # if agent discrimination success is below threshold a new percept is created
            if agent1.discrimination_success < cfg.adapt_threshold:
                cs_tag = auks.generateRandomTag(6)
                agent1.cs.create_pconcept(cs_tag, a1_context[topic_index])
                answer = cs_tag
            # else, the best matching percept is shifted towards the topic
            else:
                cs_tag = best_matching_percepts[topic_index]
                agent1.cs.get_concept(cs_tag).add_data(a1_context[topic_index])
                answer = cs_tag
        agent1.n_discrimination_games += 1
        agent1.discrimination_success = agent1.n_success_dg/agent1.n_discrimination_games
    return answer



def guessing_game(agent1, agent2, context, topic_index):
    """ Guessing game which is played by two agents. Agent1 knows the topic, finds the closest
        matching concept and communicates the label with the strongest association to agent2.
        Agent2 uses this label and the associated concept to identify the topic from the context.
        If agent2 is able to identify the topic correctly, the guessing game succeeds.
    """
    
    a1_context = agent1.perceive_context(context)
    a2_context = agent2.perceive_context(context)

    a1_cs_tag = agent1.get_closest_percept(a1_context[topic_index])
    a1_word = agent1.get_word(a1_cs_tag)
    a2_guessing_game_answer = agent2.answer_gg(a1_word, a2_context)  
    
    # if agent2 correctly points to the topic the guessing game succeeds
    if a2_guessing_game_answer[0] == topic_index:
        guessing_game_result = 1
        agent1.increase_strength(a1_word, a1_cs_tag)
        agent2.increase_strength(a1_word, a2_guessing_game_answer[1])
        agent2.cs.get_concept(a2_guessing_game_answer[1]).add_data(a2_context[topic_index])
        agent1.lex.update_word_success(a1_word) # update word success
        agent2.lex.update_word_success(a1_word) # update word success

    # if agent2 does not know the communicated word
    elif a2_guessing_game_answer == "unknown_word":
        guessing_game_result = 0
        if not agent2.pretrained_discrimination:
            a2_cs_tag = discrimination_game(agent2, a2_context, topic_index)
        else:
            a2_cs_tag = agent2.get_closest_percept(a2_context[topic_index])
        word = agent2.lex.add_word(a1_word)                     # create word in lexicon
        agent2.cs_lex.add_link(a2_cs_tag, word.tag)             # add link between lex and cs node

    # if agent2 knows the label, but points to the wrong topic
    else:
        guessing_game_result = 0
        agent1.decrease_strength(a1_word, a1_cs_tag)
        agent2.decrease_strength(a1_word, a2_guessing_game_answer[1])  
        if not agent2.pretrained_discrimination:
            a2_cs_tag = discrimination_game(agent2, a2_context, topic_index)
        else:
            a2_cs_tag = agent2.get_closest_percept(a2_context[topic_index])               
        agent2.cs_lex.add_link(a2_cs_tag, agent2.lex.get_word_tag(a1_word))

                
    # statistics
    agent2.n_guessing_games += 1
    if guessing_game_result:
        agent2.n_success_gg += 1
    agent2.guessing_success = (agent2.n_success_gg * 1.0)/agent2.n_guessing_games
    agent1.lex.update_word_use(a1_word) # update word success
    agent2.lex.update_word_use(a1_word) # update word success
    
    
    
    
def calc_average_success_words(population, cycle):
    succ_words = 0
    for i in population:
        succ_words += i.lex.calc_successful_words(cycle)
    return succ_words/(len(population)*1.0)