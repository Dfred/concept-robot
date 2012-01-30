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
import math
import logging
import threading

from numpy import array, ndarray, apply_along_axis

LOG = logging.getLogger(__package__)                  # updated in initialize()

_NEED_WAIT_PATCH = sys.version_info[0] == 2 and sys.version_info[1] < 7
_REQUIRED_CONF_ENTRIES = ('lightHead_server','expression_server',
                          'ROBOT', 'lib_vision', 'lib_spine')
BVAL = 0
RDIST = 1
TDUR = 2
DDUR = 3
DVT  = 4
VAL  = 5


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
    assert np_array is not None and isinstance(np_array, ndarray) , \
           'Not a numpy ndarray instance'
    dict.__setitem__(self, name, np_array)

  def get_snapshot(self, features=None):
    """Get a snapshot, optionally selecting specific features.
    features: iterable of strings identifying features to be returned.
    Returns: all context (default) or subset from specified features.
    """
    features = features or features.iterkeys()
    return dict( (f, isinstance(self[f],ndarray) and self[f] or
                  self[f].get_feature()) for f in features )


class AUPool(dict):
  """This class facilitates the use of Action Units within the Feature Pool.

  All values in this Pool are ideal using Motion dynamics, but predict_dist()
  allows to take error into account. 
  Threads can call wait() to avoid polling all the time.
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
    normalized_duration = '(1-x[DDUR]/x[TDUR])'
    adjust_mov = 'x[RDIST] + x[BVAL]'
    adjust_spd = 'x[RDIST]/x[TDUR]'
    fct_expr, drv_expr = self.dynamics.get_profiles_expression()
    mov_expr = '('+fct_expr.replace('x',normalized_duration)+') * ' + adjust_mov
    spd_expr = '('+drv_expr.replace('x',normalized_duration)+') * ' + adjust_spd
    LOG.debug("new lambdas:\n\tmovement x:%s\n\tspeed x:%s", mov_expr, spd_expr)
    self.fct_mov = eval('lambda x:'+mov_expr)
    self.fct_spd = eval('lambda x:'+spd_expr)

  def Log_AUs(self, AUpool=None):
    AP = AUpool or self
    for au,nval_row in AP.iteritems():
      LOG.info("%5s :"+" %.5f"*len(nval_row), au, *nval_row)

  def set_availables(self, AUs, values=None):
    """Register supported AUs, optionally setting their initial values.
    AUs: iterable of Action Unit IDs (names)
    values: iterable of floats. Needs to be the same length as AUs.
    """
    if values:
      assert len(AUs) == len(values), "AUs and values have different lengths"
    else:
      values = [0] * len(AUs)
    # base value, value diff, target dur, dur left, curr speed, curr value
    # BVAL      , RDIST     , TDUR      , DDUR    , DVT       , VAL
    table = [values] + [[.0]*len(values)]*4 + [values]
    self.FP[self.origin] = array(zip(*table))           # transpose
    LOG.info("Available AUs:\n")
    for i,au in enumerate(AUs):
      self[au] = self.FP[self.origin][i]                # view or shallow copy
    self.Log_AUs()
    return True

  def update_targets(self, iterable):
    """Set targets for a set of AUs. self[:][VAL] should reflect reality.

    iterable: list of (AU, normalized target value, target duration in sec).
    """
    for AU, target, attack in iterable:
      curr_val = self[AU][VAL]
      try:
        self[AU][0:DVT] = curr_val, target-curr_val, attack, attack
      except IndexError:
        LOG.warning("AU '%s' not found", AU)

  #TODO: optimize returning { AU, updated value }
  def update_time(self, time_interval, with_speed=False):
    """Updates the AU pool. Returns False if nothing to update, None otherwise.

    time_interval: elapsed time since last call to this function
    with_speed: update speed value as well.
    """
    data = self.FP[self.origin]
    actives_flagList = data[:,DDUR] > 0                 # filter on time left
    if not any(actives_flagList):
      return False
    data[actives_flagList,DDUR] -= time_interval
    # update values
    data[actives_flagList,VAL] = apply_along_axis(self.fct_mov, RDIST,
                                                   data[actives_flagList,:])
    if with_speed:
      data[actives_flagList,DVT] = apply_along_axis(self.fct_spd, RDIST,
                                                     data[actives_flagList,:])
    # finish off shortest activations
    overdue_idx = data[:,DDUR] < 0
    data[overdue_idx,VAL] = data[overdue_idx, BVAL] + data[overdue_idx, RDIST]
    if with_speed:
      data[overdue_idx,DVT] = 0
    data[overdue_idx,DDUR] = 0
    if not any(data[:,DDUR]):
      return False
  
  def predict_dist(self, time_interval, curr_Hpose,
                   coeff, offset):
    """Returns the distance covered in time_interval seconds (normalized value).

     This uses the dynamics profile and uses curr_Hpose to compensate for error.
    time_interval: estimated next call time to update_time.
    curr_Hpose: current hardware pose
    """
    ret = {}
    for AU,nHval in curr_Hpose.iteritems():
      if self[AU][DDUR] <= 0:
        continue
      curr_dist = abs(nHval - self[AU][BVAL])
      curr_err = abs(self[AU][VAL] - nHval)
      info_row = self[AU].copy()
      info_row[DDUR] -= time_interval
      ret[AU] = self.fct_mov(info_row) - curr_dist + curr_err
      if math.isnan(ret[AU]):
        ret[AU] = 0
      print '%.2f%%e (%.3fs +%.3fs %.2f%%) : dist_next %.6s - dist_curr %.6s + err %.6s (%s - %s)/ %.2fs => %.5s' % (
        nHval/self[AU][RDIST]*100,
        self[AU][TDUR]-self[AU][DDUR],  time_interval,
        (1-self[AU][DDUR]/self[AU][TDUR]) *100,
        coeff*self.fct_mov(info_row), coeff*curr_dist, coeff*curr_err,
        coeff*self[AU][VAL]+offset, coeff*nHval+offset,
        time_interval,
        ret[AU]/time_interval * .01)
#      print ('predict in +%.3fs' % (self[AU][DDUR] - info_row[DDUR]),
#             'ideal next:', self.fct_mov(info_row),
#             'curr_dist:', curr_dist,
#             'curr_err:', curr_err,
#             'pred_dist:', ret[AU])
    return ret

  def unblock_wait(self):
    """Unblock threads blocked in self.wait().
    """
    if self.event:
      self.event.set()                                  # unlock waiting thread

  def wait(self, timeout=None):
    """Wait for an update of any AU in this pool.
    Return: False if timeout elapsed, True otherwise
    """
    outtimed = True
    if timeout and _NEED_WAIT_PATCH:
      t = time.time()                                   # for python < 2.7
    if self.event:
      outtimed = self.event.wait(timeout)
      self.event.clear()
      if _NEED_WAIT_PATCH:
        outtimed = timeout and (time.time()-t) < timeout or True
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
    missing = conf.load(required_entries=_REQUIRED_CONF_ENTRIES)
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


if __name__ == "__main__":
  """performs AUPool tests.
  """
  import logging
  from utils import comm, conf, LOGFORMATINFO
  logging.basicConfig(level=logging.DEBUG, **LOGFORMATINFO)

  AUS = ('t1','t2')
  from RAS.dynamics import INSTANCE as DYNAMICS
  pool = AUPool('test', DYNAMICS, threaded=False)
  pool.set_availables(AUS)

  def test(triplets, t_diff):
    pool.update_targets(triplets)
    print '<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< updated targets:' ; pool.Log_AUs()
    integral_t1 = 0
    while pool.update_time(t_diff, with_speed=True) != False:
      print '--- update time (+%ss) ---'%t_diff
      integral_t1 += pool['t1'][DVT] * t_diff
      pool.Log_AUs()
    print '>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> final state:' ; pool.Log_AUs()
    print 'speed error: ', pool['t1'][RDIST] - integral_t1

  # various targets in 2s
  test( (('t1',1,2), ('t2',.5,2)), .3)
  test( (('t1',0,1), ('t2',.5,1)), .1)
