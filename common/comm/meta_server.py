import logging
LOG = logging.getLogger(__package__)


class MetaRequestHandler(object):
    """
    """

    def setup(self):
        import comm;
        comm.RequestHandler.setup(self)
        self.curr_handler = None

    def handle_notfound(self, cmd, argline):
        # TODO: use __getattr__ to route the calls
        """Routes cmd_ functions to the current handler .
        """
        if not self.curr_handler:
            LOG.debug("unset current handler and no %s() in %s", cmd, self)
            return
        try:
            fct = getattr(self.curr_handler, cmd)
        except :
            LOG.info("%s has no function '%s'", self.curr_handler, cmd)
            raise
        else:
            fct(argline)


class MetaServer(object):
    """A server that gathers other servers and their handlers.
    Allows multiple protocols to be mixed together. Indeed you would need a 
     higher protocol in order to switch from one protocol to the other.
    """

    def __init__(self):
        self.servers = []
        self.handlers = []

    def register(self, server, request_handler):
        """Adds a server and its request handler to the meta server .
        Returns the index of the new entry in self.servers .
        """
        request_handler.server = server
        self.servers.append(server)
        self.handlers.append(request_handler)
