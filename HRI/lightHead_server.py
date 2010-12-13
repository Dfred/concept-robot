# LightHead-bot programm is a HRI PhD project at 
#  the University of Plymouth,
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


#
# SERVER MODULE
#
# This module listen to control connections and dispatches module-specific
#  commands to the appropriate submodule. Also allows retreiving a snapshot of
#  the current context.
#
# MODULES IO:
#============
# OUTPUT: All HRI modules
#
# INPUT: - learning (for context retrieval)
#

import logging

from comm.meta_server import MetaRequestHandler, MetaServer

LOG = logging.getLogger(__package__)

ORGN_FACE = 'face'
ORGN_GAZE = 'gaze'
ORGN_LIPS = 'lips'
ORGN_HEAD = 'head'
ORIGINS = (ORGN_GAZE, ORGN_FACE, ORGN_LIPS, ORGN_HEAD)


class FeaturePool(object):
    """This class serves as a short term memory. It holds all possible features
    so other modules can query a snapshot of the current robot's state."""

    def __init__(self):
        self.context = {}       # identifier : value(s)

    def is_empty(self):
        return not self.context

    def get_snapshot(self, features=None):
        """Get a snapshot, optionally selecting specific features.
        features == None: return whole context
        features == iterable: return subset of the context.
        """
        print features, self.context
        if not features:
            return self.context
        return dict( (f,self.context[f]) for f in features )

    def set_value(self, identifier, value):
        self.context[identifier] = value


class lightHeadHandler(MetaRequestHandler):
    """Handles high level protocol transactions: origin and commit"""

    def __init__(self):
        MetaRequestHandler.__init__(self)
        self.handlers = {}
        for origin, srv_hclass in self.server.origins.iteritems():
            self.handlers[origin] = self.create_subhandler(*srv_hclass)

    def cmd_origin(self, argline):
        """Set or Send current origin/subhandler"""
        if argline:
            try:
                self.set_current_subhandler(self.handlers[argline])
            except KeyError:
                LOG.warning('unknown origin: %s', argline)
        else:
            self.send_msg("origin is %s" % self.curr_handler)

    def cmd_commit(self, argline):
        """Marks end of a transaction"""
        self.curr_handler.cmd_commit(argline)
#        for key in ORIGINS:
#            if self.handlers.has_key(key):
#                self.handlers[key].cmd_commit(argline)

    def cmd_reload(self, argline):
        """Reload subserver modules"""
        self.send_msg('TODO')

    def cmd_get_snapshot(self, argline):
        """Returns the current snapshot of robot context"""
        if self.server.FP.is_empty():
            for origin in self.server.origins.iterkeys():
                subserver = self.server.get_server(origin)
                self.server.FP.set_value(origin, subserver.get_features(origin))
        for k,v in self.server.FP.get_snapshot(argline.split()).iteritems():
            if v and hasattr(v, '__iter__'):
                v = [ str(i) for i in v ]
            self.send_msg(k+' '+' '.join(v))
        self.send_msg('end_snapshot')


class lightHeadServer(MetaServer):
    """Sets and regroups subservers of the lightHead system."""

    def __init__(self):
        """All subServers will receive a reference to the Feature Pool"""
        MetaServer.__init__(self)
        self.origins = {}       # { origin: index in self.servers and handlers }
        self.FP = FeaturePool() # the feature pool for context queries

    def __getitem__(self, protocol_keyword):
        return self.origins[protocol_keyword][0]
    get_server = __getitem__

    def get_handler(self, keyword):
        return self.origins[keyword][1]

    def get_server(self, keyword):
        return self.origins[keyword][0]

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

        try:
            from spine import Spine, SpineComm, SpineError
        except ImportError, e:
            LOG.warn('!!! spine backend not available. spine not included !!!')
            return
        try:
            server = self.create_subserver(Spine)
        except SpineError, e:
            LOG.error('spine connection error', e)
        self.register(server, SpineComm, 'head')

