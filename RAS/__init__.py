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

"""Main package for Human-Robot Interaction subsystems of the lightHead Robotic
Animation System.
"""

__version__ = "0.0.2"
__date__ = ""
__author__ = "Frédéric Delaunay"
__email__ = "frederic.delaunay@plymouth.ac.uk"
__copyright__ = "Copyright 2011, University of Plymouth"
__license__ = "GPL"
__credits__ = ["Joachim De Greeff"]
__maintainer__ = "Frédéric Delaunay"
__status__ = "Prototype" # , "Development" or "Production"

import sys
import site
import time
import logging
import threading

import numpy

LOG = logging.getLogger(__package__)                  # updated in initialize()
REQUIRED_CONF_ENTRIES = ('lightHead_server','expression_server',
                         'ROBOT', 'lib_vision', 'lib_spine')
NEED_WAIT_PATCH = sys.version_info[0] == 2 and sys.version_info[1] < 7

class FeaturePool(dict):
  """This singleton class serves as an efficient working memory (numpy arrays) 
  for each part of the system (aka origin).
  Snapshots of the current robot's state can be returned.
  """
  # single instance holder
  instance = None

  def __new__(cls):
    """Creates a singleton.
    Need another feature pool? Derive from that class, overriding self.instance,
     and don't bother with the __ prefix to make it pseudo-private...
    cls: Current type (ie: maybe a derived class type)
    """
    if cls.instance is None:
      cls.instance = super(FeaturePool,cls).__new__(cls)
    return cls.instance

  def __setitem__(self, name, np_array):
    """Registers a new Feature into the pool.
    name: string identifying the feature
    np_array: numpy.ndarray (aka numpy array) of arbitrary size
    """
    # load non-standard module only now
    LOG.debug("new feature (%i items) in pool from %s", len(np_array), name)
    assert np_array is not None and isinstance(np_array, numpy.ndarray) , \
           'Not a numpy ndarray instance'
    dict.__setitem__(self, name, np_array)

  def get_snapshot(self, features=None):
    """Get a snapshot, optionally selecting specific features.
    features: iterable of strings identifying features to be returned.
    Returns: all context (default) or subset from specified features.
    """
    # load non-standard module only now
    import numpy
    features = features or features.iterkeys()
    return dict( (f, isinstance(self[f],numpy.ndarray) and self[f] or
                  self[f].get_feature()) for f in features )


class AUPool(dict):
  """This class facilitates the use of Action Units within the Feature Pool.
  Threads can call wait() to avoid polling all the time.
  Also, it uses motion dynamics.
  """
  def __init__(self, origin, dynamics, threaded=False):
    """Initialize an AU pool for a specific origin, using a Dynamics instance.
    origin: ID (name) of the origin using this AU pool
    dynamics: a Dynamics instance defining motion/speed control.
    threaded: if evaluates to True, enables thread synchronization via wait().
    """
    super(AUPool, self).__init__(self)
    self.origin = origin
    self.FP = FeaturePool()
    self.dynamics = dynamics
    self.fct_mov, self.fct_spd = None, None             # movement and speed
    self._dynamics_changed()
    self.dynamics.register(self._dynamics_changed)
    self.event = threaded and threading.Event()

  def _dynamics_changed(self):
    # reset our update functions with the new profile dynamics:
    # x: normalized remaining time, factorise by diff value, add current value
    normalized_duration, adjust_value = '(1-x[3]/x[2])', '* x[1]+x[0]'
    fct_expr, drv_expr = self.dynamics.get_profiles_expression()
    mov_expr = '('+fct_expr.replace('x',normalized_duration)+')' + adjust_value
    spd_expr = '('+drv_expr.replace('x',normalized_duration)+')' + adjust_value
    LOG.debug("new lambdas:\n\tmovement x:%s\n\tspeed x:%s", mov_expr, spd_expr)
    self.fct_mov = eval('lambda x:'+mov_expr)
    self.fct_spd = eval('lambda x:'+spd_expr)

  def set_availables(self, AUs, values=None):
    """Register supported AUs, optionally setting their initial values.
    AUs: iterable of Action Unit IDs (names)
    values: iterable of floats. Needs to be the same length as AUs.
    """
    if values:
      assert len(AUs) == len(values), "AUs and values have different lengths"
    else:
      values = [0] * len(AUs)
    #base value, value difference, target duration, duration left, current value
    table = [values, [.0]*len(values),[.0]*len(values),[.0]*len(values), values]
    self.FP[self.origin] = numpy.array(zip(*table))     # transpose
    LOG.info("Available AUs:\n")
    for i,au in enumerate(AUs):
      self[au] = self.FP[self.origin][i]
      LOG.info("%5s : %s", au, self[au])
    return True

  def update_targets(self, iterable):
    """Set targets for a set of AUs.
    iterable: list of (AU, normalized target value, target duration in sec).
    """
    for AU, target, attack in iterable:
      try:
        self[AU][0:4] = self[AU][4], target - self[AU][4], attack, attack, 
      except StandardError:
        LOG.warning("AU '%s' not found", AU)
    if self.event:
      self.event.set()                                  # unlock waiting thread

  # TODO: check algo
  def update_time(self, time_interval, speed_instead=False):
    """
    """
    data = self.FP[self.origin]                         # numpy array
    actives_idx = data[:,3] > 0                         # filter on time left
    if not any(actives_idx):
      return
    data[actives_idx,3] -= time_interval
    # finish off shortest activations
    overdue_idx = data[:,3] < 0
    data[overdue_idx,-1] = data[overdue_idx, 0] + data[overdue_idx, 1]
    data[overdue_idx, 3] = 0
    # update values
    fct = speed_instead and self.fct_spd or self.fct_mov
    data[actives_idx,-1] = numpy.apply_along_axis(fct, 1, data[actives_idx,:])

  def wait(self, timeout=None):
    """Wait for an update of any AU in this pool.
    Return: False if timeout elapsed, True otherwise
    """
    outtimed = True
    if NEED_WAIT_PATCH:
      t = time.time()                                   # for python < 2.7
    if self.event:
      outtimed = self.event.wait(timeout)
      self.event.clear()
      if NEED_WAIT_PATCH:
        outtimed = (time.time() - t) < timeout          # for python < 2.7
    return outtimed


def initialize(thread_info):
  """Initialize the system.
  thread_info: tuple of booleans setting threaded_server and threaded_clients
  """
  print "LIGHTHEAD Animation System, python version:", sys.version_info
  # check configuration
  try:
    from utils import conf, LOGFORMATINFO, VFLAGS2LOGLVL
    conf.set_name('lightHead')
    missing = conf.load(required_entries=REQUIRED_CONF_ENTRIES)
    if missing:
      print '\nmissing configuration entries: %s' % missing
      sys.exit(1)
  except conf.LoadException, e:
    print 'in file {0[0]}: {0[1]}'.format(e)
    sys.exit(2)
  if not hasattr(conf, 'VERBOSITY'):
    conf.VERBOSITY = 0
  print 'verbosity level is', conf.VERBOSITY
  LOG.setLevel(VFLAGS2LOGLVL[conf.VERBOSITY])
  logging.basicConfig(level=VFLAGS2LOGLVL[conf.VERBOSITY], **LOGFORMATINFO)

  # Initializes the system and do all critical imports now that conf is ok.
  from utils.comm import session
  from lightHead_server import LightHeadServer, LightHeadHandler
  server = session.create_server(LightHeadHandler, conf.lightHead_server,
                                 threading_info=thread_info,
                                 server_mixin=LightHeadServer)
  server.create_protocol_handlers()       # inits face and all other subservers.
  return server

def cleanUp(server):
  """Cleans up and shuts down the system.
  thread_info: tuple of booleans setting threaded_server and threaded_clients
  """
  server.cleanUp()
  server.shutdown()
  print "LIGHTHEAD terminated"

