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

import sys, threading
import logging

from . import ASCIICommandClient

LOG = logging.getLogger(__package__)                      # main package logger

__NEED_WAIT_PATCH__ = sys.version_info[0] == 2 and sys.version_info[1] < 7


class ThreadedComm(ASCIICommandClient):
  """A communication class based on the comm protocol with threaded polling.
  """

  CONNECT_TIMEOUT = 3

  def __init__(self, server_addrPort, connection_succeded_function):
    super(ThreadedComm,self).__init__(server_addrPort)
    self.connect_timeout = self.CONNECT_TIMEOUT
    self.connect_success_function = connection_succeded_function
    # Threaded object manages the socket independently
    self.thread = threading.Thread(target=self.always_connected)
    self.event = threading.Event()
    self.working = True
    self.thread.start()

  def wait(self, timeout=None):                         #TODO: add event name
    """Wait for an event on the communication channel.

    Returns: False if timeout elapsed, True otherwise
    """
    outtimed = True
    if timeout and __NEED_WAIT_PATCH__:
      t = time.time()                             # for python < 2.7
    if self.event:
      outtimed = self.event.wait(timeout)
      self.event.clear()
      if __NEED_WAIT_PATCH__:
        outtimed = timeout and (time.time()-t) < timeout or True
    return outtimed

  def unblock_wait(self):                               #TODO: add event name
    """Unblock threads blocked in wait().
    """
    if self.event:
      self.event.set()                                  # unblock waiting thread

  def send_msg(self, msg):
    """Sends a message and logs (debug) messages that couldn't be sent."""
    if self.connected:
      return super(ThreadedComm, self).send_msg(msg)
    LOG.debug("*NOT* sending to %s: '%s'", self.addr_port, msg)

  def always_connected(self):
    """Enters working loop finished only on call to done() or on error.
    """
    while self.working:
      self.connect_and_run()

  def done(self):
    """Terminates the connection.
    """
    self.working = False
    self.disconnect()
    self.thread.join()

  def handle_connect_error(self, e):
    """See handle_connect_timeout.
    """
    super(ThreadedComm, self).handle_connect_error(e)
    self.handle_connect_timeout()

  def handle_connect_timeout(self):
    """Sleeps for a second if connection initialization is in timeout status.
    """
    time.sleep(1)
        
  def handle_connect(self):
    """Calls your connection_succeeded_function when connection is established.
    """
    self.connect_success_function()
