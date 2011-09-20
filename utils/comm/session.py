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

Defines classes working at the session layer of the OSI model.
Overview:
* BaseServer
* TCPServer
* UDPServer
* ForkingMixIn
* ThreadingMixIn
* create_server

Server classes of this module have been largely inspired by SocketServer.
However, there's the following modifications:
+ access to handler objects
+ server class auto-selected based on address family
+ TODO: complete the list
TODO: check timeout management for select (also impact of a client with small timeout)

Handler class of this module has been largely inspired by SocketServer.
However, there's the following modifications:
+ basic useful commands
+ TODO: complete improvement list
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
from threading import Thread, Lock
from collections import namedtuple
try:
    import threading
except ImportError:
    import dummy_threading as threading

from presentation import BasePresentation

from utils import handle_exception

LOG = logging.getLogger(__package__)
FATAL_ERRORS = (errno.EHOSTUNREACH, errno.EADDRNOTAVAIL)
DISCN_ERRORS = (errno.ECONNRESET, errno.WSAECONNRESET,
                errno.ECONNABORTED, errno.WSAECONNABORTED)


class BaseServer(object):
  """Greatly inspired from SocketServer, but allows using a single thread approach, .
  Unfortunately SocketServer is an old-style class and has a rigid design.
  """
  def __init__(self):
    self.__serving = False
    self.threaded = False
    self.thread = None
    self.listen_timeout = 0.5
    self.handler_timeout = 0.01     # aim for 100 select() per second
    self.clients = {}               # { sock : handler object }
    self.socket = None
    self.polling_sockets = None     # array of sockets polled in this thread

  def is_threaded(self):
    return self.threaded

  def is_started(self):
    return self.__serving

  def set_threaded(self):
    """Enable the server to start() its own thread.
    Sets handler_timeout so select is blocking.
    """
    self.threaded = True
    self.__is_shut_down = threading.Event()
    self.__threading_lock = threading.Lock()
    self.handler_timeout = None     # blocking select() in thread

  def set_addrPort(self, addrPort):
    """
    """
    self.addr_port = addrPort

  def set_RequestHandlerClass(self, ClientHandlerClass):
    """
    """
    self.RequestHandlerClass = ClientHandlerClass

  def set_listen_timeout(self, listen_timeout):
    """Sets socket timeout for incoming connections.
    """
    self.listen_timeout = listen_timeout
    if self.__serving:
      self.socket.settimeout(listen_timeout)
      self.update_poll_timeout()

  def set_handler_timeout(self, timeout):
    """Sets new handlers' socket timeout.
    """
    self.handler_timeout = timeout

  def update_poll_timeout(self):
    """
    """
    self.poll_interval = min([sock.gettimeout() for sock in \
                              self.polling_sockets + [self.socket]])
    LOG.debug("poll_interval for %s now %ss.", self, self.poll_interval)

  def activate(self):
    """To be overriden"""
    pass

  def disactivate(self):
    """To be overriden"""
    pass

  def start(self):
    """Starts the server (listen to connections).
    """
    self.__serving = True
    self.activate()
    self.polling_sockets = [self.socket]
    self.update_poll_timeout()
    if self.threaded:
      self.thread = Thread(target=G.server.serve_forever, name='server')
      self.thread.start()
    LOG.info("%s started in %s thread.", self.__class__.__name__,
             self.threaded and 'its' or 'main')
    return self.threaded and self.thread or None

  def pre_shutdown(self):
    """To be overriden"""
    LOG.debug('server %s now shutting down.' % self)
    pass

  def shutdown(self):
    """Stops the server.
    """
    self.pre_shutdown()
    if self.socket:
      self.__serving = False
      if self.threaded:
        self.__is_shut_down.wait()
        self.thread.join()
      else:
        for sock, client in self.clients.items():
          client.cleanup()
          if client.socket in self.polling_sockets:
            self.close_request(client.socket)
    self.disactivate()
    LOG.info('server %s now shut down.' % self)

  def serve_once(self):
    """Check for incoming connections and save further calls to select()
     for that thread.
    Return: False on error (also interrupts serve_forever()), True otherwise.
    """
    # XXX: Consider using another file descriptor or
    # connecting to the socket to wake this up instead of
    # polling. Polling reduces our responsiveness to a
    # shutdown request and wastes cpu at all other times.
    try:
      r, w, e = select.select(self.polling_sockets, [],
                              self.polling_sockets, self.poll_interval)
    except select.error, e_no:
      return self.handle_error(self.polling_sockets, "select error #%i" % e_no)
    if e:
      for sock in e:
        self.close_request(sock)
      return self.handle_error(e, self.clients[e[0]].addr_port)
    for sock in r:
      try:
        if sock is self.socket:
          self._handle_request_noblock()
        elif not self.clients[sock].read_socket():
          self.close_request(sock)
      except Exception, err:
        return self.handle_error(sock, err)
    return True

  def serve_forever(self):
    """Blocking call.
    Return: None
    """
    if not self.__serving:
      self.start()
    if self.threaded:
      self.__is_shut_down.clear()
    try:
      while self.__serving and self.serve_once():
        pass
    finally:
      if self.threaded:
        self.__is_shut_down.set()

  def _handle_request_noblock(self):
    """Handle one request, non-blocking.
    Assumes socket is readable, get_request() is non-blocking.
    """
    try:
      socket, client_addrPort = self.get_request()
    except socket.error:
      return self.handle_error(socket, client_addrPort)
    if self.verify_request(socket, client_addrPort):
      try:
        self.process_request(socket, client_addrPort)
      except:
        self.handle_error(socket, client_addrPort)
        self.close_request(socket)

  def handle_error(self, sock, client_addr):
    """Installs an interactive pdb session if logger is at DEBUG level.
    Return: None or False
    """
    LOG.error('%s got Exception with %s (%s)', self, sock, client_addr)
    handle_exception(LOG)

  def verify_request(self, request, client_addrPort):
    """Verify the request.  May be overridden.
    Return True if we should proceed with this request.
    """
    return True

  def process_request(self, sock, client_addrPort):
    """Creates a new client. Overridden by ForkingMixIn and ThreadingMixIn.
    """
    handler = self.finish_request(sock, client_addrPort)
    self.polling_sockets.append(sock)
    self.update_poll_timeout()
    self.clients[sock] = handler

  def finish_request(self, sock, client_addr):
    """Instanciates the RequestHandler and set its connection timeout.
    """
    LOG.debug('new connection request from %s (%s)', client_addr, sock)
    handler = self.RequestHandlerClass(self, sock, client_addr)
    sock.settimeout(self.handler_timeout)
    handler.setup()
    return handler

  def close_request(self, sock):
    """Cleans up an individual request. Extend but don't override.
    """
    self.clients[sock].cleanup()
    del self.polling_sockets[self.polling_sockets.index(sock)]
    del self.clients[sock]
    self.update_poll_timeout()

  def threadsafe_start(self):
    """Transparent threading support.
    When handlers are threaded, it's good to have a way to sync them.
    """
    self.__threading_lock.acquire()

  def threadsafe_stop(self):
    """Transparent threading support.
    """
    self.__threading_lock.release()


class TCPServer(BaseServer):
  """Base class for various socket-based server classes.
   Defaults to synchronous IP stream (i.e., TCP).

  Methods that may be overridden:
  - server_bind()
  - server_activate()
  - get_request() -> request, client_addrPort
  - handle_timeout()
  - verify_request(request, client_addrPort)
  - process_request(request, client_addrPort)
  - close_request(request)
  - handle_error()

  Methods for derived classes:
  - finish_request(request, client_addrPort)

  Class variables that may be overridden by derived classes or
  instances:
  - timeout
  - address_family
  - socket_type
  - request_queue_size (only for stream sockets)
  - allow_reuse_address
  """

  address_family = socket.AF_INET
  socket_type = socket.SOCK_STREAM
  request_queue_size = 5
  allow_reuse_address = True

  def activate(self):
    """Called by constructor to activate the server. May be overridden.
    """
    self.socket = socket.socket(self.address_family, self.socket_type)
    self.socket.settimeout(self.listen_timeout)
    if self.allow_reuse_address:
      self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
      self.socket.bind(self.addr_port)
    except socket.error, e:
      raise ValueError('cannot start server using %s: %s' % (self.addr_port,e))
    self.addr_port = self.socket.getsockname()
    self.socket.listen(self.request_queue_size)

  def disactivate(self):
    """Called to clean-up the server. May be overridden.
    """
    if self.socket:
      self.socket.close()

  def fileno(self):
    """Return socket file number. Interface required by select().
    """
    return self.socket.fileno()

  def get_request(self):
    """Get the request and client address from the socket.
    May be overridden."""
    return self.socket.accept()

  def close_request(self, sock):
    """Called to clean up an individual request.
    """
    if self.clients.has_key(sock):
      LOG.debug('closing TCP connection with %s (%s)',
                self.clients[sock].addr_port, sock)
    BaseServer.close_request(self, sock)
    sock.close()


class UDPServer(TCPServer):
  """UDP server class.
  """

  allow_reuse_address = False
  socket_type = socket.SOCK_DGRAM
  max_packet_size = 8192

  def get_request(self):
    data, client_addr = self.socket.recvfrom(self.max_packet_size)
    return (data, self.socket), client_addr

  def server_activate(self):
    pass                                            # No need to call listen()

  def close_request(self, socket):
    BaseServer.close_request(self, socket)          # No need to close anything


class ForkingMixIn:
  """Mix-in class to handle each request in a new process.
  """

  timeout = 300
  active_children = None
  max_children = 40

  def collect_children(self):
    """Internal routine to wait for children that have exited.
    """
    if self.active_children is None: return
    while len(self.active_children) >= self.max_children:
      # XXX: This will wait for any child process, not just ones
      # spawned by this library. This could confuse other
      # libraries that expect to be able to wait for their own
      # children.
      try:
        pid, status = os.waitpid(0, 0)
      except os.error:
        pid = None
      if pid not in self.active_children: continue
      self.active_children.remove(pid)

    # XXX: This loop runs more system calls than it ought
    # to. There should be a way to put the active_children into a
    # process group and then use os.waitpid(-pgid) to wait for any
    # of that set, but I couldn't find a way to allocate pgids
    # that couldn't collide.
    for child in self.active_children:
      try:
        pid, status = os.waitpid(child, os.WNOHANG)
      except os.error:
        pid = None
      if not pid: continue
      try:
        self.active_children.remove(pid)
      except ValueError, e:
        raise ValueError('%s. x=%d and list=%r' %(e.message, pid,
                                                  self.active_children))

  def handle_timeout(self):
    """Wait for zombies after self.timeout seconds of inactivity.
    May be extended, do not override.
    """
    self.collect_children()

  def process_request(self, socket, client_addrPort):
    """Fork a new subprocess to process the request.
    """
    self.collect_children()
    pid = os.fork()
    if pid:                                                     # Parent process
      if self.active_children is None:
        self.active_children = []
      self.active_children.append(pid)
      self.close_request(socket)
      return
    else:                                                       # Child process
      try:
        self.finish_request(socket, client_addrPort).read_while_running()
        os._exit(0)
      except:
        try:
          self.handle_error(socket, client_addrPort)
        finally:
          os._exit(1)


class ThreadingMixIn:
  """Mix-in class to handle each request in a new thread.
  """

  # Decides how threads will act upon termination of the main process
  daemon_threads = False

  def process_request_thread(self, socket, client_addrPort):
    """Same as in BaseServer but as a thread.
    In addition, exception handling is done here.
    """
    try:
      self.finish_request(socket, client_addrPort).read_while_running()
      self.close_request(socket)
    except:
      self.handle_error(socket, client_addrPort)
      self.close_request(socket)

  def process_request(self, socket, client_addrPort):
    """Start a new thread to process the request.
    """
    t = threading.Thread(target = self.process_request_thread,
                         args = (socket, client_addrPort))
    if self.daemon_threads:
      t.setDaemon (1)
    t.start()


class ForkingUDPServer(ForkingMixIn, UDPServer): pass
class ForkingTCPServer(ForkingMixIn, TCPServer): pass

class ThreadingUDPServer(ThreadingMixIn, UDPServer): pass
class ThreadingTCPServer(ThreadingMixIn, TCPServer): pass


# { type of port : { proto : { threading : class } } }
SERVER_CLASSES = { type(42): {'udp': { True : ThreadingUDPServer,
                                     False: UDPServer },
                              'tcp': { True : ThreadingTCPServer,
                                     False: TCPServer }
                            }
                  }

if hasattr(socket, 'AF_UNIX'):
  def clear_unix_socket(socket_path):
    if os.access(socket_path, os.W_OK) and os.stat(socket_path)[0] == 49645:
      LOG.debug('cleaning up socket file %s', socket_path)
      os.remove(socket_path)

  class UnixStreamServer(TCPServer):
    address_family = socket.AF_UNIX
    def __del__(self):
      clear_unix_socket(self.addr_port)

  class UnixDatagramServer(UDPServer):
    address_family = socket.AF_UNIX
    def __del__(self):
      clear_unix_socket(self.addr_port)

  class ThreadingUnixStreamServer(ThreadingMixIn, UnixStreamServer): pass
  class ThreadingUnixDatagramServer(ThreadingMixIn, UnixDatagramServer): pass

  SERVER_CLASSES[type('')] = { 'tcp': { True : ThreadingUnixStreamServer,
                                        False: UnixStreamServer },
                               'udp': { True : ThreadingUnixDatagramServer,
                                        False: UnixDatagramServer }
                               }


################################################################################
# Session layer for RequestHandler and BaseClient
###

class BasePeer(object):
  """Basic socket reading/writing, (dis)connection/error events handling.
  Base class for a local client connecting to a server (BaseClient) or
  for a remote client connecting to the local server (RequestHandler).

  * If you're using read_while_running() you can define each_loop(), called
   after the socket has been read.

  *
  """

  def __init__(self):
    self.running = False                                        # bail out flag
    self.unprocessed = ''
    self._th_save = {}                                      # see set_threading

  def handle_error(self, error):
    """Called upon connection error.
    Installs an interactive pdb session if logger is at DEBUG level.
    error: object (usually exception of string) to print in log
    Return: None
    """
    import utils
    LOG.warning("Connection error :%s", error)
    utils.handle_exception(LOG)

  def handle_disconnect(self):
    """Called after disconnection from server.
    Return: None
    """
    LOG.debug('client disconnected from remote server %s', self.addr_port)

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

  def read_socket(self):
    """Read its own socket.
    Return: False on socket error, True otherwise.
    """
    try:
      buff = self.socket.recv(2048)
      if not buff:
        return self.abort()
    except socket.error, e:
      if e.errno not in DISCN_ERRORS:                          # for Windows
        self.handle_error(e)
      return self.abort()
    LOG.debug("%s> command [%iB]: '%s'", self.socket.fileno(),
              len(self.unprocessed + buff), self.unprocessed + buff)
    self.unprocessed = self.process(self.unprocessed + buff)
    return True

  def write_socket(self, data):
    """Write its own socket.
    Return: None
    """
    if self.connected:
      try:
        LOG.debug("sending:'%s'", data)
        self.socket.send(data)
        return True
      except socket.error, e:
        if e.errno in DISCN_ERRORS:
          LOG.warning("client %s disconnected before we could send '%s'",
                      self.socket.fileno(), data)
        else:
          self.handle_error(e)
        return self.abort()
    else:
      LOG.warning("socket disconnected, cannot send data '%s'.", data)
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

  def read_while_running(self, timeout=0.01):
    """Process client commands until self.running is False. See also
     self.each_loop().
    timeout: delay (in seconds) see doc for read_once().
    Return: True if stopped running, False on error.
    """
    self.running = True
    each_loop = getattr(self,'each_loop',None)
    while self.running:
      if not self.read_once(timeout):
        return False
      each_loop and each_loop()
    return True

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


#TODO: clean class (of set_looping)
class BaseRequestHandler(BasePeer):
  """Instancied on successful connection to the server: a remote client.
  BasePeer provides 2 functions for the server, depending on threading status:
  - read_socket() when instances of this class share the server thread
  - read_while_running() when instances of this class run in their own thread.

  This class cannot be instanciated directly, it requires the implementation of
  process(), an abstract method of BasePresentation.
  Use setup()/cleanup() in child classes instead of __init__()/__del__().
  """

  def __init__(self, server, sock, addr_port):
    super(BaseRequestHandler,self).__init__()
    self.connected = True
    self.server = server                                # server that spawned us
    self.socket = sock
    self.addr_port = ( type(addr_port) is type("") and ("localhost","UNIX")
                       or addr_port )
    LOG.debug("initialized a %s.", self.__class__.__name__)

  def setup(self):
    """Initializer for child classes. Override.
    """
#    LOG.info("%i> connection accepted from %s on %s. Client is %slooping",
    LOG.info("%i> connection accepted from %s on %s.",
             self.socket.fileno(),self.addr_port[0],str(self.addr_port[1]))
#             self.work is self.read_once and '*NOT* ' or '')

  def cleanup(self):
    """Finisher for child classes. Override.
    """
#        if not self.server.handler_looping:
#            return
    try:
      connID = str(self.socket.fileno())
    except Exception, e:
      connID = '(closed)'
    LOG.info("%s> connection terminating : %s on "+str(self.addr_port[1]),
             connID, self.addr_port[0])


class BaseClient(BasePeer):
  """Client creating a connection to a (remote) server.
  BasePeer provides read_while_running() called in connect_and_run().

  This base class cannot be used directly, it requires the implementation of
  process(), an abstract method of BasePresentation.
  Unless you use BasePresentation.read_once(), you should only care about
   self.running to get out of self.connect_and_run().
  """

  @staticmethod
  def addrFamily_from_addrPort(addr_port):
    """
    Return: (Address Family, updated addr_port)
    """
    localhosts = ["127.0.0.1", "localhost"]
    if hasattr(socket, "AF_UNIX") and type(addr_port[1]) is type(""):
      if addr_port[0] and addr_port[0] not in localhosts:
        raise ValueError('address must be null or one of %s', localhosts)
      return socket.AF_UNIX, addr_port[1]
    return socket.AF_INET, addr_port

  def __init__(self, addr_port):
    super(BaseClient, self).__init__()
    addr_port = tuple(addr_port)
    self.family, self.addr_port = BaseClient.addrFamily_from_addrPort(addr_port)
    self.socket = None
    self.connected = False
    self._connect_timeout = None                                  # set blocking

  @property
  def connect_timeout(self):
    """Gets the timeout (in seconds) connecting to a server."""
    return self._connect_timeout
  @connect_timeout.setter
  def connect_timeout(self, timeout):
    """Sets the timeout (in seconds) connecting to a server."""
    self._connect_timeout = timeout

  @property
  def host(self):
    return self.addr_port[0]
  @host.setter
  def host(self, newhost):
    addr_port = (newhost, self.addr_port[1])
    self.family, self.addr_port = BaseClient.addrFamily_from_addrPort(addr_port)

  @property
  def port(self):
    return self.addr_port[1]
  @port.setter
  def port(self, newport):
    addr_port = self.addr_port[0], newport.isdigit() and int(newport) or newport
    self.family, self.addr_port = BaseClient.addrFamily_from_addrPort(addr_port)

  def handle_connect_timeout(self):
    """Called upon connection time-out.
    Return: None
    """
    LOG.debug('time-out connecting to remote server %s', self.addr_port)

  def handle_connect_error(self, e):
    """Called upon error waiting for input.
    Return: None
    """
    LOG.debug('error connecting to server %s (%s)', self.addr_port, e)

  def handle_connect(self):
    """Called upon successful connection to (remote) server.
    Return: None
    """
    LOG.debug('client connected to remote server %s', self.addr_port)

  def connect(self):
    """Creates a new connection to a server.
    Return: False on error.
    """
    assert self.connected is False, 'connecting while connected ?'
    LOG.debug('connecting to %s:%s (for%s)', self.addr_port[0],
              self.addr_port[1], (self.connect_timeout is None and 'ever')
              or " %ss." % self.connect_timeout )
    try:
      self.socket = socket.socket(self.family)
      self.socket.settimeout(self.connect_timeout)
      self.socket.connect(self.addr_port)
    except socket.timeout:
      self.handle_connect_timeout()
    except socket.error, e:
      if e[0] in FATAL_ERRORS:
        self.running = False                          # too serious to carry on
      self.handle_connect_error(e)
    else:
      self.connected = True
      self.handle_connect()
      return True
    self.socket = None
    return False

  def pre_connect(self):
    """Override if needed. Called by connect_and_run() before attempting to
    connect the 1st time.
    Return: False to abort connection, True to carry on.
    """
    return True

  def connect_and_run(self, connect_timeout=None, read_timeout=0.01):
    """Blocking call. Interrupt the loop setting self.running to False.
    connect_timeout: alternative to setting self.connect_timeout.
    read_timeout: delay in seconds before giving up waiting for data (select).
    Return: True if disconnected normally, False on error.
    """
    self.running = True
    self.connect_timeout = connect_timeout
    if not self.pre_connect():
      return True                                     # not considered an error
    while self.running and not self.connect():        # carry on despite failure
      pass
    if not self.connected:
      return False
    try:
      self.read_while_running(read_timeout)
      ret = True
    except select.error, e:
      self.handle_error(self.socket, e)
      ret = False
    finally:
      if self.socket:
        self.socket.close()
      self.connected = False
      self.handle_disconnect()
    return ret

  def disconnect(self):
    """Set flag for disconnection.
    Return: None
    """
    self.running = False


################################################################################
# Helper:
# - auto-selection of classes based on (address,port). Users can choose between
#    classic inheritance and using create_server().
###


ThreadingInfo = namedtuple('ThreadingInfo', 'threaded_server threaded_clients')

def getBaseServerClass(addr_port, threaded):
  """Returns the appropriate base class for server according to addr_port.
  Protocol can be specified using a prefix from 'udp:' or 'tcp:' in the
   port field (eg. 'udp:4242'). Default is udp.
  """
  D_PROTO = 'tcp'
  try:
    addr, port = addr_port
  except ValueError:
    raise ValueError('addr_port is a tuple also for AF_UNIX: %s'% addr_port)
  if type(port) is type(''):                                    # check protocol
    proto, port = port.find(':') > 0 and port.split(':') or (D_PROTO, port)
    if port.isdigit():
      addr_port = (addr, int(port))
  else:
    proto = D_PROTO

  try:
    srv_class = SERVER_CLASSES[type(port)][proto][threaded]
  except KeyError:
    raise ValueError('No suitable server class for:', port, proto)
  if type(addr_port[1]) is type(''):
    addr_port = addr_port[1]
  LOG.debug('address-port: %s, selected server class: %s',addr_port,srv_class)
  return tuple(addr_port), srv_class


def create_server(handler_class, addr_port,
                  threading_info=(False, True), server_mixin=None):
  """Create a server handling incoming connections with handler_class.
  handler_class: class with your own cmd_.. member fonctions
  addr_port: (interface address, port) for the server to listen to.
  threading_info: (threaded_server_bool, threaded_clients_bool). Defaults to
                  (False, True): each handlers have their own thread.
  server_mixin: class to be mixed with the auto-selected child of BaseServer.
                Default behaviour is to use the auto-selected only.
  Return: auto-selected server class instance (may be mixed with server_mixin).
  """
  if not issubclass(handler_class, BaseRequestHandler):
    raise TypeError("%s must inherit from BaseRequestHandler" % handler_class)
  # XXX: new style classes only, remove for python3
  if server_mixin and not issubclass(server_mixin, object):
    raise TypeError("%s must inherit from object" % server_mixin)
  if (server_mixin and
      server_mixin in [ cls for proto, cls in SERVER_CLASSES.items() ]):
    raise TypeError("server_mixin (%s) must be your own class" % server_mixin)

  threaded_srv, threaded_cli = threading_info
  addr_port, base_class = getBaseServerClass(tuple(addr_port), threaded_cli)

  def init_server(self):
      """Call initializers properly.
      """
      base_class.__init__(self)
      self.set_RequestHandlerClass(handler_class)
      self.set_addrPort(addr_port)
      server_mixin.__init__(self)
      if threaded_srv:
        self.set_threaded()

  if server_mixin:
    return type(server_mixin.__name__+base_class.__name__,
                (server_mixin, base_class),{'__init__':init_server})()
  else:
    srv = base_class()
    srv.set_RequestHandlerClass(handler_class)
    srv.set_addrPort(addr_port)
    return srv
