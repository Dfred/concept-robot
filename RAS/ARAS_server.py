#!/usr/bin/python
# -*- coding: utf-8 -*-

################################################################################
# This software is provided for academic research only: it is OSS but not GPL!
# In such a case, you can redistribute this software and/or modify it,
# provided you do not modify this license. Any other use is not permitted.

# ARAS is the open source software (OSS) version of the basic component of
# LightHead's software suite. 

# ARAS stands for Abstract Robotic Animation System, and features actuator,
# sensor, animation and remote management high-level interfaces.
# In particular, ARAS helps animating a head (virtual or physical), provides
# supporting algorithms for vision and hearing, as well as contributions from
# other scholars.
# Copyright 2009 - Frédéric Delaunay: dr.frederic.delaunay@gmail.com

# This software is the low-level Human-Robot-Interaction part of the CONCEPT
# project, which took place at the University of Plymouth (UK).
# The project stemed from by Frédéric Delaunay's PhD, himself under the
# supervision of professor Tony Belpaeme. The PhD project started in late 2008
# and ended in late 2011 but this part of the software is still maintained.
# Visit http://www.tech.plym.ac.uk/SoCCE/CONCEPT/ for more information.

# This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  General Public License for more details.
################################################################################

"""
SERVER MODULE

 This module listen to control connections and dispatches module-specific
  commands to the appropriate section. Also allows retreiving a snapshot of
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
from utils import conf, EXIT_DEPEND, EXIT_UNKNOWN, EXIT_CONFIG
from RAS.au_pool import FeaturePool
from supported import SECTIONS

LOG = logging.getLogger(__package__)


class ARASHandler(MetaRequestHandler, ASCIICommandProto):
  """Handles high level protocol transactions: section and commit"""

  def __init__(self, server, sock, client_addr):
    """
    """
    super(ARASHandler,self).__init__(server, sock, client_addr)
    self.fifos = {}                                 # for cmd_AU
    self.handlers = {}                              # {section : subhandler}
    self.transacting = []                           # transacting sections
    for section, (srv,hnd_class) in self.server.sections.iteritems():
      self.handlers[section] = self.create_subhandler(srv,hnd_class)
      if not self.fifos.has_key(srv):
        self.fifos[srv] = deque()

  def cmd_section(self, argline):
    """Set or replies with current section/subhandler"""
    if argline:
      argline = argline.strip()
      try:
        self.set_current_subhandler(self.handlers[argline])
        self.transacting.append(argline)
      except KeyError:
        LOG.warning("unknown section: '%s'", argline)
    else:
      self.send_msg("%s" % self.curr_handler.__class__.__name__)

  def cmd_AU(self, argline):
    """Update an AU. Careful: section is not taken into account here!
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
    """Mark the end of a transaction"""
    for srv, fifo in self.fifos.iteritems():
      if fifo:
        srv.commit_AUs(fifo)
        fifo.clear()
    for section in self.transacting:
      if hasattr(self.handlers[section], 'cmd_commit'):
        self.handlers[section].cmd_commit(argline)
    self.transacting = []

  # TODO: implement a reload of modules ?
  def cmd_reload(self, argline):
    """Reload subserver modules"""
    self.send_msg('Not yet implemented')

  def cmd_get_snapshot(self, argline):
    """Return the current snapshot of the robot's state.
    argline: optional 'ASCII' for clear text + identifiers of arrays to be sent.
    """
    args = argline.split()
    binary = True
    if args and args[0] == 'ASCII':
      binary = False
      args.pop(0)
    sections = (args and [o.strip() for o in args if o in self.server.FP.keys()]
               ) or self.server.FP.keys()
    snapshot = self.server.FP.get_snapshot(sections)
    if binary:
      # make sure we have extra sections in the snapshot as well
      for section in snapshot.keys():
        for extra_o in self.server.get_extra_sections(section):
          snapshot[extra_o] = snapshot[section]
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
    """Allow remotes to get config and variables. 100% unsecure!...
    """
    args = argline.split()
    try:
      if args[0] in SECTIONS:
        self.send_msg(repr(getattr(self.server.sections[args[0]][0], args[1])))
      elif args[0].startswith('backend'):               # section's backend
        self.send_msg(self.server.sections[args[1]][0].name)
    except StandardError as e:
      LOG.warning("cannot get: '%s' (%s)", argline, e)
      return


class ARASServer(object):
  """Sets and regroups subservers of the lightHead system."""

  def __init__(self):
    """All subServers will receive a reference to the Feature Pool"""
    super(ARASServer,self).__init__()
    self.sections = {}          # { section: self.server and associed handler }
    self.FP = FeaturePool()     # the feature pool for context queries

  def __getitem__(self, protocol_keyword):
    return self.sections[protocol_keyword][0]
  get_server = __getitem__

  def get_handler(self, keyword):
    return self.sections[keyword][1]

  def get_server(self, keyword):
    return self.sections[keyword][0]

  def get_extra_sections(self, section):
    """Get sections sharing the same (srv,req_handler_class) as given section.
    Return: iterable
    """
    return [ o for o,v in self.sections.iteritems() if o != section and
             v == self.sections[section] ]

  def register(self, server, req_handler_class, section):
    """Bind section keyword with server and relative request handler.

    server: a server instance
    req_handler_class: request handler class
    section: section identifier
    """
    if section not in SECTIONS:
      LOG.error("rejecting registration of handler for unknown section '%s'",
                section)
      return
    LOG.debug("registering server %s & handler class %s for section '%s'",
              server, req_handler_class, section)
    self.sections[section] = server, req_handler_class

  def create_protocol_handlers(self):
    """Build and bind each server and its handler to the meta server from
    conf.CONFIG definitions.
    Return: None
    """
    try:
      backends = conf.CONFIG['backends']
    except KeyError as e:
      LOG.error("config lacks '%s' entry.", e)
      exit(EXIT_CONFIG)

    ## check for attributes, allowing a section to register more than one
    ## SECTION keyword with its extra_sections attribute.
    for i, be_name in enumerate(backends):
      try:
        module = __import__('RAS.backends.'+be_name, fromlist=['',])
      except ImportError as e:
        LOG.error("Can't import backend '%s': %s", be_name, e)
        sys.exit(EXIT_DEPEND)
      except SyntaxError as e:
        LOG.error("Can't import backend '%s': %s %s:%s", be_name, e.msg,
                  e.filename, e.lineno)
        sys.exit(EXIT_UNKNOWN)

      assert hasattr(module,'get_networking_classes'), "error with %s" % module
      try:
        subserv_cls, handler_cls = module.get_networking_classes()
      except StandardError as e:
        LOG.fatal("Can't call get_networking_classes from backend '%s': %s",
                  be_name, e)
        sys.exit(EXIT_UNKNOWN)
      assert subserv_cls and handler_cls,("subserver and handler classes can't"
                                          "be None, use base classes if needed")
      ## Everything being set up, try spawning backends expecting something to
      ## go wrong. Done here as backends might not allow use of ARAS.__init__ .
      try:
        subserver = subserv_cls()
      except conf.ConfigError as e:
        LOG.error("Reading %s: %s", conf.get_loaded(), e)
        sys.exit(EXIT_CONFIG)
      except StandardError as e:
        LOG.error("Error while initializing module '%s':", be_name)
        LOG.error("StandardError: %s", e) 
        if LOG.getEffectiveLevel() == logging.DEBUG:
          import pdb; pdb.post_mortem()
        sys.exit(EXIT_UNKNOWN)
      if not hasattr(subserver,"name"):
        LOG.error("%s has no name", subserver)          # for cmd_backend()
        sys.exit(EXIT_UNKNOWN)
      sections = conf.CONFIG[be_name+'_sections']
      self.register(subserver, handler_cls, sections[0])
      for section in sections[1:]:
        self.register(subserver, handler_cls, section)
    if not self.sections:
      raise conf.LoadingError("Server hasn't any registered section.")
#    missing = [ o for o in SECTIONS if o not in self.sections ]
#    if missing:
#      LOG.warning("Server is missing sections: "+"%s, "*len(missing), *missing)
