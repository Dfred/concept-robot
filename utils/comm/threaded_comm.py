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

"""
comm package for python (versions >= 2.6)

A template server and associated handler + client:
Provides socket-based communication (with logging support) and a convenient
way for handling word-based (text) application protocols.
Auto-selection of base classes from address family, port type and threading
information doesn't require child classes to use inheritance; see doc of
create_server() for more details

Overview:
* session.py, holds server classes connecting processes,
* presentation.py, holds application protocol classes,
* meta_session.py, allows grouping servers in a single process,
* __init__.py, interesting classes and logging management function.

TODO: document all use-cases.
"""

__author__    = "Frédéric Delaunay"
__license__   = "GPL"
__maintainer__= "Frédéric Delaunay"
__email__     = "delaunay.fr at gmail.com"
__credits__   = ["University of Plymouth and EPSRC"]

import sys
import time
import logging
import threading

from . import ASCIICommandClient

LOG = logging.getLogger(__package__)                      # main package logger

__NEED_WAIT_PATCH__ = sys.version_info[0] == 2 and sys.version_info[1] < 7


class ThreadedComm(ASCIICommandClient):
  """A communication class based on the comm protocol spawning its own thread.
  """

  CONNECT_TIMEOUT = 3

  def __init__(self, *args, **kwds):
    """Override BaseClient to manage threading.
    """
    super(ThreadedComm,self).__init__(*args, **kwds)
    self.connect_timeout = self.CONNECT_TIMEOUT
    self._thread_name = 'ThComm_default_name'
    self.__thread = None
    self.__event = None
    self.__working = False

  ##
  ## Threading specific
  ##

  @property
  def thread(self):
    return self.__thread

  @property
  def working(self):
    return self.__working

  def wait(self, timeout=None):                         #TODO: add event name
    """Wait for an event on the communication channel.

    Return: False if timeout elapsed, True otherwise
    """
    outtimed = True
    if timeout and __NEED_WAIT_PATCH__:
      t = time.time()                                   # for python < 2.7
    if self.__event:
      outtimed = self.__event.wait(timeout)
      self.__event.clear()
      if __NEED_WAIT_PATCH__:
        outtimed = timeout and (time.time()-t) < timeout or True
    return outtimed

  def unwait(self):                                     #TODO: add event name
    """Unblock threads blocked in wait().
    """
    if self.__event:
      self.__event.set()                                # unblock waiting thread

  def always_connected(self):
    """Loop on connect+work_loop which finishes by calling done() or on error.
    """
    while self.__working:
      self.connect_and_run()

  def done(self):
    """Unblocks always_connected().
    """
    self.__working = False

  def disconnect(self):
    """Terminate the connection.
    """
    self.__working = False
    name = self.__thread.getName()
    super(ThreadedComm,self).disconnect()
    LOG.debug("joining thread '%s'", name)
    self.abort()
    if not threading.current_thread() == self.__thread:
      self.__thread.join()
    self.set_threaded(False)
    LOG.debug('joined thread %s', self)

  ##
  ## Overrides
  ##

  def connect(self):
    if not self.__thread:                               ## 1st call
      self.connect_and_run()
    else:
      super(ThreadedComm,self).connect()                ## 2nd call (baseclass)

  def connect_and_run(self):
    """Connect to the remote server within the spawned thread.
    """
    assert not self.__thread, "thread %s still alive!" % self.__thread.getName()
    cnr = super(ThreadedComm,self).connect_and_run
    self.__thread= threading.Thread(target=cnr, name=self._thread_name)
    self.__event = threading.Event()
    self.__working = True
    self.set_threaded(True)
    self.__thread.start()

  def handle_connect_error(self, e):
    """See handle_connect_timeout.
    """
    super(ThreadedComm, self).handle_connect_error(e)
    self.handle_connect_timeout()

  def handle_connect_timeout(self):
    """Sleep for a second if connection initialization is in timeout status.
    """
    super(ThreadedComm, self).handle_connect_timeout()
    time.sleep(1)
