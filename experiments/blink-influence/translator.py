#!/usr/bin/python
# -*- coding: utf-8 -*-

# LightHead programm is a HRI PhD project at the University of Plymouth,
#  a Robotic Animation System including face, eyes, head and other
#  supporting algorithms for vision and basic emotions.
# Copyright (C) 2010 Frederic Delaunay, frederic.delaunay@plymouth.ac.uk

#  This program is free software: you can redistribute it and/or
#   modify it under the terms of the GNU General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.

#  This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   General Public License for more details.

#  You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

__author__ = "Frédéric Delaunay"
__credits__ = [""]
__license__ = "GPL"

import sys
import math

FOCAL_DIST = 2                                          # in meters
FPS = 24


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
    self.lineno += 1
    line = line.strip()
    if self.utf8:
      line = line.decode("utf-8").encode("ascii","ignore")
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
    self.script = Script(filepath, utf8=True)
    self.data = {}
    self.focus = 0,0,0

  def cleanup(self):
    del self.script

  def get_transform(self, factor, direction):
    if not direction:
#      print self.focus
      self.focus = 0,0,0                                        #XXX: check
      return "((0,%s,0))" % FOCAL_DIST
    a = math.radians(direction -90)
    x,z = math.cos(a)*factor, math.sin(a)*factor
    focus = x*FOCAL_DIST, FOCAL_DIST, z*FOCAL_DIST
    self.focus = [ self.focus[i]+v for i,v in enumerate(focus) ]    #XXX: same
    return "[%s,%s,%s]" % focus

  def get_values(self, line):
    """Returns a single dict indexed by time of occurrence.
    """
    element = ''
    topic, t, dur, intens, att, sus, dec, dsc, nbr, garbage = line
    dsc = dsc.strip()
    t = float(t) / FPS
    key = topic.upper()
    if ' -' not in (t,dur):
      dur = float(dur) / FPS
    else:
      print "--- ignoring line:", line
      return
    if key.startswith("EXPRESSION"):
      i = 0
      element = '%s*%.3f' % (dsc, 1)
    elif key.startswith("SPEECH"):
      i = 1
      element = dsc
    elif key.endswith("MOVE"):
      i = key.startswith("eye")+2
      direction = None if dsc.endswith("Center)") else int(dsc[:-3])
      element = self.get_transform(float(intens), direction)
    elif key == "HEAD STATE":
      i = 4
      words = dsc.split()
      element = "chat-gaze:"+words[1].lower()
    elif key == "MENTAL STATE":
      i = 4
      element = "blink:"+dsc.lower()
    else:
      print "--- unused:", dsc
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
#        exit(3)
      line = self.script.next()
    self.write_player_script()

  def write_player_script(self):
    last_t = 0
    sorted_keys = sorted(self.data.keys())
    print "0 neutral/.001;;;;enable:chat-gaze;INIT"
    for i,t in enumerate(sorted_keys):
      assert t - last_t >= 0, "negative time diff (%s - %s)" % (t,last_t)
      infos = tuple([t-last_t]+self.data[t]+[i])
      print '%.3f %s;"%s";%s;%s;%s;tag%i' % infos
      if last_t != t:
        last_t = t


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
