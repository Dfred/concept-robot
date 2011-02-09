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

# protocol keywords to switch from a subserver/handler to another
ORIGINS = ('face', 'gaze', 'lips', 'head')

# submodule key for registering more protocol keywords for a subserver/handler
EXTRA_ORIGINS = 'extra_origins'


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
        self.updated = []

    def cmd_origin(self, argline):
        """Set or Send current origin/subhandler"""
        if argline:
            try:
                self.set_current_subhandler(self.handlers[argline])
                self.updated.append(argline)
            except KeyError:
                LOG.warning('unknown origin: %s', argline)
        else:
            self.send_msg("origin is %s" % self.curr_handler)

    def cmd_commit(self, argline):
        """Marks end of a transaction"""
        for origin in self.updated:
            self.handlers[origin].cmd_commit(argline)
        self.updated = []

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
        self.origins = {}       # { origin: self.server and associed handler }
        self.FP = FeaturePool() # the feature pool for context queries

    def __getitem__(self, protocol_keyword):
        return self.origins[protocol_keyword][0]
    get_server = __getitem__

    def get_handler(self, keyword):
        return self.origins[keyword][1]

    def get_server(self, keyword):
        return self.origins[keyword][0]

    def register(self, server, req_handler_class, origin):
        """Binds origin keyword with server and relative request handler."""
        if origin not in ORIGINS:
            LOG.error("rejecting unknown origin '%s'", origin)
            return
        LOG.debug("registering server %s & handler class %s for origin '%s'",
                  server, req_handler_class, origin)
        self.origins[origin] = server, MetaServer.register(self, server,
                                                           req_handler_class)

    def create_protocol_handlers(self):
        """Bind individual servers and their handler to the meta server.
        This function uses conf's module definitions: if conf has an attribute
         which name can be found in ORIGINS, then the HRI module is loaded.
         """
#TODO:        See more info in the documentation.
#        """
        # conf's specifics should have been sorted out much earlier
        import conf; conf.load()

        # check for mod_... attributes, allowing a submodule to register more
        #  than one ORIGIN keyword with its extra_origins attribute.
        for info, name in [ (getattr(conf,name), name[4:]) for name in dir(conf)
                            if name.startswith('mod_') ]:
            try:
                module = __import__(name)
            except ImportError:
                LOG.info("Found %s's config but couldn't load that HRI module",
                         name)
                continue
            try:
                subserv_class = getattr(module, name.capitalize()+'_Server')
                handler_class = getattr(module, name.capitalize()+'_Handler')
            except AttributeError, e:
                raise conf.LoadException("Module %s: Missing mandatory classes"
                                         "(%s)" % (name, e))
            subserver = self.create_subserver(subserv_class)
            self.register(subserver, handler_class, name)
            if info.has_key(EXTRA_ORIGINS):
                for origin in info[EXTRA_ORIGINS]:
                    self.register(subserver, handler_class, origin)
        if not self.origins:
            raise conf.LoadException("No submodule found in configuration.")
        missing = [ o for o in ORIGINS if o not in self.origins ]
        if missing:
            LOG.warning("Missing submodules: "+"%s, "*len(missing), *missing)


def initialize(thread_info):
    """Initialize the system.
    thread_info: tuple of booleans setting threaded_server and threaded_clients
    """
    import sys
    print "LIGHTHEAD Animation System, python version:", sys.version

    # check configuration
    try:
        import conf; missing = conf.load()
        if missing:
            fatal('missing configuration entries: %s' % missing)
        if hasattr(conf, 'DEBUG_MODE') and conf.DEBUG_MODE:
            # set system-wide logging level
            import comm; comm.set_default_logging(debug=True)
    except conf.LoadException, e:
        fatal('in file {0[0]}: {0[1]}'.format(e)) 

    # Initializes the system
    import comm
    from lightHead_server import lightHeadServer, lightHeadHandler
    server = comm.create_server(lightHeadServer, lightHeadHandler,
                                conf.lightHead_server, thread_info)
    # Because what we have here is a *meta server*, we need to initialize it
    #  properly; face and all other subservers are initialized in that call
    server.create_protocol_handlers()
    return server
