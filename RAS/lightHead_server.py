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
SERVER MODULE

 This module listen to control connections and dispatches module-specific
  commands to the appropriate submodule. Also allows retreiving a snapshot of
  the current context.

 MODULES IO:
============
 OUTPUT: All RAS modules

 INPUT: - learning (for context retrieval)
"""

import sys

from utils.comm.meta_server import MetaRequestHandler
from utils.comm import ASCIICommandProto
from utils import get_logger, conf
from RAS import FeaturePool

LOG = get_logger(__package__)
ORIGINS = ('face', 'gaze', 'lips', 'spine', 'dynamics') # protocol keywords


class LightHeadHandler(MetaRequestHandler, ASCIICommandProto):
    """Handles high level protocol transactions: origin and commit"""

    def __init__(self, server, sock, client_addr):
        super(LightHeadHandler,self).__init__(server, sock, client_addr)
        self.handlers = {}                              # {origin : subhandler}
        self.transacting = None                         # current transaction
        for origin, srv_hclass in self.server.origins.iteritems():
            self.handlers[origin] = self.create_subhandler(*srv_hclass)

    def cmd_origin(self, argline):
        """Set or Send current origin/subhandler"""
        if argline:
            argline = argline.strip()
            try:
                self.set_current_subhandler(self.handlers[argline])
                self.transacting = argline
            except KeyError:
                LOG.warning("unknown origin: '%s'", argline)
        else:
            self.send_msg("origin is %s" % self.curr_handler)

    def cmd_commit(self, argline):
        """Marks end of a transaction"""
        self.handlers[self.transacting].cmd_commit(argline)
        self.transacting = None

    # TODO: implement a reload of modules ?
    def cmd_reload(self, argline):
        """Reload subserver modules"""
        self.send_msg('Not yet implemented')

    def cmd_get_snapshot(self, argline):
        #TODO: use pickle: human readable doesn't make much sense for snapshots.
        """Returns the current snapshot of robot context
        argline: origins identifying arrays to be sent.
        """
        origins = ( argline.strip() and [ o.strip() for o in argline.split()
                                        if o in self.server.FP.keys() ]
                    ) or self.server.FP.keys()
#        for k,v in self.server.FP.get_snapshot(origins).iteritems():
#            self.send_msg(k+' '+' '.join(v))
        for o in origins:
            self.send_msg('snapshot %s %s' % (o, self.server.FP[o].__repr__().replace('\n', ' ')))


class LightHeadServer(object):#MetaServerMixin):
    """Sets and regroups subservers of the lightHead system."""

    def __init__(self):
        """All subServers will receive a reference to the Feature Pool"""
        super(LightHeadServer,self).__init__()
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
        """Binds origin keyword with server and relative request handler.
        """
        if origin not in ORIGINS:
            LOG.error("rejecting unknown origin '%s'", origin)
            return
        LOG.debug("registering server %s & handler class %s for origin '%s'",
                  server, req_handler_class, origin)
        self.origins[origin] = server, req_handler_class
        #self.origins[origin] = server, super(LightHeadServer,self).register(
        #    server, req_handler_class)

    def create_protocol_handlers(self):
        """Bind individual servers and their handler to the meta server.
        This function uses conf's module definitions: if conf has an attribute
         which name can be found in ORIGINS, then that RAS module is loaded.
         """
        EXTRA_ORIGINS = 'extra_origins'
        try:
            r_dict = conf.ROBOT
        except AttributeError:
            LOG.error("ROBOT dictionnary not found in configuration file")
            return

        # check for attributes, allowing a submodule to register more
        #  than one ORIGIN keyword with its extra_origins attribute.
        for name, info in r_dict.iteritems():
            if not name.startswith('mod_') or not r_dict[name]:
                continue
            name = name[4:]
            try:
                module = __import__('RAS.'+name, fromlist=['RAS'])
            except ImportError, e:
                LOG.error("Configuration mentions 'mod_%s' but this module"
                          " can't be loaded. Error: %s", name, e)
                sys.exit(3)
            try:
                subserv_class = getattr(module, 'get_server_class')()
                handler_class = getattr(module, name.capitalize()+'_Handler')
            except AttributeError, e:
                # Consider that missing class just means no subserver
                LOG.warning("Module %s: Missing mandatory classes (%s)" %
                            (name, e))
                continue
            subserver = subserv_class()
#            subserver = self.create_subserver(subserv_class)
            self.register(subserver, handler_class, name)
            if info.has_key(EXTRA_ORIGINS):
                for origin in info[EXTRA_ORIGINS]:
                    self.register(subserver, handler_class, origin)
        if not self.origins:
            raise conf.LoadException("No submodule configuration.")
        missing = [ o for o in ORIGINS if o not in self.origins ]
        if missing:
            LOG.warning("Missing submodules: "+"%s, "*len(missing), *missing)
