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

Defines classes working at the presentation layer of the OSI model.
Overview:
* BasePresentation, socket reading, (dis)connection/error events handling
* ASCIICommandProto, packet tokenization and function resolver/caller
* RequestHandler, implements interface for BaseServer (see session.py)
* BaseClient, class for clients connecting to BaseServer.

"""

__author__    = "Frédéric Delaunay"
__license__   = "GPL"
__maintainer__= "Frédéric Delaunay"
__email__     = "delaunay.fr at gmail.com"
__credits__   = ["University of Plymouth and EPSRC"]

import errno
import socket
import select
import logging

from abc import ABCMeta, abstractmethod

LOG = logging.getLogger(__package__)


class BasePresentation(object):
  """Basic socket reading, (dis)connection/error events handling.
  Base class for a local client connecting to a server (BaseClient) or
  for a remote client connecting to the local server (RequestHandler).

  To implement a specific protocol, you would override:
  - process()
  - parse_cmd()
  - send_msg()
  """

  __metaclass__ = ABCMeta

  CMD_PREFIX = "cmd_"

  def __init__(self):
    self.unprocessed = ''
    self.connected = False
    self.running = False                                # processing loop switch
    self._th_save = {}                                  # see set_threading

  def handle_error(self, error):
    """Called upon connection error.
    Installs an interactive pdb session if logger is at DEBUG level.
    error: object (usually exception of string) to print in log
    Return: None
    """
    import utils
    LOG.warning("Connection error :%s", error)
    if LOG.getEffectiveLevel() != logging.DEBUG:
      utils.handle_exception_simple()
      print 'use debug mode to spawn post-mortem analysis with pdb'
    else:
      utils.handle_exception_debug()

  def handle_disconnect(self):
    """Called after disconnection from server.
    Return: None
    """
    LOG.debug('client disconnected from remote server %s', self.addr_port)

  def handle_notfound(self, cmd, args):
    """Called when a cmd_... method (a command handler) is not found in self.
    To be overriden.
    Return: None
    """
    LOG.error("function %s not found in %s (args: '%s')" % (cmd,self,args))

  def abort(self):
    """Completely abort any loop or connection.
    Return: False
    """
    if self.socket:
      self.socket.close()
    self.connected = False
    self.running = False
    self.handle_disconnect()
    return False

  def read_once(self, timeout):
    """One-pass processing of client commands.
    timeout: time waiting for data (in seconds).
             a value of 0 specifies a poll and never blocks.
             a value of None makes the function blocks until socket's ready.
    Return: False on error, True if all goes well or upon timeout expiry.
    """
    try:
      r, w, e = select.select([self.socket], [], [self.socket], timeout)
    except KeyboardInterrupt:
      self.abort()
      raise
    if not r:
      return timeout
    if e:
      self.handle_error('select() error with socket %s' % e)
      return self.abort()
    return self.read_socket()

  def read_socket(self):
    """Read its own socket.
    Return: False on socket error, True otherwise.
    """
    try:
      buff = self.socket.recv(2048)
      if not buff:
        return self.abort()
    except socket.error, e:
      if e.errno != errno.WSAECONNRESET:                          # for Windows
        self.handle_error(e)
      return self.abort()
    self.unprocessed = self.process(self.unprocessed + buff)
    return True

  def each_loop(self):
    """Override to do your stuff if you use read_while_running().
    Return: None
    """
    pass

  def read_while_running(self, timeout=0.01):
    """Process client commands until self.running is False. See also
     self.each_loop().
    timeout: delay (in seconds) see doc for read_once().
    Return: True if stopped running, False on error.
    """
    self.running = True
    while self.running:
      if not self.read_once(timeout):
        return False
      self.each_loop()
    return True

  # TODO: rename to dispatch
  @abstractmethod
  def process(self, command):
    """Abstract. Command dispatcher function.
    Return: None (When overriden, return unprocessed buffered data)
    """
    pass

  # TODO: rename to parse
  @abstractmethod
  def parse_cmd(self, data):
    """Abstract. Parse data read from socket.
    Return: None
    """
    pass

  # TODO: rename to send
  @abstractmethod
  def send_msg(self, msg):
    """Abstract. Send a message to the remote.
    Return: None
    """
    pass

  # TODO: test
  def set_threading(self, threaded):
    """Enable threading.
    It's not the best design, but it allows transparent threading.
    threaded: True => set thread-safe
    Return: None
    """
    def th_send_msg(self, msg):
      """Thread safe version of send_msg().
      """
      self._threading_lock.acquire()
      BasePresentation.send_msg(self, msg)
      self._threading_lock.release()

    if threaded:
      self._th_save['send_msg'] = self.send_msg
      self._threading_lock = Lock()
      self.send_msg = th_send_msg
      LOG.debug('client in thread-safe. send_msg is %s', self.send_msg)
    else:
      for name, member in self._th_save:
        setattr(self, name, member)
      self._th_save.clear()
      LOG.debug('client in single-thread. send_msg is %s', self.send_msg)


class ASCIICommandProto(object):
  """This class implements a command-to-function resolver for ASCII based
  application protocols using first word as command name.
  E.G: "get file my_file.txt" would call cmd_get() with ["file","my_file.txt"]
  """

  def parse_cmd(self, cmdline):
    """Tokenise ASCII lines and attempt to call `cmd_ + 1st_token` of self.
    If found, calls function with list of remaining tokens as argument.
    If not found, calls self.handle_notfound().
    To be overriden for implementation of a different protocol.
    Return: None
    """
    tokens = cmdline.split(None,1)
    cmd, args = tokens[0], tokens[1] if len(tokens) > 1 else ''
    try:
      bound_fct = getattr(self, self.CMD_PREFIX+cmd)
    except AttributeError:
      self.handle_notfound(self.CMD_PREFIX+cmd, args)
    else:
      bound_fct(args)

  def process(self, command):
    """Command dispatcher function.
    Commands can be issued within the same step by linking them with '&&'.
    command: (multiline) ASCII text to process
    Return: unprocessed data, not finishing with a \n
    """
    LOG.debug("%s> command [%iB]: '%s'",
              self.socket.fileno(), len(command), command)
    buffered = ''
    for cmdline in command.splitlines(True):
      if cmdline.lstrip().startswith('#'):                  # comments
        continue
      elif cmdline.endswith('\\\n'):                        # escaped multiline
        buffered += cmdline[:-2]
        continue
      # XXX: issue with windows \r ?
      elif not cmdline.endswith('\n'):                      # unfinished line
        return cmdline

      cmdline = buffered + cmdline
      buffered = ''
      cmdline = cmdline.strip()
      if not cmdline:
        continue
      for cmd in cmdline.split('&&'):                       # same loop exec
        self.parse_cmd(cmd)
    return buffered

  def send_msg(self, message):
    """Send a message adding a trailing \\n as required by the protocol.
    To be overriden for implementation of a different protocol.
    message: ASCII text
    Return: None
    """
    LOG.debug("sending '%s\n'", message)
    self.socket.send(message+'\n')



class RequestHandlerCmdsMixIn(object):
  """This class adds the following functions :
  * cmd_shutdown:
  * cmd_clients:
  * cmd_verb:
  If needed, set your own protocol handler overriding BasePresentation.process.
  """

  def cmd_shutdown(self, args):
    """Disconnects all clients and terminate the server process.
    Return: None
    """
    if self.server is None:
      raise CmdError("cannot shutdown server")
    self.running = False
    self.server.shutdown()

  def cmd_clients(self, args):
    """Lists clients currently connected.
    Return: None
    """
    LOG.info("%s> listing %i clients.",
             self.socket.fileno(), len(self.server.clients))
    clients_infos = []
    for sock, cl in self.server.clients.iteritems():
      clients_infos.append(type(cl.addr_port) is type("") and
                           (sock.fileno(), "UNIX", "localhost") or
                           (sock.fileno(), cl.addr_port[1], cl.addr_port[0]))
    clients_infos.sort()
    obuffer = "clients: %i connected: (ID, PORT, ADDR)"%(len(clients_infos))
    for client_info in clients_infos:
      obuffer += "\\\n> %s:  %5s  %s" % client_info
    self.send_msg(obuffer)

  def cmd_verb(self, args):
    """Changes LOG verbosity level.
    Return: None
    """
    if not args:
      self.send_msg("CRITICAL 50\nERROR	 40\nWARNING  30\n"
                    "INFO     20\nDEBUG	 10\nNOTSET    0")
    else:
      LOG.warning("changing log level to %s", args[0])
      LOG.setLevel(args[0])
    self.send_msg("verb is %s now" % LOG.getEffectiveLevel())
