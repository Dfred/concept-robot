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
MAX_B = 64                              # Max len in Bytes for Debug of packets


class BasePresentation(object):
  """Base class for protocol handlers.
  Handle a specific protocol by implementing these abstract functions:
  - process()
  - parse_cmd()
  - send_msg()
  """

  __metaclass__ = ABCMeta

  def handle_notfound(self, cmd, args):
    """Called when a cmd_... method (command handler) is not found in self.
    To be overriden.
    Return: None
    """
    LOG.error("function %s not found in %s (args: '%s')" % (cmd,self,args))

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


class ASCIICommandProto(BasePresentation):
  """This class implements a command-to-function resolver for ASCII based
  application protocols using first word as command name.
  E.G: "get file my_file.txt" would call cmd_get() with ["file","my_file.txt"]
  """

  CMD_PREFIX = "cmd_"

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
      bound_fct = getattr(self, ASCIICommandProto.CMD_PREFIX+cmd)
    except AttributeError:
    #XXX:design limitation with metaHandlers: in next call self shifts and state
    # of parsing (self.data, self.data_end) is not accessible until call returns
      ret = self.handle_notfound(ASCIICommandProto.CMD_PREFIX+cmd, args)
    else:
      ret = bound_fct(args)
    if ret:                                                 # data to be ignored
      self.read(ret)

  def process(self, recv_data):
    """Command dispatcher function.
    Commands linked with '&&' are issued within the same step.
    recv_data: network data to process (should be multiline ASCII text)
    Return: unprocessed data, not finishing with a \n
    """
    LOG.debug("%s> command [%iB]:%s", self._socket.fileno(), len(recv_data),
              len(recv_data)>MAX_B and recv_data[:MAX_B]+'[...]' or recv_data)
    #XXX: this version allows tampering with buffers while parsing.
    self.data = recv_data                                   # allows extern read
    self.data_end = 0                                       # end data processed
    end = recv_data.find('\n')
    while end != -1:
      end += self.data_end                                  # adjust abs. offset
      line = recv_data[self.data_end:end]
      self.data_end += 1                                    # account for '\n'
      for cmd in line.split('&&'):                          # same step commands
        self.data_end += len(cmd) + (line!=cmd and 2 or 0)  # account for '&&'
        cmd = cmd.strip()
        if cmd:
          self.parse_cmd(cmd)
      end = recv_data[self.data_end:].find('\n')
    self.data = None                                        # garbage collection
    return recv_data[self.data_end:]

  def read(self, size):
    """Read in self.data, then the socket itself if needed.

    Return: data read. Notice: caller shall check length of data read!
    """
#    import pdb; pdb.set_trace()
    more = size - len(self.data[self.data_end:])
    if more > 0:
      data = self.read_socket(more)
      if data != False:
        self.data += data
        size -= more - len(data) if len(data) <= more else 0
      else:
        size = len(self.data[self.data_end:])
    prev_end = self.data_end
    self.data_end += size
    return self.data[prev_end:self.data_end]

  def send_msg(self, message):
    """Send a message adding a trailing '\n' as required by the protocol.
    To be overriden for implementation of a different protocol.
    message: ASCII text
    Return: None
    """
    self.write_socket(message+'\n')


class ASCIICommandProtoEx(ASCIICommandProto):
  """This class interprets common special characters for easier use of scripts
  so it's possible to dump a script to a server or use the filter_lines() to
  cleanup the special content of a script.
  """

  @staticmethod
  def filter_lines(text):
    """Checks the line for special characters (python/*sh style):
    start of line + # : comment
    \ + end of line   : append next line to current
    odd number of "   : raw text until closing "
    Return: (filtered lines, remaining characters)
    """
    filtered_lines, unfinished_line = [], ''
    buffered = ''
    raw = False
    for s_line in text.splitlines(True):                    # keep line endings
      if s_line.find('"') != -1 and s_line.count('"') % 2:  # odd double-quotes
        raw = not raw
      if raw:
        buffered += s_line
        continue
      elif s_line.lstrip().startswith('#'):                 # comments
        continue
      elif s_line.endswith('\\\n'):                         # escaped multiline
        buffered += s_line[:-2]
        continue
      if not s_line.endswith('\n'):                         # must be last line
        unfinished_line = s_line
        continue
      s_line = buffered + s_line.strip()
      buffered = ''
      if not s_line:
        continue
      filtered_lines.append(s_line)
    return filtered_lines, unfinished_line

  def process(self, recv_data):
    """Uses filter_line() to add script-friendly features.
    """
    LOG.debug("%s> command [%iB]:%s", self._socket.fileno(),
              len(recv_data)>32 and recv_data[:32]+'[...]' or recv_data)
    filtered, buffered = self.__class__.filter_lines(recv_data)
    for cmdline in filtered:
      for cmd in cmdline.split('&&'):                       # same loop exec
        cmd = cmd.strip()
        if cmd:
          self.parse_cmd(cmd)
    return buffered


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
    self.abort()
    self.server.shutdown()

  def cmd_clients(self, args):
    """Lists clients currently connected.
    Return: None
    """
    LOG.info("%s> listing %i clients.",
             self._socket.fileno(), len(self.server.clients))
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
