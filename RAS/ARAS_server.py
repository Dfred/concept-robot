#!/usr/bin/python
# -*- coding: utf-8 -*-

# ARAS is a programm part of CONCEPT, a HRI PhD project at the University
#  of Plymouth. ARAS is a Robotic Animation System including face, eyes,
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
 -----------
 OUTPUT: All RAS modules

 INPUT: - learning (for context retrieval)
"""

import sys
import logging
from collections import deque
import cPickle as pickle

from utils.comm.meta_server import MetaRequestHandler
from utils.comm import ASCIICommandProto
from utils import conf
from RAS.au_pool import FeaturePool
from RAS.supported import ORIGINS

LOG = logging.getLogger(__package__)


class ARASHandler(MetaRequestHandler, ASCIICommandProto):
  """Handles high level protocol transactions: origin and commit"""

  def __init__(self, server, sock, client_addr):
    """
    """
    super(ARASHandler,self).__init__(server, sock, client_addr)
    self.fifos = {}                                 # for cmd_AU
    self.handlers = {}                              # {origin : subhandler}
    self.transacting = []                           # transacting origins
    for origin, (srv,hnd_class) in self.server.origins.iteritems():
      self.handlers[origin] = self.create_subhandler(srv,hnd_class)
      if not self.fifos.has_key(srv):
        self.fifos[srv] = deque()

  def cmd_origin(self, argline):
    """Set or replies with current origin/subhandler"""
    if argline:
      argline = argline.strip()
      try:
        self.set_current_subhandler(self.handlers[argline])
        self.transacting.append(argline)
      except KeyError:
        LOG.warning("unknown origin: '%s'", argline)
    else:
      self.send_msg("%s" % self.curr_handler.__class__.__name__)

  def cmd_AU(self, argline):
    """Updates an AU. Careful: origin is not taken into account here!
    argline: AU_name  target_value  duration.
    """
    try:
      au_name, value, duration = argline.split()[:3]
    except ValueError:
      LOG.error("[AU] wrong number of arguments (%s)", argline)
      return
    try:
      value, duration = float(value), float(duration)
    except ValueError,e:
      LOG.error("[AU] invalid float (%s)", e)
      return
    for server, fifo in self.fifos.iteritems():
      if server.AUs.has_key(au_name):
        fifo.append([au_name, value, duration])
        return
      elif server.AUs.has_key(au_name+'R'):
        fifo.extend([ [au_name+'R',value,duration],
                      [au_name+'L',value,duration] ])
        return
    LOG.warning("[AU] %s isn't supported", au_name)

  def cmd_commit(self, argline):
    """Marks end of a transaction"""
    for srv, fifo in self.fifos.iteritems():
      if fifo:
        srv.commit_AUs(fifo)
        fifo.clear()
    for origin in self.transacting:
      if hasattr(self.handlers[origin], 'cmd_commit'):
        self.handlers[origin].cmd_commit(argline)
    self.transacting = []

  # TODO: implement a reload of modules ?
  def cmd_reload(self, argline):
    """Reload subserver modules"""
    self.send_msg('Not yet implemented')

  def cmd_get_snapshot(self, argline):
    """Returns the current snapshot of the robot's state.
    argline: optional 'ASCII' for clear text + identifiers of arrays to be sent.
    """
    args = argline.split()
    binary = True
    if args and args[0] == 'ASCII':
      binary = False
      args.pop(0)
    origins = (args and [o.strip() for o in args if o in self.server.FP.keys()]
               ) or self.server.FP.keys()
    snapshot = self.server.FP.get_snapshot(origins)
    if binary:
      # make sure we have extra origins in the snapshot as well
      for origin in snapshot.keys():
        for extra_o in self.server.get_extra_origins(origin):
          snapshot[extra_o] = snapshot[origin]
      p_str = pickle.dumps(snapshot, pickle.HIGHEST_PROTOCOL)
      self.send_msg("snapshot %i" % len(p_str))
      self.send_msg(p_str)
    else:
      for o, (dsc,array) in snapshot.iteritems():
        msg = "snapshot %s %s " % (o,
                                   dsc and repr(dsc[0]).replace(' ','') or None)
        for i, row in enumerate(array):
          msg += "%s %s\n" % (dsc and dsc[1][i] or None,
                              ' '.join(["%s "%v for v in row]))
      self.send_msg(msg)

  def cmd_get(self, argline):
    """Allows remotes to get config and variables. 100% unsecure!...
    """
    args = argline.split()
    try:
      if args[0] in ORIGINS:
        self.send_msg(repr(getattr(self.server.origins[args[0]][0], args[1])))
      elif args[0].startswith('backend'):               # origin's backend
        self.send_msg(self.server.origins[args[1]][0].name)
    except StandardError as e:
      LOG.warning("cannot get: '%s' (%s)", argline, e)
      return


class ARASServer(object):
  """Sets and regroups subservers of the lightHead system."""

  def __init__(self):
    """All subServers will receive a reference to the Feature Pool"""
    super(ARASServer,self).__init__()
    self.origins = {}           # { origin: self.server and associed handler }
    self.FP = FeaturePool()     # the feature pool for context queries

  def __getitem__(self, protocol_keyword):
    return self.origins[protocol_keyword][0]
  get_server = __getitem__

  def get_handler(self, keyword):
    return self.origins[keyword][1]

  def get_server(self, keyword):
    return self.origins[keyword][0]

  def get_extra_origins(self, origin):
    """Returns origins sharing the same (srv,req_handler_class) as given origin.
    """
    return [ o for o,v in self.origins.iteritems() if o != origin and
             v == self.origins[origin] ]

  def register(self, server, req_handler_class, origin):
    """Binds origin keyword with server and relative request handler.

    server: a server instance
    req_handler_class: request handler class
    origin: origin identifier
    """
    if origin not in ORIGINS:
      LOG.error("rejecting registration of handler for unknown origin '%s'",
                origin)
      return
    LOG.debug("registering server %s & handler class %s for origin '%s'",
              server, req_handler_class, origin)
    self.origins[origin] = server, req_handler_class

  def create_protocol_handlers(self):
    """Bind individual servers and their handler to the meta server.
    This function uses conf's module definitions: if conf has an attribute
    which name can be found in ORIGINS, then that RAS module is loaded.
    Return: None
    """
    EXTRA_ORIGINS = 'extra_origins'
    if not hasattr(conf, 'ROBOT'):
      return LOG.error("in '%s': ROBOT dictionnary not found",
                       conf.get_loaded())
    if not conf.ROBOT.has_key('modules'):
      return LOG.error("in '%s': ROBOT dictionnary has no 'modules' entry",
                       conf.get_loaded())

    # check for attributes, allowing a submodule to register more
    #  than one ORIGIN keyword with its extra_origins attribute.
    for i, info in enumerate(conf.ROBOT['modules']):
      if not info.has_key('backend'):
        return LOG.error("in '%s', ROBOT's modules #%i lacks 'backend' entry",
                         conf.get_loaded(), i)
      be_name = info['backend']
      try:
        module = __import__('RAS.backends.'+be_name, fromlist=['',])
      except ImportError as e:
        LOG.error("Error importing backend '%s': %s", be_name, e)
        sys.exit(3)
      except SyntaxError as e:
        LOG.error("Error with backend '%s': %s %s:%s", be_name, e.msg,
                  e.filename, e.lineno)
        sys.exit(3)

      try:
        subserv_cls, handler_cls = getattr(module, 'get_networking_classes')()
      except AttributeError as e:
        # Consider that a missing class just means no subserver
        LOG.error("Module '%s' lacks get_networking_classes function" % be_name)
        sys.exit(3)
      assert subserv_cls and handler_cls,("subserver and handler classes can't"
                                          "be None, use base classes if needed")
      try:
        subserver = subserv_cls(info)
      except StandardError as e:
        LOG.error("Error while initializing module '%s':", be_name)
        if LOG.getEffectiveLevel() == logging.DEBUG:
          LOG.error("StandardError: %s", e) 
          import pdb; pdb.post_mortem()
        sys.exit(4)
      if not hasattr(subserver,"name"):
        LOG.error("%s has no name", subserver)          # for cmd_backend()
        sys.exit(5)
      self.register(subserver, handler_cls, info['origins'][0])
      for origin in info['origins'][1:]:
        self.register(subserver, handler_cls, origin)
    if not self.origins:
      raise conf.LoadException("No submodule configuration.")
    missing = [ o for o in ORIGINS if o not in self.origins ]
    if missing:
      LOG.warning("Missing submodules: "+"%s, "*len(missing), *missing)
