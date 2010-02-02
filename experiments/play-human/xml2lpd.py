#!/usr/bin/python

# lightbot performance data from xml (script_template.xsd)
#
# uses expat (no validation).

import xml.parsers.expat
import math, random
import sys


fps = None
human_data = {}         # key: time(in s), value specific head/eye/face/..
eyes_rot_vect = [0.0,0,0.0]


def set_dialogue(attrs):
    global fps
    fps = int(attrs['fps'])

def set_phgs(attrs):
    """Translate head movements."""
    """protocol: """
    st, et = int(attrs['startTime']), int(attrs['endTime'])
    value = 'head %i' % (int(attrs['direction']), None)
    human_data[float(attrs['startTime'])/fps] = value

def set_cstate(attrs):
    """Set complex facial expressions"""
    """protocol: f_expr id intensity duration"""
    st, et = int(attrs['startTime']), int(attrs['endTime'])
    intensity = random.uniform(.3, .6)
    duration = (float(et-st)/fps)
    f_expr = attrs['state'].strip().replace(' ', '_')
    human_data[float(st)/fps] = "f_expr %s %.3f %.3f" % (f_expr,
                                                         intensity,
                                                         duration)
    human_data[(float(st)/fps)+duration] = "f_expr %s %.3f %.3f" % ('neutral',
                                                                    0,
                                                                    duration)

def set_pfe(attrs):
    """Translate facial expressions:"""
    """protocol: f_expr id intensity duration"""
    st, et = int(attrs['startTime']), int(attrs['endTime'])
    intensity = random.uniform(.3, .6)
    duration = (float(et-st)/fps)
    human_data[float(st)/fps] = "f_expr %s %.3f %.3f" % (attrs['expression'],
                                                         intensity,
                                                         duration)
    human_data[(float(st)/fps)+duration] = "f_expr %s %.3f %.3f" % ('neutral',
                                                                    0,
                                                                    duration)

def set_pbl(attrs):
    """Translate blinks."""
    """protocol: blink intensity"""
    st, et = int(attrs['startTime']), int(attrs['endTime'])
    human_data[float(st)/fps] = "blink %.3f" % (float(et-st)/fps)

def set_pems(attrs):
    """Translate eye movements."""
    """protocol: eyes rot_axis_X rot_axis_Y rot_axis_Z angle_radians duration"""
    st, et = int(attrs['startTime']), int(attrs['endTime'])
    a, d = int(attrs['angle']), float(attrs['distance'])
    x = math.cos(math.radians(360-(a-90)) )*d
    y = math.sin(math.radians(360-(a-90)) )*d
    if not x:
        eyes_rot_vect[0] = 0
    else:
        eyes_rot_vect[0] += x
    if not y:
        eyes_rot_vect[2] = 0
    else:
        eyes_rot_vect[2] += y
    value = "eyes % .3f .0 % .3f %.2f %.3f" %(eyes_rot_vect[0],eyes_rot_vect[2],
                                              d, float(et-st)/fps)
    human_data[float(st)/fps] = value



verbose = False
functions = {
    "cState": set_cstate,
    #        "phgs": set_phgs,
    "pfe" : set_pfe,
    "pbl" : set_pbl,
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
    if verbose:
        print "done"

        
__name__ == '__main__' and main()
