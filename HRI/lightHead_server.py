import logging

from comm.meta_server import MetaRequestHandler, MetaServer

LOG = logging.getLogger(__package__)

ORGN_FACE = 'face'
ORGN_GAZE = 'gaze'
ORGN_LIPS = 'lips'
ORGN_HEAD = 'head'
ORIGINS = (ORGN_GAZE, ORGN_FACE, ORGN_LIPS, ORGN_HEAD)

class lightHeadHandler(MetaRequestHandler):
    """Handles high level protocol transactions: origin and commit"""

    def __init__(self):
        MetaRequestHandler.__init__(self)
        self.handlers = dict([ (k,val[1]) for k,val in \
                                   self.server.origins.iteritems() ])

    def cmd_origin(self, argline):
        if not argline:
            self.send_msg("origin is %s" % self.curr_handler)
        else:
            self.curr_handler = self.handlers[argline]

    def cmd_commit(self, argline):
        for key in ORIGINS:
            self.handlers[key].cmd_commit(argline)

class lightHeadServer(MetaServer):
    """Sets and regroups subservers of the lightHead system."""

    def __init__(self):
        MetaServer.__init__(self)
        self.origins = {}       # { origin: index in self.servers and handlers }

    def __getitem__(self, protocol_keyword):
        return self.origins[protocol_keyword][0]
    get_server = __getitem__

    def get_handler(self, keyword):
        return self.origins[keyword][1]

    def register(self, server, request_handler, origin):
        """bufferize server-handler associations with origin keyword."""
        if origin not in ORIGINS:
            LOG.error("rejecting unknown origin '%s'", origin)
            return
        LOG.debug("registering server %s & handler %s for origin '%s'",
                  server, request_handler, origin)
        MetaServer.register(self, server,request_handler)
        self.origins[origin] = (self.servers[-1], self.handlers[-1])


    def create_protocol_handlers(self):
        """Bind individual servers and their handler to the meta server.
        Upon reception of 'origin' (protocol keyword), it switches to .
        """
        # TODO: use conf for automatic registration
        from face import FaceServer, FaceClient
        server = FaceServer()
        handler = FaceClient()
        self.register(server, handler, 'face')
        self.register(server, handler, 'gaze')
        self.register(server, handler, 'lips')
        from spine import SpineServer, SpineClient
        self.register(SpineServer(), SpineClient(), 'head')

