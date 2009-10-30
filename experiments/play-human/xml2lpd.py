#!/usr/bin/python

# lightbot performance data from xml (script_template.xsd)
#
# uses expat (no validation).

import xml.parsers.expat
import sys


class Dialogue():
    """Static Class, we don't really need to create an instance."""
    fps = None
    # each data is a dictionnary with time as a key (in s.)
    eye_data = {}       # value: ()
    face_data = {}      # value: () 
    head_data = {}      # value: ()
    speech_data = {}    # value: ()



def set_dialogue(attrs):
    Dialogue.fps = int(attrs['fps'])

def set_cstate(attrs):
    pass

def set_phgs(attrs):
    """Get orientation axis and angle."""
    value = ( int(attrs['direction']), None )
    Dialogue.head_data[float(attrs['startTime'])/Dialogue.fps] = value

def set_pems(attrs):
    """Eye Orientation."""
    value = ( int(attrs['angle']), float(attrs['distance']) )
    Dialogue.eye_data[float(attrs['startTime'])/Dialogue.fps] = value

functions = {
#             "cState": set_cstate,
             "phgs": set_phgs,
             "pems": set_pems,
             "dialogue": set_dialogue
             }

# main handler functions
def start_element(name, attrs):
    try:
        functions[name](attrs)
        print name, attrs
    except KeyError, e:
#        print "[unimplemented %s]" % e
        pass

def end_element(name):
    pass

def char_data(data):
    data =  data.strip()
#    if (data):
#        print '`--', repr(data)



def main():
    try:
        xml_file = file(sys.argv[1])
    except IndexError:
        print "xml file argument needed"
        exit(-1)

    try:
        encoding = sys.argv[2]
    except IndexError:
        encoding = None

    parser = xml.parsers.expat.ParserCreate(encoding)
    parser.buffer_text = True
    parser.StartElementHandler = start_element
    parser.EndElementHandler = end_element
    parser.CharacterDataHandler = char_data
    try:
        parser.ParseFile(xml_file)
    except Exception, e:
        print "Something's wrong with l."+str(parser.CurrentLineNumber), ":", e
        exit(-1)
    xml_file.close()


__name__ == '__main__' and main()
