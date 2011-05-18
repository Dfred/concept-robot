#! /usr/bin/python
# -*- coding: utf-8 -*-
"""Main package for Human-Robot Interaction subsystems of the lightHead Robotic
Animation System.
"""

import sys
import logging

__version__ = "0.0.1"
__date__ = ""
__author__ = "Frédéric Delaunay"
__email__ = "frederic.delaunay@plymouth.ac.uk"
__copyright__ = "Copyright 2011, University of Plymouth"
__license__ = "GPL"
__credits__ = ["Joachim De Greeff"]
__maintainer__ = "Frédéric Delaunay"
__status__ = "Prototype" # , "Development" or "Production"

LOG = logging.getLogger(__package__)

class FeaturePool(dict):
    """This class serves as a short term memory. It holds all possible features
    so other modules can query a snapshot of the current robot's state.
    Also, it's a singleton.
    """
    # single instance holder
    instance = None

    def __new__(cls):
        """Creates a singleton.
        Another feature pool? Derive from that class overriding self.instance,
         and don't bother with the __ prefix to make it pseudo-private...
        cls: don't touch (it's the current type, ie: maybe a derived class type)
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
        import numpy
        LOG.debug("new feature in the pool from %s: %s", name, np_array)
        if np_array is not None:
            assert isinstance(np_array,numpy.ndarray),\
                'Not a numpy ndarray instance'
        dict.__setitem__(self, name, np_array)

    def get_snapshot(self, features=None):
        """Get a snapshot, optionally selecting specific features.
        features: iterable of str specifying features to be returned.
        Returns: all context (default) or subset from specified features.
        """
        # load non-standard module only now
        import numpy
        features = features or features.iterkeys()
        return dict( (f, isinstance(self[f],numpy.ndarray) and self[f] or
                         self[f].get_feature() )
                     for f in features )


def initialize(thread_info):
    """Initialize the system.
    thread_info: tuple of booleans setting threaded_server and threaded_clients
    """
    print "LIGHTHEAD Animation System, python version:", sys.version_info

    # check configuration
    try:
        from utils import conf; missing = conf.load()
        if missing:
            print '\nmissing configuration entries: %s' % missing
            sys.exit(1)
        if hasattr(conf, 'DEBUG_MODE') and conf.DEBUG_MODE:
            # set system-wide logging level
            from utils import comm; comm.set_default_logging(debug=True)
    except conf.LoadException, e:
        print 'in file {0[0]}: {0[1]}'.format(e)
        sys.exit(2)

    # Initializes the system
    from utils import comm
    from lightHead_server import lightHeadServer, lightHeadHandler
    server = comm.create_server(lightHeadServer, lightHeadHandler,
                                conf.lightHead_server, thread_info)
    # Because what we have here is a *meta server*, we need to initialize it
    #  properly; face and all other subservers are initialized in that call.
    server.create_protocol_handlers()
    return server
