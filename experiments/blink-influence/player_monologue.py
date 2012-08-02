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
import logging

from HMS.communication import MTExpressionComm
from utils import conf, LOGFORMATINFO


LOG = logging.getLogger(__package__)
noACK = False

class Script(object):
  """
  """

  def __init__(self, filepath):
    self.file = file(filepath, 'r', 1)
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

  def skip_to(self, lineno):
    while self.lineno < lineno:
      self.read_line()

  def next(self):
    """Switch to next line.
    """
    line = self.read_line()
    while line is not None:
      if line.startswith('#') or len(line) == 0:
        line = self.read_line()
        continue
      try:
        pause, datablock = line.split(None,1)
        pause = float(pause)
      except ValueError:
        LOG.error("BAD LINE #%i : '%s'", self.lineno, line)
        return None
      return self.lineno, pause, datablock
    return 'EOF'


class MonologuePlayer(object):
  """A simple player reading monologue file.
  """

  def run(self, skip_to=None):
    """Awaits connection, then processes all of the monologue file.
    """
    skip_to and self.script.skip_to(skip_to)
    while not self.running:     # waiting for connection
      time.sleep(.5)
    pause, sent_t, recv_t = 0, 0, 0
    while self.running:         # until disconnection or EOF
      if pause:
        delay = pause - (recv_t - sent_t)
        if delay < 0:
          LOG.warning("cannot match %ss pause (action took %.3fs, diff: %.3fs)",
                      pause, recv_t-sent_t, delay)
        else:
          LOG.debug('pausing for %.3fs (pause: %ss - action duration: %.3fs).',
                    delay , pause, recv_t - sent_t)
          time.sleep(delay)
      line = self.script.next()
      if line == 'EOF':
        return
      if line:
        lineno, pause, datablock = line
        datablock, tag = datablock.rsplit(';', 1)
        LOG.debug('sending line #%i and waiting reply for tag "%s"', lineno,tag)
        sent_t = time.time()
        if noACK:
          self.comm_expr.send_my_datablock(datablock+';'+tag)
        else:
          self.comm_expr.sendDB_waitReply(datablock+';', tag)
        recv_t = time.time()

  def cleanup(self):
    del self.script
    self.comm_expr.done()

  def on_bad_command(self, argline):
    LOG.error("command with tag '%s' has an error", argline)
    self.running = False

  def connected(self):
    self.running = True

  def disconnected(self):
    LOG.warning('disconnected from server')
    self.running = False

  def __init__(self, filepath):
    """
    """
    missing = conf.load(required_entries=('ROBOT','expression_server'))
    if missing:
      LOG.warning('\nmissing configuration entries: %s', missing)
      exit(1)

    self.running = False
    self.comm_expr = MTExpressionComm(conf.expression_server,
                                      connection_lost_fct=self.disconnected,
                                      connection_succeded_fct=self.connected)
    #XXX: on_bad_command() could miss the 1st datablocks (although unlikely).
    setattr(self.comm_expr,'cmd_NACK',self.on_bad_command)
    self.script = Script(filepath)
    self.wait_reply = False


if __name__ == '__main__':
  import sys, logging
  debug = len(sys.argv) > 2 and sys.argv[1].startswith('-v') and sys.argv.pop(1)
  logging.basicConfig(level=(debug and logging.DEBUG or logging.INFO),
                      **LOGFORMATINFO)

  skip = len(sys.argv) > 2 and sys.argv[1].startswith('-s') and sys.argv.pop(1)
  # noACK is global
  noACK = len(sys.argv) > 2 and sys.argv[1].startswith('-n') and sys.argv.pop(1)
  conf.set_name('lightHead')

  try:
    m = MonologuePlayer(sys.argv[1])                          # also loads conf
  except IndexError:
    print 'usage: %s monologue_file' % sys.argv[0]
    exit(1)
  try:
    m.run(skip and int(skip[2:]))
  except KeyboardInterrupt:
    print '\n--- user interruption ---'
  else:
    print '--- done ---'
  m.cleanup()
  print 'done'
