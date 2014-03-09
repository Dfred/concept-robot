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
import time
import logging
import threading

from numpy import array, ndarray, apply_along_axis

_NEED_WAIT_PATCH = sys.version_info[0] == 2 and sys.version_info[1] < 7

LOG = logging.getLogger(__package__)

## column index for au pool (see set_availables)
BVAL = 0                                        ## Base Value
RDIST= 1                                        ## Relative Distance
TDUR = 2                                        ## Target Duration
DDUR = 3                                        ## Delta Duration
DVT  = 4                                        ## Derivative Value
VAL  = 5                                        ## current Value


class FeaturePool(dict):
  """This singleton class serves as an efficient working memory (numpy arrays) 
  for each feature of the system. Ideally, all system data shall be in the pool
  so generic learning algorithms could detect data relationship across features.
  Also, snapshots of the current state can be returned.
  """
  # single instance holder
  instance = None

  def __new__(cls):
    """Creates a singleton.

    Need another feature pool? Derive from that class, overriding cls.instance,
     and don't bother with the __ prefix to make it pseudo-private...
    >cls: Current type (ie: maybe a derived class type)
    Return: FeaturePool instance
    """
    if cls.instance is None:
      cls.instance = super(FeaturePool,cls).__new__(cls)
      cls.instance.__descriptors = {}                   #XXX: yes, it's bad!
    return cls.instance

  def __setitem__(self, key, value):
    """Registers a Feature into the pool.

    >key: string identifying the feature
    >value: numpy.ndarray (aka numpy array) of arbitrary size
    """
    LOG.debug("new feature (%i items) in pool from %s", len(value), key)
    assert isinstance(value, ndarray) , "Not a numpy ndarray instance"
    dict.__setitem__(self, key, value)
    self.__descriptors[key] = None

  def set_descriptor(self, key, descriptor):
    """Describes the data for a feature. This info is sent in a snapshot.

    key: string identifying the feature.
    descriptor: tuple of iterable of strings, 1st for columns 2nd for rows.
    """
    assert len(descriptor) == 2, "descriptor should have only 2 iterables"
    self.__descriptors[key] = descriptor

  def get_snapshot(self, features=None):
    """Get a snapshot, optionally selecting specific features.

    features: iterable of strings identifying features to be returned.
    Returns: { feature : (descriptor,values) }
    """
    return dict( (f,(self.__descriptors[f],self[f])) for f
                 in (features or self.iterkeys()) )


class AUPool(dict):
  """This class facilitates the use of Action Units within the Feature Pool.

  Pool values updated in this class are ideal and use motion dynamics.
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
    for au,nval_row in sorted(AP.iteritems(),key=lambda x: x[0]):
      LOG.info("%5s :"+" %.5f"*len(nval_row), au, *nval_row)

  def set_availables(self, AUs, values=None):
    """Register supported AUs, optionally setting their initial values.
    AUs: iterable of Action Unit IDs (names)
    values: iterable of floats. Needs to be the same length as AUs.
    Returns: None
    """
    if values:
      assert len(AUs) == len(values), "AUs and values have different lengths"
    else:
      values = [0] * len(AUs)
    # base value, relatv dist, target dur, remaining dur, derivt val, curr value
    # BVAL      , RDIST      , TDUR      , DDUR         , DVT       , VAL
    table = [values] + [[.0]*len(values)]*4 + [values]
    self.FP[self.origin] = array(zip(*table))           # transpose
    self.FP.set_descriptor(self.origin, 
                           (('BVAL','RDIST','TDUR','DDUR','DVT','VAL'),AUs) )
    for i,au in enumerate(AUs):
      self[au] = self.FP[self.origin][i]                # view or shallow copy
    LOG.info("Available AUs:\n")
    self.Log_AUs()

  def update_targets(self, iterable):
    """Set targets for a set of AUs. self[:][VAL] should reflect reality.

    iterable: list of (AU, normalized target value, target duration in sec).
    """
    for AU, target, attack in iterable:
      curr_val = self[AU][VAL]
      self[AU][0:DVT] = curr_val, target-curr_val, attack, attack

  #TODO: optimize returning { AU, updated value }
  def update_time(self, time_interval, with_speed=False):
    """Updates the AU pool.

    time_interval: elapsed time since last call to this function
    with_speed: update speed value as well.
    Returns: False if all AUs reached their targets (no update), True otherwise.
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
    return any(data[:,DDUR])
  
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
