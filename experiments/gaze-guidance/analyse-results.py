#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from optparse import OptionParser

def get_dist(ref, data):
    x = abs(ref%10 - data%10)
    y = abs(ref/10 - data/10)
    return (x == y and 1.5 *x or x+y, x, y)

def force_load(fo_data):
    data = []
    for n in fo_data:
        try:
            data.append(int(n))
        except ValueError:
            data.append(n)
    return data

def grid_error(ref, data):
    grid = [0] * 100
    for i in xrange(len(ref)):
        grid[ref[i]] += type(data[i]) != type('x') and get_dist(ref[i], data[i])[0] or 0
    return grid
        

parser = OptionParser("%prog [options] reference data")
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
parser.add_option("-F", "--fix-file", action="store_true", dest="fix_file",
                  default=False, help="compute mean error to fill gaps.")

(options, args) = parser.parse_args()
if options.show_all:
    options.horizontal = options.vertical = options.grid = True

ref = [int(n) for n in file(args[0])]

try:
    data = [int(n) for n in file(args[1])]
except ValueError:
    if options.fix_file:
        data = force_load(file(args[1]))
    else:
        print args[1], ": error parsing file"
        exit(-1)

lengths = (len(ref), len(data))
if lengths[0] != lengths[1]:
    print args[1], "length mismatch (%i against %i lines)" % lengths
    exit(-1)

unknown = [ entry for entry in data if type(entry) == type('x') ]

error = 0
x_error, y_error = ([], [])
for i in xrange(lengths[0]):
    if type(data[i]) != type(ref[i]):
        continue
    diff, x, y = get_dist(ref[i], data[i])
    error += diff
    x_error.append(x)
    y_error.append(y)

error += error/(lengths[0]) * len(unknown)

# DISPLAY # LABEL # ORIENTATION # rubbish
rindex = args[1].rfind('/') 
info=args[1][rindex >= 0 and rindex or 0:].replace('/','').replace('.','-',1).split('-')

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
