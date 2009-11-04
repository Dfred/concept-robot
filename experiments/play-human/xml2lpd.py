#!/usr/bin/python

# lightbot performance data from xml (script_template.xsd)
#
# uses expat (no validation).

import xml.parsers.expat
import math
import sys


fps = None
human_data = {}         # key: time(in s), value specific head/eye/face/..
current_eyes = [0,0,1,0,1,0,1,0,0]



def set_dialogue(attrs):
    global fps
    fps = int(attrs['fps'])

def set_cstate(attrs):
    pass

def set_phgs(attrs):
    """Get orientation axis and angle."""
    value = 'head %i' % (int(attrs['direction']), None)
    human_data[float(attrs['startTime'])/fps] = value

def set_pems(attrs):
    """Eye Orientation."""
    a, d = int(attrs['angle']), float(attrs['distance'])
    current_eyes[1] += math.cos(a)*d
    current_eyes[7] += math.sin(a)*d
    value = 'eyes '+ ' '.join(['%.3f' % v for v in current_eyes])
    human_data[float(attrs['startTime'])/fps] = value



verbose = False
functions = {
    #        "cState": set_cstate,
    #        "phgs": set_phgs,
        "pems": set_pems,
        "dialogue": set_dialogue
        }

# main handler functions
def start_element(name, attrs):
    try:
        functions[name](attrs)
        if verbose:
            print name, attrs
    except KeyError, e:
        name = "[unimplemented %s]" % e
        if verbose > 1:
            print name, attrs

def end_element(name):
    pass


def char_data(data):
    data =  data.strip()
    #    if (data):
    #        print '`--', repr(data)


def main():
    try:
        global verbose
        verbose = sys.argv[1][0] == '-' and sys.argv[1].count('v')
        if verbose:
            sys.argv.pop(1)
        xml_fname = sys.argv[1]
        out_fname = len(sys.argv) > 2 and sys.argv[2]
    except IndexError:
        print sys.argv[0],": [-v[v] (verbose)] xml_file out_file (or none for stdout)"
        exit(-1)

    parser = xml.parsers.expat.ParserCreate()
    parser.buffer_text = True
    parser.StartElementHandler  = start_element
    parser.EndElementHandler    = end_element
    parser.CharacterDataHandler = char_data
    try:
        xml_file = file(xml_fname)
        parser.ParseFile(xml_file)
    except Exception, e:
        print "Something's wrong with l."+str(parser.CurrentLineNumber), ":", e
        if verbose and xml_file:
            xml_file.seek(parser.ErrorByteIndex+2)      #XXX: this +2 may change
            print '`-->',xml_file.readline()
        exit(-1)
        
    try:
        out_file = out_fname and open(out_fname, 'w') or sys.stdout
    except IOError:
        print "could not open file", out_fname, "using standard output"
        out_file = sys.stdout

    for time in sorted(human_data.keys()):
        data = human_data[time]
        line = "%.3f:%s\n" % (time, data)
        out_file.write(line)
    if out_fname :
        out_file.close()
    print "done"

        
__name__ == '__main__' and main()
