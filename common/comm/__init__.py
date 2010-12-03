#!/usr/bin/python

# Lighthead-bot programm is a HRI PhD project at the University of Plymouth,
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
Copyright (C) 2009 frederic DELAUNAY, University of Plymouth (UK).
"""
"""
A fully functional template server and associated client talking ASCII:
Provides async socket-based communication layer for modules + logging support.
Look at exemple.py for an overview.

recognized module communication arguments:
client mode: [module_id=ip_address:port]
server mode: [interface_address:port]
"""

__author__  = "frederic Delaunay f dot d at chx-labs dot org"
__status__  = "beta"
__version__ = "0.3"
__date__    = "$$"

import os
import socket
import select
import logging
from threading import Thread, Lock

LOGFORMAT = "%(lineno)4d:%(filename).21s\t-%(levelname)s-\t%(message)s"
# create our logging object and set log format
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
    """Exception for dealing with type generation"""
    pass


class BaseServer(object):
    """Allows using a single threaded approach, inspired from SocketServer.
    See set_manual()'s docstring for how to use it.
    Also allows user classes not to inherit from anything (see create_server() )
    """
    def __init__(self, threaded=False):
        self.handler_looping = True     # default looping behaviour for RequestHandler
        self.handler_timeout = 0
        self.listen_timeout = 0.5
        self.__threaded = threaded
        self.__running = False
        if threaded:
            self.__is_shut_down = threading.Event()
        self.clients = {}       # { fd : handler object }
        self.polling_sockets = None  # array of sockets polled in this thread

    def set_addrPort(self, addrPort):
        self.addr_port = addrPort

    def set_requestHandlerClass(self, ClientHandlerClass):
        self.RequestHandlerClass = ClientHandlerClass

    def set_listen_timeout(self, listen_timeout):
        """Sets socket timeout for incoming connections."""
        self.listen_timeout = listen_timeout
        if self.__running:
            self.socket.settimeout(listen_timeout)
            self.update_poll_timeout()

    def set_handler_timeout(self, timeout):
        """Sets new handlers' socket timeout."""
        self.handler_timeout = timeout

    def update_poll_timeout(self):
        self.poll_interval = min([sock.gettimeout() for sock in \
                                      self.polling_sockets + [self.socket]])

    def activate(self):
        """To be overriden"""
        pass

    def disactivate(self):
        """To be overriden"""
        pass

    def start(self):
        """Starts the server (listen to connections)"""
        self.__running = True
        self.activate()
        self.polling_sockets = [self.socket]
        self.update_poll_timeout()
        if self.__threaded:
            self.thread = Thread(target=G.server.serve_forever, name='server')
            self.thread.start()
        LOG.info("server started in %s-thread mode",
                 self.__threaded and 'multi' or 'single')

    def shutdown(self):
        """Stops the server."""
        LOG.info("%s> stopping server", self.socket.fileno())
        self.__running = False
        if self.__threaded:
            self.__is_shut_down.wait()
            self.thread.join()
        else:
            for fd, client in self.clients.iteritems():
                client.finish()
                if client.socket in self.polling_sockets:
                    self.close_request(client.socket)
        self.disactivate()

    def serve_once(self):
        """Check for incoming connections and saves further calls to select()
         for that thread."""
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
                if sock == self.socket:
                    self._handle_request_noblock()
                elif not self.clients[sock.fileno()].read_socket():
                    self.close_request(sock)
        except Exception, err:
            return self.handle_error(self.polling_sockets, None)
        return True

    def serve_forever(self):
        """Blocking call. Inspired from SocketServer.
        """
        if self.__threaded:
            self.__is_shut_down.clear()
        try:
            while self.__running and self.serve_once():
                pass
        finally:
            self.__running = True
            if self.__threaded:
                self.__is_shut_down.set()

    def _handle_request_noblock(self):
        """Handle one request, non-blocking. Inspired from SocketServer
        assumption: socket is readable, get_request() is non-blocking.
        """
        try:
            socket, client_address = self.get_request()
        except socket.error:
            return self.handle_error(socket, client_address)
        if self.verify_request(socket, client_address):
            try:
                self.process_request(socket, client_address)
            except:
                self.handle_error(socket, client_address)
                self.close_request(socket)

    def handle_error(self, sock, client_addr):
        """Installs an interactive pdb session if logger is at DEBUG level"""
        LOG.error('Exception raised with %s (%s)', sock, client_addr)
        if LOG.getEffectiveLevel() != logging.DEBUG:
            print 'use debug mode to spawn post-mortem analysis with pdb'
        else:
            import pdb, traceback
            print '===EXCEPTION CAUGHT'+'='*60
            traceback.print_exc()
            pdb.post_mortem()

    def verify_request(self, request, client_address):
        """Verify the request.  May be overridden.
        Return True if we should proceed with this request."""
        return True

    def finish_request(self, sock, client_addr):
        """Instanciates the RequestHandler and set its connection timeout."""
        LOG.debug('new connection request from %s (%s)', client_addr, sock)
        handler = self.RequestHandlerClass()
        handler.set_server(self)
        handler.set_channel(sock, client_addr)
        sock.settimeout(self.handler_timeout)
        return handler

    def process_request(self, sock, client_address):
        """Creates a new client. Overridden by ForkingMixIn and ThreadingMixIn.
        """
        handler = self.finish_request(sock, client_address)
        self.polling_sockets.append(sock)
        self.update_poll_timeout()
        self.clients[sock.fileno()] = handler

    def close_request(self, sock):
        """Cleans up an individual request. Extend but don't override."""
        LOG.debug('closing connection with %s (%s)',
                  self.clients[sock.fileno()].addr_port, sock)
        del self.polling_sockets[self.polling_sockets.index(sock)]
        del self.clients[sock.fileno()]
        self.update_poll_timeout()

    def set_auto(self):
        """Restores functions hooked by set_manual
        """
        self.handler_looping = True
        if hasattr(self, '_fr'):
            self.finish_request = self._fr
            self.close_request = self._cr

    def set_manual(self):
        """Hooks finish_request and close_request for SocketServer to behave as
        we want:
        * not blocking in the Handler's __init__
        * not closing connection after __init__
        """
        self.handler_looping = False
        self._fr = self.finish_request
        self.finish_request = self._finish_request
        self._cr = self.close_request
        self.close_request  = self._close_request
        # obj = self
        # cls = obj.__class__
        # import types
        # # disable closing of socket while we're still on it (ugly, I know..)
        # obj.finish_request = types.MethodType(BaseServer._finish_request,obj,cls)
        # obj.close_request  = types.MethodType(BaseServer._close_request, obj,cls)
        LOG.debug('overriden finish_request and close_request')

    def threadsafe_start(self):
        """Transparent threading support."""
        """When handlers are threaded, it's good to have a way to sync them."""
        pass

    def threadsafe_stop(self):
        """Transparent threading support."""
        pass


class TCPServer(BaseServer):
    """Base class for various socket-based server classes. Inspired from SocketServer.
    Defaults to synchronous IP stream (i.e., TCP).

    Methods that may be overridden:

    - server_bind()
    - server_activate()
    - get_request() -> request, client_address
    - handle_timeout()
    - verify_request(request, client_address)
    - process_request(request, client_address)
    - close_request(request)
    - handle_error()

    Methods for derived classes:

    - finish_request(request, client_address)

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
        """Called by constructor to activate the server. May be overridden."""
        self.socket = socket.socket(self.address_family,
                                    self.socket_type)
        self.socket.settimeout(self.listen_timeout)
        if self.allow_reuse_address:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.addr_port)
        self.addr_port = self.socket.getsockname()
        self.socket.listen(self.request_queue_size)

    def disactivate(self):
        """Called to clean-up the server. May be overridden."""
        self.socket.close()

    def fileno(self):
        """Return socket file number. Interface required by select()."""
        return self.socket.fileno()

    def get_request(self):
        """Get the request and client address from the socket. May be overridden."""
        return self.socket.accept()

    def close_request(self, socket):
        """Called to clean up an individual request."""
        BaseServer.close_request(self, socket)
        socket.close()


class UDPServer(TCPServer):
    """UDP server class."""

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
        pass

class ForkingMixIn:
    """Mix-in class to handle each request in a new process."""

    timeout = 300
    active_children = None
    max_children = 40

    def collect_children(self):
        """Internal routine to wait for children that have exited."""
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
                raise ValueError('%s. x=%d and list=%r' % (e.message, pid,
                                                           self.active_children))

    def handle_timeout(self):
        """Wait for zombies after self.timeout seconds of inactivity.

        May be extended, do not override.
        """
        self.collect_children()

    def process_request(self, socket, client_address):
        """Fork a new subprocess to process the request."""
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
                self.finish_request(socket, client_address)
                os._exit(0)
            except:
                try:
                    self.handle_error(socket, client_address)
                finally:
                    os._exit(1)

class ThreadingMixIn:
    """Mix-in class to handle each request in a new thread."""

    # Decides how threads will act upon termination of the
    # main process
    daemon_threads = False

    def process_request_thread(self, socket, client_address):
        """Same as in BaseServer but as a thread.
        In addition, exception handling is done here.
        """
        try:
            self.finish_request(socket, client_address)
            self.close_request(socket)
        except:
            self.handle_error(socket, client_address)
            self.close_request(socket)

    def process_request(self, socket, client_address):
        """Start a new thread to process the request."""
        t = threading.Thread(target = self.process_request_thread,
                             args = (socket, client_address))
        if self.daemon_threads:
            t.setDaemon (1)
        t.start()


class ForkingUDPServer(ForkingMixIn, UDPServer): pass
class ForkingTCPServer(ForkingMixIn, TCPServer): pass

class ThreadingUDPServer(ThreadingMixIn, UDPServer): pass
class ThreadingTCPServer(ThreadingMixIn, TCPServer): pass

#
# addition
# { type of port : { proto : { threading : class } } }
#
SERVER_CLASSES = {
    type(42): {'udp': { True : ThreadingUDPServer,
                        False: UDPServer },
               'tcp': { True : ThreadingTCPServer,
                        False: TCPServer }
               } }

if hasattr(socket, 'AF_UNIX'):
    class UnixStreamServer(TCPServer):   address_family = socket.AF_UNIX
    class UnixDatagramServer(UDPServer): address_family = socket.AF_UNIX
    class ThreadingUnixStreamServer(ThreadingMixIn, UnixStreamServer): pass
    class ThreadingUnixDatagramServer(ThreadingMixIn, UnixDatagramServer): pass
#
# And of pure reuse
#
    SERVER_CLASSES[type('')] = { '':{ True : ThreadingUnixStreamServer,
                                      False: UnixStreamServer } }

       
class BaseComm(object):
    """Basic protocol handling and command-to-function resolver. This is the
     base class for a local client connecting to a server (BaseClient) or for a
     handler of a remote client connecting to the local server (RequestHandler).
     This class only relies on socket's fileno() function.
    """

    CMD_PREFIX = "cmd_"

    def __init__(self):
        self.command = ''

    def abort(self):
        """For read_while_running"""
        LOG.debug("communication has been interrupted")
        self.running = False
        return False

    def read_once(self, timeout=0.05):
        """Non-blocking call for processing client commands (see __init__).
        Replaces handle()
        No check for self.running.
        Return: False on error
        """
        r, w, e = select.select([self.socket], [], [self.socket], timeout)
        if not r:
            return True
        if e:
            self.handle_error('Unknown error with socket %s' % e)
            return self.abort()
        return self.read_socket()

    def read_socket(self):
        """Read its own socket."""
        try:
            buff = self.socket.recv(1024)
            if not buff:
                return self.abort()
            self.command += buff
        except socket.error, e:
            self.handle_error(e)
            return self.abort()
        self.command = self.command[self.process(self.command):]
        return True

    def read_while_running(self):
        """Blocking call for processing of client commands (see __init__).
        Returns if self.running is False.
        """
        self.running = True
        while self.running and self.read_once():
            pass

    def handle_notfound(self, cmd, args):
        """When a method (a command) is not found in self. See process().
        To be overriden.
        """
        LOG.debug("function %s not found in %s [args: '%s']", cmd, self, args)

    def handle_error(self, e):
        """Callback for connection error.
        """
        LOG.warning("Connection error :%s", e)

    def parse_cmd(self, cmdline):
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
        """Command dispatcher function.

        Tokenize command and calls 'cmd_ + 1st_token' function defined in self.
         Calls self.handle_notfound if the built function name isn't defined.
         Function is called with remaining tokens (array) as one argument.
         Simultaneous commands (called within the same step) can be issued
          linking them with '&&'.

        command: string of text to be parsed
        Returns the number of bytes read.
        """        
        length = 0
        buffered = ''
        LOG.debug("%s> command [%iB]: '%s'",
                  self.socket.fileno(), len(command), command)

        for cmdline in command.splitlines(True):
            length += len(cmdline)
            cmdline = cmdline.strip()
            if not cmdline or cmdline.startswith('#'):
                continue
            if cmdline.endswith('\\'):
                buffered += cmdline[:-1]
                continue
            cmdline = buffered + cmdline
            buffered = ''
            for cmd in cmdline.split('&&'):
                self.parse_cmd(cmd)
        return length

    def send_msg(self, msg):
        """Sends msg with a trailing \\n as required by the protocol."""
        LOG.debug("sending %s\n", msg)
        self.socket.send(msg+'\n')

    def cmd_bye(self, args):
        """Disconnects that client."""
        self.running = False
    cmd_EOF = cmd_bye
        

class RequestHandler(BaseComm):
    """Instancied on successful connection to the server: a remote client.

    Reads data from self.request and adds default functions :
     cmd_shutdown, cmd_clients and cmd_verb.
    If needed, define your own protocol handler overriding BaseComm.process.
    """

    def set_channel(self, socket, addr_port):
        self.socket = socket
        self.addr_port = addr_port

    def set_server(self, server):
        self.server = server

    def run(self):
        try:
            self.setup()
            self.work()
            self.finish()
        finally:
            import sys
#            sys.exc_traceback = None    # Help garbage collection

    def setup(self):
        """Overrides SocketServer"""
        # check if we want to block in self.work()
        self.work = self.server.handler_looping and\
            self.read_while_running or self.read_once
        # update addr_port for unix sockets (another crazy thing!)
        self.addr_port = type(self.addr_port) == type("") and \
            ("localhost", "UNIX Socket") or self.addr_port
        LOG.info("%i> connection accepted from %s on %s. Client is %slooping",
                 self.socket.fileno(), self.addr_port[0], str(self.addr_port[1]),
                 self.work == self.read_once and '*NOT* ' or '')

    def finish(self):
        """Overrides SocketServer"""
#        if not self.server.handler_looping:
#            return
        LOG.info("%i> connection terminated : %s on "+str(self.addr_port[1]),
                 self.socket.fileno(), self.addr_port[0])

    def cmd_shutdown(self, args):
        """Disconnects all clients and terminate the server process."""
        if self.server == None:
            raise CmdError("cannot shutdown server")
        self.running = False
        self.server.shutdown()

    def cmd_clients(self, args):
        """Lists clients currently connected."""
        LOG.info("%s> listing %i clients.",
                 self.socket.fileno(), len(self.server.clients))
        clients_infos = []
        for fd, cl in self.server.clients.iteritems():
            clients_infos.append( type(cl.addr_port) == type("") and
                                  (fd, "UNIX", "localhost") or
                                  (fd, cl.addr_port[1], cl.addr_port[0]) )
        clients_infos.sort()
        obuffer = "clients: %i connected: (ID, PORT, ADDR)"%(len(clients_infos))
        for client_info in clients_infos:
            obuffer += "\\\n> %s:  %5s  %s" % client_info
        self.send_msg(obuffer)
        
    def cmd_verb(self, args):
        """Changes LOG verbosity level."""
        if not args:
            self.send_msg("CRITICAL 50\nERROR	 40\nWARNING  30\n"
                          "INFO     20\nDEBUG	 10\nNOTSET    0")
        else:
            LOG.warning("changing log level to %s", args[0])
            LOG.setLevel(args[0])
        self.send_msg("verb is %s now" % LOG.getEffectiveLevel())


class BaseClient(BaseComm):
    """Client creating a connection to a (remote) server.

       Remember it's impossible to use the file interface of the socket while
        setting a socket timeout.
    """
    def __init__(self, addr_port):
        BaseComm.__init__(self)
        family, self.target_addr = get_conn_infos(addr_port)
        self.socket = socket.socket(family)
        self.connected = False

    def set_timeout(self, timeout):
        self.socket.settimeout(timeout)

    def disconnect(self):
        """Set flag for disconnection.
        You need to set a timeout to connect_and_run() or read_until_done()"""
        self.running = False

    def connect_and_run(self):
        try:
            self.socket.connect(self.target_addr)
        except socket.error, e:
            self.handle_error(e)
            self.socket.close()
            return
        self.connected = True
        self.handle_connect()

	try:
	    self.read_while_running()
	except select.error, e:
	    self.handle_error(e)
	finally:
            self.socket.close()
            self.connected = False
            self.handle_disconnect()

    def handle_connect(self):
        """Callback for client successful connection to (remote) server.
        """
        LOG.debug('client connected to remote server %s', self.target_addr)

    def handle_timeout(self):
        """Callback for timeout on waiting for input
        Returning False would skip recv()
        """
        pass

    def handle_disconnect(self):
        """Callback after client disconnection to (remote) server.
        """
        LOG.debug('client disconnected from remote server %s', self.target_addr)


def set_default_logging(debug=False):
    """This function does nothing if the root logger already has
    handlers configured."""
    if debug:
        logging.basicConfig(level=logging.DEBUG, format=LOGFORMAT)
    else:
        logging.basicConfig(level=logging.INFO, format=LOGFORMAT)


def get_conn_infos(addr_port):
    if hasattr(socket, "AF_UNIX") and \
            type(addr_port[1]) == type("") and \
            addr_port[0] in ["127.0.0.1", "localhost"]:
        return socket.AF_UNIX, addr_port[1]
    return socket.AF_INET, addr_port


def getBaseServerClass(addr_port, threaded):
    """Returns the appropriate base class for server according to addr_port"""
    """protocol can be specified using a prefix from 'udp:' or 'tcp:' in the
     port field (eg. 'udp:4242'). Default is udp."""
    D_PROTO = 'tcp'
    addr, port = addr_port
    if type(port) == type(''):
        proto, port = port.find(':') > 0 and port.split(':') or (D_PROTO, port)
        if port.isdigit():
            port = int(port)
            addr_port = (addr, port)
    else:
        proto = D_PROTO
    try:
        srv_class = SERVER_CLASSES[type(port)][proto][threaded]
        if type(port) == '' and \
           srv_class == isinstance(srv_class, SocketServer.UnixStreamServer):
            addr_port = addr_port[1]
        LOG.debug('address-port: %s, selected server class: %s',
                  addr_port, srv_class)
        return addr_port, srv_class
    except KeyError:
        raise Exception('No suitable server class from addr_port. Check conf.')


def create_requestHandler_class(handler_class, threaded=False):
    """Creates a new (compound) type of RequestHandler suitable for inclusion to
    a compound server. Users can simply ignore networking in the class code.
    """
    if not issubclass(handler_class, object):
        raise ClassError('class %s must inherit from object' % handler_class)

    def requestHandler_init(self, socket, client_addr, server):
        """Call all subclasses initializers"""
        LOG.debug('initializing compound request handler %s', self.__class__)
        # add runtime support for threading (sending clients)
        if threaded:
            self._threading_lock = Lock()
            def th_send_msg(self, msg):
                self._threading_lock.acquire()
                BaseComm.send_msg(self, msg)
                self._threading_lock.release()
        # most of this mess because it can be done and I have fun doing it
        RequestHandler.__init__(self, socket, client_addr, server)
        handler_class.__init__(self)
        self.run()

    if handler_class != RequestHandler:
        bases = (handler_class, RequestHandler)
    else:
        bases = (RequestHandler,)
    return type(handler_class.__name__+'RequestHandler', bases,
                {"__init__":requestHandler_init})

def create_server(ext_class, handler_class, addr_port, thread_info):
    """Creates a new (compound) type of server according to addr_port, also
     creates a new type of RequestHandler so users don't inherit from anything.

        ext_class: extension class to be a base of the new type.
        handler_class: class to be instancied on accepted connection.
        addr_port: (address, port). port type is relevant, see conf module.
    """
    if not issubclass(ext_class, object):
        raise ClassError('class %s must inherit from object' % ext_class)

    addr_port, base_class = getBaseServerClass(addr_port, thread_info[0])
    mixed_handler_class = create_requestHandler_class(handler_class,
                                                      thread_info[1])
    def server_init(self, addr_port, handler_class):
        """Call all subtypes initializers and add support for threading locks"""
        # add runtime support for threading (accessing server)
        if thread_info[0]:
            self._threading_lock = threading.Lock()
            def threadsafe_start(self):
                self._threading_lock.acquire()
            def threadsafe_stop(self):
                self._threading_lock.release()
        LOG.debug('initializing compound server %s', self.__class__)
        # most of this mess because of parameters in SocketServer.__init__
        base_class.__init__(self, addr_port, handler_class)
        BaseServer.__init__(self)
        ext_class.__init__(self)

    if ext_class != BaseServer:
        bases = (ext_class, BaseServer)
    else:
        bases = (BaseServer,)
    return type(ext_class.__name__+base_class.__name__, bases,
                {"__init__":server_init})(addr_port, mixed_handler_class)


if __name__ == '__main__':
    THREADED_SERVER  = False 
    THREADED_CLIENTS = False
    THREAD_INFO = (THREADED_SERVER, THREADED_CLIENTS)

#    server = create_server(THREAD_INFO)
    server = TCPServer()
    server.set_requestHandlerClass(RequestHandler)
    server.set_addrPort(('localhost',4242))

    set_default_logging(debug=True)
#    import pdb; pdb.set_trace()

    # set timeout for checking incoming connections
    server.set_listen_timeout(0.5)
    server.start()
    if not THREADED_SERVER:
        while server.serve_once():
            pass
