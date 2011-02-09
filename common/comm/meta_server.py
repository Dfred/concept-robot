import types
import logging

import comm

LOG = logging.getLogger(__package__)

class MetaRequestHandler(object):
    """Remote Client Handler.
    Represents a single remote client, so no thread-safety issues here.
    """

    def __init__(self):
        self.curr_handler = None

    def create_subhandler(self, srv, subhandler_class):
        """Equivalent of create_subserver.
        Basically we emulate the basics of SocketServer.BaseRequestHandler and 
        """
        subhandler = subhandler_class()
        subhandler.socket = self.socket
        subhandler.addr_port = self.addr_port
        subhandler.server = srv
        subhandler.send_msg = types.MethodType(comm.BaseComm.send_msg,
                                               subhandler, subhandler_class)
        return subhandler

    def set_current_subhandler(self, handler):
        self.curr_handler = handler

    def handle_notfound(self, cmd, argline):
        """Routes cmd_ functions to the current handler.
        """
        if not self.curr_handler:
            LOG.debug("unset current handler and no %s() in %s", cmd, self)
            return
        try:
            fct = getattr(self.curr_handler, cmd)
        except AttributeError:
            LOG.info("%s has no function '%s'", self.curr_handler, cmd)
        except :
            raise
        else:
            fct(argline)

    def cmd_list(self, argline):
        """list all available commands"""
        cmds = []
        for obj in (self, self.curr_handler):
            cmds.append( [a[4:] for a in dir(obj) if a.startswith('cmd_')] )
        cmds[1] = filter(lambda x: x not in cmds[0], cmds[1])
        self.send_msg('commands:\t{0[0]}\nextra commands:\t{0[1]}'.format(cmds))



class MetaServer(object):
    """A server that gathers other servers and their handlers.
    Allows multiple protocols to be mixed together. Indeed you would need a 
     higher protocol in order to switch from one protocol to the other.
    """

    def __init__(self):
        self.servers_SHclasses = {}

    def register(self, server, handler_class):
        """Adds a server and its request handler class to the meta server .
        On connection, self.clients adds an instance of request_handler_class .
        """

        def meta_subhandler_init(self):
            """Provides the handler with BaseComm.send_msg()"""
            LOG.debug('initializing compound handler %s', self.__class__)
            comm.BaseComm.__init__(self)
            handler_class.__init__(self)

        commHandler_class = type(handler_class.__name__+'BaseComm',
                                 (handler_class, comm.BaseComm),
                                 {'__init__':meta_subhandler_init,
                                  'server':server} )
        self.servers_SHclasses[server] = commHandler_class
        return commHandler_class

    def unregister(self, server):
        """Removes a registered server."""
        try:
            del self.servers_SHclasses[server]
        except KeyError:
            return False
        return True

    def create_subserver(self, server_class):
        """Equivalent of create_server for a meta server.
        Basically we get rid of SocketServer.
        """
        def meta_subserver_init(self):
            LOG.debug('initializing compound server %s', self.__class__)
            comm.BaseServer.__init__(self)
            server_class.__init__(self)

        return type(server_class.__name__+'BaseServer',
                    (server_class, comm.BaseServer),
                    {'__init__':meta_subserver_init} )()
