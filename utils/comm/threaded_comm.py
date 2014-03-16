#!/usr/bin/python
# -*- coding: utf-8 -*-

# LightHead is a programm part of CONCEPT, a HRI PhD project at the University
#  of Plymouth. LightHead is a Robotic Animation System including face, eyes,
#   head and other supporting algorithms for vision and basic emotions.
# Copyright (C) 2010-2011 Frederic Delaunay, frederic.delaunay@plymouth.ac.uk

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
