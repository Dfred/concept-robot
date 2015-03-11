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

import time
import logging

from utils.comm import get_addrPort
from utils.comm_CHLAS_ARAS import ChlasCommTh
from utils import conf, LOGFORMATINFO
from RAS import REQUIRED_CONF_ENTRIES

LOG = None

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


class MonologuePlayer():
  """A simple player reading monologue file.
  """

  def __init__(self, addrPort, filepath):
    """
    """
    self.comm_expr = ChlasCommTh(get_addrPort(addrPort),
                                 fct_connected=self.connected,
                                 fct_disconnected=self.disconnected)
    #XXX: on_bad_command() could miss the 1st datablocks (although unlikely).
    setattr(self.comm_expr,'cmd_NACK',self.on_bad_command)
    self.script = Script(filepath)
    self.__wait_reply = True
    self.__running = False
    self.no_fail = False
    self.comm_expr.connect()

  def set_wait_reply(self, wait_flag):
    """
    """
    self.__wait_reply = wait_flag

  def launch(self, skip_to=None):
    """Awaits connection, then processes all of the monologue file.
    """
    skip_to and self.script.skip_to(skip_to)
    while not self.__running:     # waiting for connection
      print "waiting for connection"
      time.sleep(.5)
    pause, sent_t, recv_t = 0, 0, 0
    while self.__running:         # until disconnection or EOF
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
        LOG.debug('sending line #%i %sfor tag "%s"', lineno, 
                  "and waiting reply " if self.__wait_reply else "", tag)
        sent_t = time.time()
        if self.__wait_reply:
          self.comm_expr.sendDB_waitReply(datablock+';', tag)
        else:
          self.comm_expr.send_my_datablock(datablock, tag)
        recv_t = time.time()

  def cleanup(self):
    del self.script
    self.comm_expr.done()

  def on_bad_command(self, argline):
    LOG.error("command with tag '%s' has an error", argline)
    if self.no_fail:
      return
    self.__running = False

  def connected(self):
    LOG.debug("connected")
    self.__running = True

  def disconnected(self):
    LOG.debug("disconnected")
    self.__running = False


if __name__ == '__main__':
  import sys, logging
  from optparse import OptionParser

  parser = OptionParser("%s remote_addrPort script_path" % sys.argv[0])
  parser.add_option("-v", "--verbose", dest="verbosity", action='count',
                    default=0, help="start in debug mode")
  parser.add_option("-n", "--no-waitACK", dest="noACK", action="store_true", 
                    help="don't wait for ACK to send next datablock.")
  parser.add_option("-d", "--dont-stopNACK", dest="deaf", action="store_true", 
                    help="don't stop after receiving a NACK.")
  parser.add_option("-s", "--skip", dest="skip", type=int, default=None,
                    help="skip the 1st SKIP lines of the script.")
  opts, args = parser.parse_args()

  logging.basicConfig(level=[logging.WARNING,
                             logging.INFO,
                             logging.DEBUG][opts.verbosity],
                      **LOGFORMATINFO)
  LOG = logging.getLogger(__package__)

  conf.set_name('lighty')
  
  try:
    addrPort, filepath = args
  except:
    print "arguments required"
    sys.exit(1)
  m = MonologuePlayer(*args)                            # also loads conf

  if opts.skip:
    print "-- will start from line %i --" % opts.skip
  if opts.noACK:
    m.set_wait_reply(False)
    print "-- won't wait for ACK --"
  if opts.deaf:
    m.no_fail = True
    print "-- won't stop on NACK --"

  try:
    m.launch(opts.skip)
  except KeyboardInterrupt:
    print '\n--- user interruption ---'
  else:
    print '--- done ---'
  m.cleanup()
  print 'done'
