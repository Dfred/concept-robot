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
        self.handlers = {}
        for origin, srv_hclass in self.server.origins.iteritems():
            self.handlers[origin] = self.create_subhandler(*srv_hclass)

    def cmd_origin(self, argline):
        if not argline:
            self.send_msg("origin is %s" % self.curr_handler)
        else:
            self.set_current_subhandler(self.handlers[argline])

    def cmd_commit(self, argline):
        for key in ORIGINS:
            if self.handlers.has_key(key):
                self.handlers[key].cmd_commit(argline)

    def cmd_reload(self, argline):
        """reload subserver modules"""
        self.send_msg('TODO')


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

    def register(self, server, request_handler_class, origin):
        """bufferize server-handler associations with origin keyword."""
        if origin not in ORIGINS:
            LOG.error("rejecting unknown origin '%s'", origin)
            return
        LOG.debug("registering server %s & handler class %s for origin '%s'",
                  server, request_handler_class, origin)
        MetaServer.register(self, server, request_handler_class)
        self.origins[origin] = self.servers_SHclasses[-1]


    def create_protocol_handlers(self):
        """Bind individual servers and their handler to the meta server."""
        # TODO: use conf for automatic registration

        from face import Face, FaceComm
        server = self.create_subserver(Face)
        self.register(server, FaceComm, 'face')
        self.register(server, FaceComm, 'gaze')
        self.register(server, FaceComm, 'lips')

        import conf
        if not hasattr(conf, 'conn_head'):
            return
        from spine import Spine, SpineComm, SpineError
        try:
            server = self.create_subserver(Spine)
        except SpineError, e:
            LOG.error('spine connection error', e)
        self.register(server, SpineComm, 'head')

