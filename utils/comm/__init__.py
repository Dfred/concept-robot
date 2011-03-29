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


"""
comm package for python.
versions >= 2.5

A fully functional template server and associated client talking ASCII:
Provides async socket-based communication layer for modules + logging support.
Also allows user classes to inherit from nothing (see create_server() )
Look at exemple.py for an overview.

The server definitions of this module has been largely inspired by SocketServer.
However, significant modifications make it more usable than the original.
"""

__author__    = "Frédéric Delaunay"
__license__   = "GPL"
__version__   = "0.4b"
__status__    = "Prototype"
__date__      = "Thu. 17 Feb 2011"
__maintainer__= "Frédéric Delaunay"
__email__     = "f dot d at chx-labs dot org"
__credits__   = ["University of Plymouth and EPSRC"]

import os
import socket
import select
import logging
from threading import Thread, Lock

LOGFORMAT = "%(asctime)s %(lineno)4d:%(filename).21s\t-%(levelname)s-\t%(message)s"
# let users set log format themselves (see set_default_logging)
LOG = logging.getLogger(__package__)


class ProtocolError(Exception):
    """Base Exception class for protocol error.
    Failed transmissions shall raise exceptions inherting from this class.
    """
    pass


class CmdError(Exception):
    """Base Exception class for error in command processing.
    Failed commands shall raise exceptions inherting from this class.
    """
    pass


class ClassError(Exception):
    """Exception for dealing with type generation.
    """
    pass


class BaseServer(object):
    """Allows using a single threaded approach, inspired from SocketServer.
    Unfortunately SocketServer is an old-style class and has a rigid design.
    """
    def __init__(self):
        self.running = False
        self.threaded = False
        self.listen_timeout = 0.5
        self.handler_timeout = 0.01     # aim for 100 select() per second
        self.handler_looping = True     # default looping behaviour for RequestHandler
        self.clients = {}               # { sock : handler object }
        self.socket = None
        self.polling_sockets = None     # array of sockets polled in this thread

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
        if self.running:
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

    def activate(self):
        """To be overriden"""
        pass

    def disactivate(self):
        """To be overriden"""
        pass

    def start(self):
        """Starts the server (listen to connections).
        """
        self.running = True
        self.activate()
        self.polling_sockets = [self.socket]
        self.update_poll_timeout()
        if self.threaded:
            self.thread = Thread(target=G.server.serve_forever, name='server')
            self.thread.start()
        LOG.info("server started in %s-thread mode",
                 self.threaded and 'multi' or 'single')
        return self.threaded and self.thread or None

    def pre_shutdown(self):
        """To be overriden"""
        pass

    def shutdown(self):
        """Stops the server.
        """
        self.pre_shutdown()
        if self.socket:
            self.running = False
            if self.threaded:
                self.__is_shut_down.wait()
                self.thread.join()
            else:
                for fd, client in self.clients.items():
                    client.finish()
                    if client.socket in self.polling_sockets:
                        self.close_request(client.socket)
        self.disactivate()
        LOG.info('server now shut down.')

    def serve_once(self):
        """Check for incoming connections and saves further calls to select()
         for that thread.
        """
        # XXX: Consider using another file descriptor or
        # connecting to the socket to wake this up instead of
        # polling. Polling reduces our responsiveness to a
        # shutdown request and wastes cpu at all other times.
        try:
            r, w, e = select.select(self.polling_sockets, [],
                                    self.polling_sockets, self.poll_interval)
            if e:
                return self.handle_error(e, self.clients[e].addr_port)
            for sock in r:
                if sock is self.socket:
                    self._handle_request_noblock()
                elif not self.clients[sock].read_socket():
                    self.close_request(sock)
        except Exception, err:
            return self.handle_error(self.polling_sockets, None)
        return True

    def serve_forever(self):
        """Blocking call. Inspired from SocketServer.
        """
        if not self.running:
            self.start()
        if self.threaded:
            self.__is_shut_down.clear()
        try:
            while self.running and self.serve_once():
                pass
        finally:
            if self.threaded:
                self.__is_shut_down.set()

    def _handle_request_noblock(self):
        """Handle one request, non-blocking. Inspired from SocketServer
        assumption: socket is readable, get_request() is non-blocking.
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
        """
        import traceback
        LOG.error('Exception raised with %s (%s)', sock, client_addr)
        if LOG.getEffectiveLevel() != logging.DEBUG:
            print 'use debug mode to spawn post-mortem analysis with pdb'
        else:
            import pdb
            print '===EXCEPTION CAUGHT'+'='*60
            traceback.print_exc()
            pdb.post_mortem()

    def verify_request(self, request, client_addrPort):
        """Verify the request.  May be overridden.
        Return True if we should proceed with this request.
        """
        return True

    def finish_request(self, sock, client_addr):
        """Instanciates the RequestHandler and set its connection timeout.
        """
        LOG.debug('new connection request from %s (%s)', client_addr, sock)
        handler = self.RequestHandlerClass(self, sock, client_addr)
        sock.settimeout(self.handler_timeout)
        return handler

    def process_request(self, sock, client_addrPort):
        """Creates a new client. Overridden by ForkingMixIn and ThreadingMixIn.
        """
        handler = self.finish_request(sock, client_addrPort)
        self.polling_sockets.append(sock)
        self.update_poll_timeout()
        self.clients[sock] = handler

    def close_request(self, sock):
        """Cleans up an individual request. Extend but don't override.
        """
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
    Inspired from SocketServer. Defaults to synchronous IP stream (i.e., TCP).

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
        self.socket = socket.socket(self.address_family,
                                    self.socket_type)
        self.socket.settimeout(self.listen_timeout)
        if self.allow_reuse_address:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.socket.bind(self.addr_port)
        except socket.error, e:
            raise ProtocolError('cannot start server using %s: %s' % (
                    self.addr_port, e))
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
        # No need to call listen() for UDP.
        pass

    def close_request(self, socket):
        # No need to close anything.
        BaseServer.close_request(self, socket)


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
        if pid:
            # Parent process
            if self.active_children is None:
                self.active_children = []
            self.active_children.append(pid)
            self.close_request(socket)
            return
        else:
            # Child process.
            # This must never return, hence os._exit()!
            try:
                self.finish_request(socket, client_addrPort)
                os._exit(0)
            except:
                try:
                    self.handle_error(socket, client_addrPort)
                finally:
                    os._exit(1)


class ThreadingMixIn:
    """Mix-in class to handle each request in a new thread.
    """

    # Decides how threads will act upon termination of the
    # main process
    daemon_threads = False

    def process_request_thread(self, socket, client_addrPort):
        """Same as in BaseServer but as a thread.
        In addition, exception handling is done here.
        """
        try:
            self.finish_request(socket, client_addrPort)
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
                              } }

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
    # check protocol
    if type(port) is type(''):
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
    return addr_port, srv_class


def create_RequestHandlerClass(handler_class, threaded=False):
    """Creates a new (compound) type of RequestHandler suitable for inclusion to
    a compound server. Users can simply ignore networking in the class code.
    """
    if not issubclass(handler_class, object):
        raise ClassError('class %s must inherit from object' % handler_class)
    if handler_class == RequestHandler:
        raise ClassError("handler_class (%s) must be your own class" %
                         handler_class)

    def handler_init(self, server, sock, client_addr):
        """Call initializers properly + runtime support for threading.
        """
        RequestHandler.__init__(self, server, sock, client_addr)
        # add runtime support for threading (sending clients)
        if threaded:
            self._threading_lock = Lock()
            def th_send_msg(self, msg):
                self._threading_lock.acquire()
                BaseComm.send_msg(self, msg)
                self._threading_lock.release()
        handler_class.__init__(self)

    return type(handler_class.__name__+'RequestHandler',
                (handler_class, RequestHandler),{'__init__':handler_init})


def create_server(ext_class, handler_class, addr_port, thread_info):
    """
    """
    if not issubclass(ext_class, object):
        raise ClassError("class %s must inherit from object" % ext_class)
    if ext_class in [ cls for proto, cls in SERVER_CLASSES.items() ]:
        raise ClassError("ext_class (%s) must be your own class" % ext_class)

    addr_port, base_class = getBaseServerClass(addr_port, thread_info[0])
    mixed_handler_class = create_RequestHandlerClass(handler_class,
                                                     thread_info[1])
    def init_server(self):
        """Call initializers properly.
        """
        base_class.__init__(self)
        self.set_RequestHandlerClass(mixed_handler_class)
        self.set_addrPort(addr_port)
        ext_class.__init__(self)

    return type(ext_class.__name__+base_class.__name__,
                (ext_class, base_class),{'__init__':init_server})()


###
# Protocol Level: Request Handlers and Remote Clients
###

class BaseComm(object):
    """Basic protocol handling and command-to-function resolver. This is the
     base class for a local client connecting to a server (BaseClient) or for a
     handler of a remote client connecting to the local server (RequestHandler).
    This class mainly relies on socket's fileno() function.
    There's no
    To implement a binary protocol, you'd override process() and parse_cmd().
    """

    CMD_PREFIX = "cmd_"

    def __init__(self):
        self.unprocessed = ''
        self.connected = False
        self.running = False

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
        """Non-blocking call for processing client commands (see __init__).
        timeout: time waiting for data (in seconds).
                 a value of 0 specifies a poll and never blocks.
                 a value of None makes the function blocks until socket's ready.
        Returns: False on error, True if all goes well or timeout on expiry.
        """
        r, w, e = select.select([self.socket], [], [self.socket], timeout)
        if not r:
            return timeout
        if e:
            self.handle_error('Unknown error with socket %s' % e)
            return self.abort()
        return self.read_socket()

    def read_socket(self):
        """Read its own socket.
        Returns: False on socket error, True otherwise.
        """
        try:
            buff = self.socket.recv(2048)
            if not buff:
                return self.abort()
        except socket.error, e:
            self.handle_error(e)
            return self.abort()
        self.unprocessed = self.process(self.unprocessed + buff)
        return True

    def read_while_running(self, timeout=0.01):
        """Blocking call for processing of client commands (see __init__) which
         only returns when self.running is False.
        timeout: optional delay see doc for read_once().
        Returns: True if stopped running, False on error.
        """
        self.running = True
        while self.running:
            if not self.read_once(timeout):
                return False
        return True

    def parse_cmd(self, cmdline):
        """To be overriden for implementation of a different protocol.
        Returns: None
        """
        cmd_tokens = cmdline.split(None,1) # keep 1
        cmd, args = self.CMD_PREFIX+cmd_tokens.pop(0),\
                    cmd_tokens and cmd_tokens[0] or ""
        try:
            try:
                bound_fct = getattr(self, cmd)
            except AttributeError:
                self.handle_notfound(cmd, args)
            else:
                bound_fct(args)
        except Exception, e:
            LOG.warning("%s> unsuccessful command '%s' [%s]",
                        self.socket.fileno(), cmdline, e)
            if LOG.getEffectiveLevel() == logging.DEBUG:
                raise

    def process(self, command):
        """Command dispatcher function. (Override for different protocol).
        Tokenize command and calls 'cmd_ + 1st_token' function defined in self.
        Calls self.handle_notfound if the built function name isn't defined.
        Function is called with remaining tokens (array) as one argument.
        Simultaneous commands (called within the same step) can be issued
         linking them with '&&'.
        command: (multiline) text data to process
        Returns: unread last bits, not finishing with a \n
        """
        LOG.debug("%s> command [%iB]: '%s'",
                  self.socket.fileno(), len(command), command)
        buffered = ''
        for cmdline in command.splitlines(True):
            # comment
            if cmdline.lstrip().startswith('#'):
                continue
            # escaped multiline (useful for batchs)
            elif cmdline.endswith('\\\n'):
                buffered += cmdline[:-2]
                continue
            # unfinished line
            elif not cmdline.endswith('\n'):
                # may be an issue here with windows \r
                return cmdline
            cmdline = buffered + cmdline
            buffered = ''
            cmdline = cmdline.strip()
            if not cmdline:
                continue
            for cmd in cmdline.split('&&'):
                self.parse_cmd(cmd)
        return buffered

    def send_msg(self, msg):
        """Sends msg with a trailing \\n as required by the protocol.
        """
        LOG.debug("sending %s\n", msg)
        self.socket.send(msg+'\n')

    def handle_error(self, e):
        """Callback for connection error.
        Installs an interactive pdb session if logger is at DEBUG level.
        """
        import traceback
        LOG.warning("Connection error :%s", e)
        if LOG.getEffectiveLevel() != logging.DEBUG:
            print 'use debug mode to spawn post-mortem analysis with pdb'
        else:
            import pdb
            print '===EXCEPTION CAUGHT'+'='*60
            traceback.print_exc()
            pdb.post_mortem()

    def handle_disconnect(self):
        """Callback after client disconnection to (remote) server.
        """
        LOG.debug('client disconnected from remote server %s', self.addr_port)

    def handle_notfound(self, cmd, args):
        """When a method (a command) is not found in self. See process().
        To be overriden.
        """
        LOG.debug("function %s not found in %s [args: '%s']", cmd, self, args)

    def cmd_bye(self, args):
        """Disconnects that client.
        """
        self.running = False
    cmd_EOF = cmd_bye


class RequestHandler(BaseComm):
    """Instancied on successful connection to the server: a remote client.

    Reads data from self.request and adds default functions :
     cmd_shutdown, cmd_clients and cmd_verb.
    If needed, define your own protocol handler overriding BaseComm.process.
    """

    def __init__(self, server, sock, addr_port):
        BaseComm.__init__(self)
        self.server = server
        self.socket = sock
        self.addr_port = addr_port

    def run(self):
        try:
            self.setup()
            self.work()
            self.finish()
        finally:
            import sys
#            sys.exc_traceback = None    # Help garbage collection

    def setup(self):
        """Overrides SocketServer
        """
        # check if we want to block in self.work()
        self.work = self.server.handler_looping and\
            self.read_while_running or self.read_once
        # update addr_port for unix sockets (another crazy thing!)
        self.addr_port = type(self.addr_port) is type("") and \
            ("localhost", "UNIX Socket") or self.addr_port
        LOG.info("%i> connection accepted from %s on %s. Client is %slooping",
                 self.socket.fileno(),self.addr_port[0],str(self.addr_port[1]),
                 self.work is self.read_once and '*NOT* ' or '')

    def finish(self):
        """Overrides SocketServer
        """
#        if not self.server.handler_looping:
#            return
        LOG.info("%i> connection terminating : %s on "+str(self.addr_port[1]),
                 self.socket.fileno(), self.addr_port[0])

    def cmd_shutdown(self, args):
        """Disconnects all clients and terminate the server process.
        """
        if self.server is None:
            raise CmdError("cannot shutdown server")
        self.running = False
        self.server.shutdown()

    def cmd_clients(self, args):
        """Lists clients currently connected.
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
        """
        if not args:
            self.send_msg("CRITICAL 50\nERROR	 40\nWARNING  30\n"
                          "INFO     20\nDEBUG	 10\nNOTSET    0")
        else:
            LOG.warning("changing log level to %s", args[0])
            LOG.setLevel(args[0])
        self.send_msg("verb is %s now" % LOG.getEffectiveLevel())


class BaseClient(BaseComm):
    """Client creating a connection to a (remote) server.
    Allows to set the connection timeout. Other non-blocking timeout should be
     handled with connect_and_run()'s timeout parameter (select based timeout).

    [Dev Note: Remember it's impossible to use the file interface of the socket
     while setting a socket timeout.]
    """
    def __init__(self, addr_port):
        BaseComm.__init__(self)
        self.family, self.addr_port = get_conn_infos(addr_port)
        self.socket = None
        self.connect_timeout = None	# blocking

    def set_connect_timeout(self, timeout):
        """Sets the timeout connecting to a server.
        Use
        """
        self.connect_timeout = timeout
        # self.socket.settimeout(timeout)

    def get_connect_timeout(self):
        """Gets the timeout connecting to a server.
        """
        return self.connect_timeout
        # return self.socket.gettimeout()

    def handle_connect_timeout(self):
        """Callback for timeout on connection.
        """
        LOG.debug('timeout connecting to remote server %s', self.addr_port)

    def handle_connect_error(self, e):
        """Callback for error on waiting for input.
        """
        LOG.debug('error connecting to server %s (%s)', self.addr_port, e)

    def handle_connect(self):
        """Callback for client successful connection to (remote) server.
        """
        LOG.debug('client connected to remote server %s', self.addr_port)

    def disconnect(self):
        """Set flag for disconnection.
        You need to set a timeout to connect_and_run() or read_until_done().
        """
        self.running = False

    def connect(self):
        """Creates a new connection to a server.
        Returns:
        """
        assert self.connected is False, 'connecting while connected ?'
        LOG.debug('connecting to %s:%s (for %s)', self.addr_port[0],
                  self.addr_port[1], (self.connect_timeout is None and 'ever')
                  or str(self.connect_timeout)+'s.')
        try:
            self.socket = socket.socket(self.family)
            self.socket.settimeout(self.connect_timeout)
            self.socket.connect(self.addr_port)
        except socket.timeout:
            self.handle_connect_timeout()
        except socket.error, e:
            self.handle_connect_error(e)
        else:
            self.connected = True
            self.handle_connect()
            return True
        self.socket = None
        return False

    def connect_and_run(self, timeout=0.01):
        """High Level communication processing: blocks until connected and run()
         returns. You can interrupt the connection loop in handle_error().
        timeout: delay in seconds before giving up waiting for data (select).
        Returns: True if disconnected normally, False on error.
        """
        self.running = True
        while self.running and not self.connect():
            pass
        if not self.connected:
            return False
        try:
            self.read_while_running(timeout)
            ret = True
        except select.error, e:
            self.handle_error(e)
            ret = False
        finally:
            if self.socket:
                self.socket.close()
            self.connected = False
            self.handle_disconnect()
        return ret


def set_default_logging(debug=False):
    """This function does nothing if the root logger already has
    handlers configured.
    """
    log_lvl = (debug and logging.DEBUG or logging.INFO)
    logging.basicConfig(level=log_lvl, format=LOGFORMAT)
    LOG.setLevel(log_lvl)
    LOG.info('Logger[%s] set log level to %s',
             LOG.name, debug and 'DEBUG' or 'INFO')


def get_conn_infos(addr_port):
    """
    """
    LOCALHOSTS = ["127.0.0.1", "localhost"]
    if hasattr(socket, "AF_UNIX") and type(addr_port[1]) is type(""):
        if addr_port[0] and addr_port[0] not in LOCALHOSTS:
            raise ProtcolError('address must be null or one of %s', LOCALHOSTS)
        return socket.AF_UNIX, addr_port[1]
    return socket.AF_INET, addr_port


if __name__ == '__main__':
    THREADED_SERVER  = False
    THREADED_CLIENTS = False
    THREAD_INFO = (THREADED_SERVER, THREADED_CLIENTS)

    set_default_logging(debug=True)

    class TestS(object): pass
    class TestH(object): pass

    server = create_server(TestS, TestH, ('localhost',2121), THREAD_INFO)
    server.start()
    if not THREADED_SERVER:
        while server.serve_once():
            pass
