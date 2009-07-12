#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from optparse import OptionParser

def cmp(ref, data):
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

parser = OptionParser("%prog [options] reference data")
parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                  default=False, help="print extended info")
parser.add_option("-x", "--horizontal", action="store_true", dest="horizontal",
                  default=False, help="show horizontal error")
parser.add_option("-y", "--vertical", action="store_true", dest="vertical",
                  default=False, help="show vertical error")
parser.add_option("-a", "--all", action="store_true", dest="show_all",
                  default=False, help="show all errors")
parser.add_option("-f", "--fix-file", action="store_true", dest="fix_file",
                  default=False, help="compute mean error to fill gaps.")

(options, args) = parser.parse_args()
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
if lengths[0] != lengths[0]:
    print args[1], "length mismatch (%i against %i lines)" % lengths
    exit(-1)

error = 0
x_error, y_error = ([], [])
for i in xrange(lengths[0]):
    if type(data[i]) != type(ref[i]):
        continue
    diff, x, y = cmp(ref[i], data[i])
    error += diff
    x_error.append(x)
    y_error.append(y)

unknown = [ entry for entry in data if type(entry) != type(1) ]
error += error/(lengths[0]) * len(unknown)

# DISPLAY # LABEL # ORIENTATION # rubbish
info=args[1][args[1].rfind('/'):].replace('/','').replace('.','-',1).split('-')

if options.verbose:
    print info[0], info[2]+'°',
print info[1], "\t", error, "\t",
if options.show_all or options.horizontal:
    print sum(x_error),
    if options.verbose: print (min(x_error),max(x_error)),
if options.show_all or options.vertical:
    print sum(y_error),
    if options.verbose: print (min(y_error), max(y_error)),
if options.verbose:
    print unknown and str(len(unknown))+" fixed" or ""
print ""
