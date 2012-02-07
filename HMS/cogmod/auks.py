import numpy, math, time
import random as ran
#import pycuda.gpuarray as gpuarray
#import pycuda.autoinit
#from pycuda.elementwise import ElementwiseKernel
import globals as gl
import cfg


# alphabet sets
consonant_set = ["B","C","D","F","G","H","J","K","L","M","N","P","Q","R","S","T","V","W"]
vowel_set = ["A","E","I","O","U"]
alphabet_set = ["a","b","c","d","e","f","g","h","i","j","k","l","m",\
                    "n","o","p","q","r","s","t","u","v","w","x","y","z"]
alphanumeric_set = ["a","b","c","d","e","f","g","h","i","j","k","l","m",\
                    "n","o","p","q","r","s","t","u","v","w","x","y","z",\
                    "1","2","3","4","5","6","7","8","9","0"]


def posMax(list):
    """ returns the index of the highest value of a given list
        if multiple highest values exist, the first is returned
    """
    m = list[0]
    index = 0
    for i, x in enumerate(list):
        if x > m:
            m = x
            index = i
    return index



def posMin(list):
    """ returns the index of the lowest value of a given list
        if multiple highest values exist, the first is returned
    """
    m = list[0]
    index = 0
    for i, x in enumerate(list):
        if x < m:
            m = x
            index = i
    return index


def generateRandomTag(length):
    """ generates a random alphanumeric tag with a given length 
    """
    i = 0
    tag = ""
    while i < length:
        tag += str((ran.choice(alphanumeric_set)))
        i += 1
    return tag


def generateRandomWord(length):
    """ generates a random word with a given length 
    """
    check = False
    while not check:
        i = 0
        word = ""
        while i < length :
            if i % 2 == 0:
                word += str(ran.choice(consonant_set))
            else:
                word += str(ran.choice(vowel_set))
            i += 1
        if word not in gl.words_in_world:   #check if word is unique
            gl.words_in_world.append(word)
            check = True
    return word


def generateRandomCoors(n):
    """ generates a list with n random ints
    """
    coors = []
    for i in range(0, n):
        coors.append(ran.randint(0, 10))
    return coors

    
def calc_distance_euc(x, x_sd, y):
    """ euclidean distance between x and y
        sd of x is taken into account
    """
    if len(x) != len(y):
        raise ValueError, "vectors must be same length"
    sum = 0
    for i in range(len(x)):
        if (x[i] + x_sd[i]) < y[i]:
            sum += ( x[i]+x_sd[i] -y[i])**2
        elif (x[i] - x_sd[i]) > y[i]:
            sum += ( x[i]-x_sd[i] -y[i])**2
        else:
            sum += 0
    return math.sqrt(sum)


def calc_distance_euc2(x, y):
    """ euclidean distance between x and y
    """
    if len(x) != len(y):
        raise ValueError, "vectors must be same length"
    sum = 0
    for i in range(len(x)):
        sum += ( x[i] -y[i])**2
    return math.sqrt(sum)


def calc_distance_euc_cuda(kernel, point1, point2):
    x_gpu = gpuarray.to_gpu(numpy.array([point2[0]]))
    y_gpu = gpuarray.to_gpu(numpy.array([point2[1]]))
    z_gpu = gpuarray.to_gpu(numpy.array([point2[2]]))
    result = gpuarray.empty_like(x_gpu)
    kernel(point1[0], point1[1], point1[2], x_gpu, y_gpu, z_gpu, result)
    return result.get()



def generate_training_data(n_sets, context_size):
    """ generates training data for language games in colour domain
    """
    training_dataset = []
    count = 0
    while count < n_sets:
        count2 = 0
        set = []
        while count2 < context_size:
            check = True
            while check:
                stimulus = [["rgb", [ran.random(), ran.random(), ran.random()]]]
                if set == []:
                    check = False
                else:   # check if distance is big enough
                    sequence = []
                    for i in set:
                        if cfg.sample_minimum_distance < calc_distance_euc2(i[0][1], stimulus[0][1]):
                            sequence.append("1")
                        else:
                            sequence.append("0")
                    if "0" not in sequence:
                        check = False
            set.append(stimulus)
            count2 += 1
        training_dataset.append(set)
        count += 1
    return training_dataset



def generate_training_data_wavelength(n_sets, context_size):
    """ generates training data for language games using wavelength ranging from 400 - 700
    """
    training_dataset = []
    count = 0
    while count < n_sets:
        count2 = 0
        new_set = []
        while count2 < context_size:
            check = True
            while check:
                stimulus = [["wav", [ran.randint(400,700)]]]
                if new_set == []:
                    check = False
                else:   # check if distance is big enough
                    sequence = []
                    for i in new_set:
                        if cfg.sample_minimum_distance < calc_distance_euc2(i[0][1], stimulus[0][1]):
                            sequence.append("1")
                        else:
                            sequence.append("0")
                    if "0" not in sequence:
                        check = False
            new_set.append(stimulus)
            count2 += 1
        training_dataset.append(new_set)
        count += 1
    return training_dataset




def generate_training_data_objects(n_sets, context_size):
    """ generates training data for language games in colour domain
    """
    training_dataset = []
    count = 0
    while count < n_sets:
        count2 = 0
        new_set = []
        while count2 < context_size:
            check = True
            while check:
                stimulus = [["hri", [ran.random(), ran.random(), ran.random(), ran.random(), ran.random(), ran.random(), ran.random()]]]
                if new_set == []:
                    check = False
                else:   # check if distance is big enough
                    sequence = []
                    for i in new_set:
                        if cfg.sample_minimum_distance < calc_distance_euc2(i[0][1], stimulus[0][1]):
                            sequence.append("1")
                        else:
                            sequence.append("0")
                    if "0" not in sequence:
                        check = False
            new_set.append(stimulus)
            count2 += 1
        training_dataset.append(new_set)
        count += 1
    return training_dataset


def get_cone_proportions():
    """generates agents cone proportions based on settings in cfg
    """
    if cfg.cone_proportions is "random":
        pr_s = 0.1
        pr_m = 0.9 * ran.random()
        pr_l = 0.9 - pr_m
        cone_proportion = [pr_s, pr_m, pr_l]
    elif cfg.cone_proportions is "random2":
        pr_s = ran.random()
        pr_m = (1 - pr_s) * ran.random()
        pr_l = (1 - pr_s) - pr_m
        cone_proportion = [pr_s, pr_m, pr_l]
    else:
        cone_proportion = cfg.cone_proportions
    return cone_proportion


def calc_mean(dat):
    """returns the mean values and SD for a collection of data lists
       dat = [ [x1,x2,...,xn], [y1, y2,...,yn]]
       return = [ [x_mean, sd], [y_mean, sd]]
    """
    tot = [0] * len(dat[0])
    mean = [0] * len(dat[0])
    for i in dat:
        for x, j in enumerate(i):
            mean[x] += j
    for x, i in enumerate(mean):
        mean[x] = mean[x]/len(dat)
        sd = 0
        for j in dat:
            sd += (j[x] - mean[x])**2
        sd = math.sqrt(sd/len(dat))
        tot[x] = [mean[x], sd]
    return tot