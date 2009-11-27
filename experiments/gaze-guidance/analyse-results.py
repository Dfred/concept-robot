#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, os.path, math
from optparse import OptionParser

HELP="For unknown answer from the participant,"
"please use the character 'x'. See also option --fill-gaps"
UNKNOWN='x'

def get_dist(ref, data):
    """compute euclydian distance"""
    x = abs(ref%10 - data%10)
    y = abs(ref/10 - data/10)
    return math.sqrt(x**2 + y**2), x, y

def force_load(fo_data):
    """returns a list of integers read from an open file (Universal mode only),
    appending only 'UNKNOWN' entries, otherwise a ValueError is raised"""
    data, line = [], 1
    for n in fo_data:
        try:
            data.append(int(n))
        except ValueError:
            if n.strip() != UNKNOWN:
                raise ValueError, "%s: the %ith line is invalid." % \
                    (fo_data.name, line)
            data.append(n)
        line +=1
    return data

def grid_error(ref, data):
    """compute location-wise error:
    the euclydian distance for each participant answer."""
    grid = [0] * 100
    for i in xrange(len(ref)):
        grid[ref[i]] += type(data[i]) != type(UNKNOWN) and \
            get_dist(ref[i], data[i])[0] or 0
    return grid
        

# set commandline options

parser = OptionParser("%prog [options] reference data."+HELP)
parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                  default=False, help="print extended info")
parser.add_option("-l", "--no-label", action="store_false", dest="label",
                  default=True, help="don't print label")
parser.add_option("-x", "--horizontal", action="store_true", dest="horizontal",
                  default=False, help="show horizontal error")
parser.add_option("-y", "--vertical", action="store_true", dest="vertical",
                  default=False, help="show vertical error")
parser.add_option("-a", "--all", action="store_true", dest="show_all",
                  default=False, help="show all errors")
parser.add_option("-s", "--only-side", action="store_true", dest="side",
                  default=False, help="display only sideview results.")
parser.add_option("-f", "--only-front", action="store_true", dest="front",
                  default=False, help="display only frontview results.")
parser.add_option("-g", "--grid", action="store_true", dest="grid",
                  default=False, help="draw error for each cell of the grid.")
parser.add_option("-m", "--mean", action="store_true", dest="mean",
                  default=False, help="get the mean score for each participant")
parser.add_option("-F", "--fill-gaps", action="store_true", dest="fix_file",
                  default=False, help="compute mean error to fill gaps.")
#parser.add_option("-S", "--spss-format", action="store_true", dest="spps_out",
#                  default=False, help="format output for spss.")

# check options and arguments

(options, args) = parser.parse_args()
if len(args) < 2:
    parser.print_usage()
    exit(-1)

if options.show_all:
    options.horizontal = options.vertical = options.grid = True

# read reference file and data file

ref = [int(n) for n in file(args[0])]

try:
    data = [int(n) for n in file(args[1], 'rU')]
except ValueError:
    if options.fix_file:
        data = force_load(file(args[1], 'rU'))
    else:
        print args[1], ": error parsing file"
        exit(-1)

# safety checks

length_ref, length_data = len(ref), len(data)
if length_ref != length_data:
    print args[1], "length mismatch (%i against %i lines)" % lengths
    exit(-1)

unknown = [ entry for entry in data if type(entry) == type(UNKNOWN) ]

error = 0
x_error, y_error = ([], [])
for i in xrange(length_ref):
    if type(data[i]) != type(ref[i]):
        continue
    diff, x, y = get_dist(ref[i], data[i])
    error += options.mean and diff/length_data or diff 
    x_error.append(x)
    y_error.append(y)

error += error/(length_ref) * len(unknown)

# DISPLAY # LABEL # ORIENTATION # rubbish
info=os.path.basename(args[1]).replace('.','-',1).split('-')

if options.side and info[2] != '45':
    print ""
    exit(0)
if options.front and info[2] != '0':
    print ""
    exit(0)

if options.verbose:
    print info[0], info[2]+'°',
if options.label:
    print info[1], '\t', error, '\t'

if options.horizontal:
    print sum(x_error),
    if options.verbose: print (min(x_error),max(x_error)), x_error
if options.vertical:
    print sum(y_error),
    if options.verbose: print (min(y_error), max(y_error)), y_error
if options.grid:
    g_error = grid_error(ref, data)
    if options.verbose:
        for i in xrange(0,9):
            print g_error[i*10:i*10+9]
    else:
        print g_error
if options.verbose:
    print unknown and str(len(unknown))+" fixed" or ""
print ""
