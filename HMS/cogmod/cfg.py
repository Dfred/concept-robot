
import data

interactions_per_agent = 5000
n_agents = 10                        # number of agents in the population
n_cycles = (n_agents * interactions_per_agent)/2.0
replicas = 1


#language game learning
base = "dg"                         # base knowledge: dg = discrimination game, kmeans = kmeans cluster data, som = som data
dg_base_n = 1000                    # if dg is base, number of games used to train
context_size = 3                    # number of stimuli in the context, including the topic
adapt_threshold = .9
word_learning_rate = .1
lateral_inhibition = 1
training_data = 2                   # 0 = colour only; 1 = objects, 2 = wavelength
sample_minimum_distance = 40         # minimum distance between stimuli in the context
teacher_data = data.object_data     # teacher starting knowledge [colour_data, object_data]

#lexicon
som_representation = False          # use som representation of words in lexicon
successful_word_threshold = .8      # threshold which determines if word is successful
successful_word_min_use = .01       # minimal percentage use of words to be counted as successful

# experimental settings
cone_proportions = [1.0, 1.0, 1.0]    # specifies agents cone proportions [s, m, l]
#cone_proportions = [0.33, 0.33, 0.33]    # specifies agents cone proportions [s, m, l]
#cone_proportions = [0.1, 0.45, 0.45]    # specifies agents cone proportions [s, m, l]
use_cone_opponency = False               # speciefies if cone opponency is used

#misc
save_agent_xml = True               # saves agent into an xml file
agent_plot_cs = True                # plots the CS of an agent in an 3D plot


# gnuplot plotting options
set_value = False            # displays end value in the plot


# may need to be modified
root_dir = '/home/joachim/PhD@Plymouth/Concept_project/workspace/cogmod2_0.31/'
vis_dir = '/home/fred/Work/concept-robot/utils/vision'


# graphical config
use_gui = True

#cam_resolution = (0, (960,544))     
cam_resolution = (0, (640,480))

detect_faces = False
detect_edge = False
gaze_follows_target = False
neck_follows_target = False
histogram_filter = False

canny_threshold1 = 50

# gaze and neck tuning
gaze_tune_x = 50
gaze_tune_y = 50
neck_tune_x = 50
neck_tune_y = 50
