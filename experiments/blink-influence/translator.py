#!/usr/bin/python
# -*- coding: utf-8 -*-

################################################################################
# This software is provided for academic research only: it is OSS but not GPL!
# In such a case, you can redistribute this software and/or modify it,
# provided you do not modify this license. Any other use is not permitted.

# ARAS is the open source software (OSS) version of the basic component of
# LightHead's software suite. 

# ARAS stands for Abstract Robotic Animation System, and features actuator,
# sensor, animation and remote management high-level interfaces.
# In particular, ARAS helps animating a head (virtual or physical), provides
# supporting algorithms for vision and hearing, as well as contributions from
# other scholars.
# Copyright 2009 - Frédéric Delaunay: dr.frederic.delaunay@gmail.com

# This software is the low-level Human-Robot-Interaction part of the CONCEPT
# project, which took place at the University of Plymouth (UK).
# The project stemed from by Frédéric Delaunay's PhD, himself under the
# supervision of professor Tony Belpaeme. The PhD project started in late 2008
# and ended in late 2011 but this part of the software is still maintained.
# Visit http://www.tech.plym.ac.uk/SoCCE/CONCEPT/ for more information.

# This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  General Public License for more details.
################################################################################

__author__ = "Frédéric Delaunay"
__credits__ = [""]
__license__ = "GPL"

import sys
import math

FOCAL_DIST = 1.2                                        # in meters
FPS = 24
E_FIX = (                                              # eye fix
  .3,                                                   # cos (horizontal)
  .3, )                                                 # sin (vertical)
H_FIX = (                                              # head affine fix
  .075, .25)
H_Y_FACTOR = .5


class Script(object):
  """
  """

  SEPARATOR = ','
  MAXSPLIT = 9

  def __init__(self, filepath, utf8=False):
    self.file = file(filepath, 'r', 1)
    self.buff = None
    self.lineno = 0
    self.utf8 = utf8

  def __del__(self):
    if hasattr(self, 'file'):
      self.file.close()

  def read_line(self):
    line = self.file.readline()
    if not line:
      return None
    if self.utf8:
      line = line.decode("utf-8")
      if line[0] == u'\ufeff':
        line = line[1:]
    self.lineno += 1
    line = line.strip()
    return line

  def skip_to(self, lineno):
    while self.lineno < lineno:
      self.read_line()

  def next(self):
    """Switch to next line.
    """
    line = self.read_line()
    while line is not None:
      if ( line.startswith('#') or len(line) == 0 or 
           line.startswith(self.SEPARATOR) ):
        line = self.read_line()
        continue
      return self.lineno, line.split(self.SEPARATOR, self.MAXSPLIT)
    return 'EOF'


class CF_Translator(object):
  """
  """

  def __init__(self, filepath):
    self.fpath = filepath
    self.ofpath = filepath[:filepath.rfind('.')]+'.player'
    self.script = Script(filepath, utf8=True)
    self.data = {}
    self.roll = 0                               # hack to keep head roll

  def cleanup(self):
    del self.script

  def get_Etransform_str(self, factor, direction):
    """Tries to match the *visual* rendering of the face with the participant's.
    CF uses visual analysis of eye gaze considering a front-facing face, so an
    affine fixing of cos&sin is used to match character/participant visuals.
    
    factor: normalized distance from the maximum position of eye gaze
    direction: 0: up, 270: right, 45: up-left..
    """
    if direction is None:
      return "[[0,%s,0]]" % FOCAL_DIST
    a = math.radians(int(direction))
    x,z = E_FIX[0]*math.cos(a)*factor, E_FIX[1]*math.sin(a)*factor
#    print direction,  factor, "->", "[%.3f,%.3f,%.3f]" % (x*FOCAL_DIST, 0, z*FOCAL_DIST)
    return "[%.3f,%.3f,%.3f]" % (x*FOCAL_DIST, 0, z*FOCAL_DIST) # relative

  def get_Stransform_str(self, factor, direction):
    """Tries to match the *visual* rendering of the face with the participant's.
    CF uses visual analysis of head gaze considering a front-facing face, so an
    affine fixing of cos&sin is used to match character/participant visuals.
    
    factor: normalized distance from the maximum position of head gaze
    direction: 0: up, 270: right, 45: up-left..
    """
    if direction is None:
      return "((0,0,0))"
    y = 0
    if '/' in direction:                                        # roll's after /
      direction, roll = direction.split('/')
      direction = direction[:-3]                                        # 'deg'
      y = math.radians(int(roll)) * H_Y_FACTOR
    a = math.radians(int(direction) + 90)
    x,z = math.sin(a)*factor, math.cos(a)*factor
    x,z = H_FIX[0] * x, H_FIX[1] * z 
    return "((%.3f,%.3f,%.3f))" % (x, y, z)

  def get_values(self, line):
    """Returns a single dict indexed by time of occurrence.
    """
    element = ''
    topic, t, dur, intens, att, sus, dec, dsc, nbr, garbage = line
    dsc = dsc.strip()
    t = float(t) / FPS
    key = topic.strip().upper()

    if t != ' -' :
      dur = float(dur) / FPS if dur != ' -' else None
    else:
      print "--- ignoring line:", line
      return

    if key.startswith("EXPRESSION"):
      i = 0
      element = '%s*%.3f' % (dsc, 1)
      self.data.setdefault(t,['',]*5)[4] += '|blink:expression-on'
      
    elif key.startswith("SPEECH"):
      i = 1
      element = dsc
      remains = [nbr,]
      remains.extend(garbage.split(','))
      while not element.endswith(u'”'):
        element += (', '+remains.pop(0))
      element = u'"%s"' % element[1:-1]
      self.data.setdefault(t,['',]*5)[4] += '|chat-gaze:speaking|blink:self-speech-on'
    elif key.endswith("MOVE"):
      i = key.startswith("HEAD")+2
      element2 = None
      if dsc.endswith("(Re-Center)"):
        element2 = self.get_Etransform_str(float(intens), None)
        dsc = dsc[:-12]                                 # remove "(Re-Center)"
        self.data.setdefault(t+dur,['',]*5)[i] += element2
        self.data.setdefault(t+dur,['',]*5)[4] += '|enable:chat-gaze'
      direction = dsc[:-3]                              # remove 'deg'
      element = ( self.get_Etransform_str(float(intens), direction) if i==2 else
                  self.get_Stransform_str(float(intens), direction) )
      if i==2:                                  # eye gaze
        self.data.setdefault(t,['',]*5)[4] +=  '|disable:chat-gaze'
      element += "/%.3f" % dur
    elif key == "HEAD STATE":
      i = 4
      if dsc.split()[0].lower() == 'stare':
        self.data.setdefault(t,['',]*5)[4] += '|disable:chat-gaze'
      elif dsc == "Looking Away":
        self.data.setdefault(t,['',]*5)[4] += '|blink:look-away-face'
      elif dsc == "Looking At":
        self.data.setdefault(t,['',]*5)[4] += '|blink:look-at-face'
    elif key == "MENTAL STATE":
      i = 4
      if dsc in ('on-locutor-speech', 'expression-off'):
        element = "blink:"+dsc
      else:
        element = "blink:new-mental-state"
    elif key == "BLINK":
      i = 4
      element = "blink:%s=[%s,%s,%s]" % (dsc,
                                         round(float(att)/FPS,3),
                                         round(float(sus)/FPS,3),
                                         round(float(dec)/FPS,3))
    else:
      print "--- unused line %i:" % self.script.lineno, dsc
      return
    if i == 4 and self.data.has_key(t) and self.data[t][i]:
      self.data[t][i] += '|'+element
    else:
      self.data.setdefault(t,['',]*5)[i] = element
 
  def run(self, skip_to=None):
    skip_to and self.script.skip_to(skip_to)
    line = self.script.next()
    while line != 'EOF':
      try:
        self.get_values(line[1])
      except StandardError,e:
        print "\n-- ERROR with line %i %s:" % line, e
        #import pdb; pdb.set_trace()
      line = self.script.next()
    self.write_player_script()

  def write_player_script(self):
    last_t = 0
    sorted_keys = sorted(self.data.keys())
    out = file(self.ofpath, "w")
    out.write("0 neutral;;[[0,%s,0]];((0,0,0));enable:chat-gaze;INIT\n" % FOCAL_DIST)
    for i,t in enumerate(sorted_keys):
      assert t - last_t >= 0, "negative time diff (%s - %s)" % (t,last_t)
      out.write(('%.3f %s;%s;%s;%s;%s;tag%i\n' % tuple([t-last_t]+self.data[t]+[i])).encode("utf8"))
      if last_t != t:
        last_t = t
    out.write('0 neutral/1.2;;[[0,%s,0]];((0,0,0));;END\n' % FOCAL_DIST)
    out.close()
    print "wrote file:", self.ofpath


if __name__ == "__main__":
  if len(sys.argv) < 2:
    print "filename to translate please!"
    exit(1)

  skip = len(sys.argv) > 2 and sys.argv[1].startswith('-s') and sys.argv.pop(1)
  try:
    m = CF_Translator(sys.argv[1])
  except StandardError,e:
    print e
    exit(2)
  try:
    m.run(skip and int(skip[2:]))
  except KeyboardInterrupt:
    print '\n--- user interruption ---'
  else:
    m.cleanup()
#  print 'done'
