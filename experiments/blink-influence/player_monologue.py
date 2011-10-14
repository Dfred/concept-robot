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

import time
import math
import random

from HMS.expression_player import Behaviour_Builder
from utils import Frame, conf, LOGFORMATINFO
from utils.FSMs import SMFSM


class Utterances(object):
  """
  """

  def __init__(self, filepath):
    self.file = file(filepath, 'r', 1)
    self.next_time = None
    self.buff = None
    self.lineno = 0

  def __del__(self):
    if hasattr(self, 'file'):
      self.file.close()

  def read_line(self):
    line = self.file.readline()
    if not line:
      return None
    self.lineno += 1
    return line.strip()

  def next(self):
    """Switch to next line. Also, check self.lock() for deferred reading.
    """
    if not self.next_time:
      self.next_time = time.time()
    if time.time() >= self.next_time:
      line = self.read_line()
      if line == None:
        return 'EOF'
      while line.startswith('#') or len(line) == 0:
        line = self.read_line()
        if line == None:
          return 'EOF'
      print "current time", time.time()
      try:
        min_dur, datablock = line.split(None,1)
      except ValueError:
        print "UTTERRANCES ERROR - line %i : '%s'" % (self.lineno, line)
        return None
      return (float(min_dur), datablock[:datablock.rindex(';')+1],
              datablock[datablock.rindex(';')+1:])
    return None

  def lock_for(self, duration):
    """Lock iterating over the file for duration seconds.
    """
    self.next_time = time.time() + duration
    print "next_time", self.next_time


class MonologuePlayer(Behaviour_Builder):
  """A simple player reading monologue file.
  """

  def read(self):
    """
    Switches to: SMFSM.STOPPED
    """
    if self.wait_reply:
      return
    line = self.utterances.next()
#    import pdb; pdb.set_trace()
    if line == 'EOF':
      return SMFSM.STOPPED
    if line:

      def got_reply(status, tag):
        self.wait_reply = False
        self.comm_expr.on_reply_fct(self.tag, None)
        self.utterances.lock_for(pause)

      pause, datablock, self.tag = line
      self.wait_reply = True
      self.comm_expr.on_reply_fct(self.tag, got_reply)
      self.comm_expr.send_my_datablock(datablock, self.tag)

  def search_participant(self):
    """
    Switches to: 'FOUND_PART'
    """
    self.faces = self.vision.find_faces()
    if self.vision.gui:
      self.vision.mark_rects(self.faces)
      self.vision.gui.show_frame(self.vision.frame)
    return self.faces and 'FOUND_PART' or None

  def adjust_gaze_neck(self):
    """
    Switches to: 'ADJUSTED'
    """
    eyes = self.vision.find_eyes([self.faces[0]])[0]
    center = Frame(((eyes[0].x + eyes[1].x)/2, (eyes[0].y+eyes[1].y)/2,
                    self.faces[0].w, self.faces[0].h))
    gaze_xyz = self.vision.camera.get_3Dfocus(center)
    neck = ((.0,.0,.0),(.0,.0,.0))
    # TODO: ideally, we would not have to set the neck if gaze is enough to
    #  drive the neck (an expr2 instinct could do it).
    if not self.vision.camera.is_within_tolerance(center.x, center.y):
      neck = (gaze_xyz,(.0,.0,.0))
    self.comm_expr.set_gaze(gaze_xyz)
    self.comm_expr.set_neck(*neck)
    tag = self.comm_expr.send_datablock('gaze_neck')
    self.comm_expr.wait_reply(tag)
    return 'ADJUSTED'

  def finish(self, name):
    """Called on FSM.STOPPED state.
    name: name of the machine.
    """
    del self.utterances
    return None

  def __init__(self, filepath):
    """
    """
    PLAYER_DEF= ( (SMFSM.STARTED, self.read),
                  (SMFSM.STOPPED, self.finish),
                )
    if conf.ROBOT['mod_vision']:
      FTRACKER_DEF = ( ((SMFSM.STARTED,'ADJUSTED'), self.search_participant),
                       ('FOUND_PART', self.adjust_gaze_neck),
                       (SMFSM.STOPPED, self.finish),
                     )
      Behaviour_Builder.__init__(self, [('player',PLAYER_DEF,None),
                                        ('tracker',FTRACKER_DEF,'player')],
                                 with_vision=True)
    else:
      Behaviour_Builder.__init__(self, [('player',PLAYER_DEF,None),],
                                 with_vision=False)

    self.utterances = Utterances(filepath)
    self.wait_reply = False

if __name__ == '__main__':
  conf.set_name('lightHead')
  conf.load()
  import sys, logging
  logging.basicConfig(level=logging.DEBUG,**LOGFORMATINFO)
  try:
    m = MonologuePlayer(sys.argv[1])                          # also loads conf
  except IndexError:
    print 'usage: %s monologue_file' % sys.argv[0]
    exit(1)
  m.run()
  m.cleanup()
  print 'done'
