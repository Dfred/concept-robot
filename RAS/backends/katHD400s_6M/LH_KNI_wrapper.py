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
LightHead KNI wrapper using Python ctypes.
This file can only be used with LH_KNI_wrapper.cpp compiled to a shared library.
Refer to the README for further information.

Only basic control on the arm is needed. Avoiding swig also allows us to be
closer to low-level apis, hence reducing overhead.
"""
from os.path import dirname, sep
from platform import system
from ctypes import *

from RAS.spine import SpineError

class LHKNI_wrapper(object):
    """
    """
    @staticmethod
    def validate(API_return_value):
        if API_return_value == -1:
            raise SpineError('KNI failure')
        return API_return_value

    #XXX: Careful: it seems ctypes has issues with debug symbols!
    LIB_PATH = dirname(__file__)+sep+'libLH_KNI_wrapper'+(
        system() == 'Windows' and '.dll' or '.so')

    def __init__(self, KNI_cfg_file, address):
        try:
            self.KNI = CDLL(self.LIB_PATH)
        except OSError, e:
            raise ImportError('trying to load '+self.LIB_PATH+': '+e.args[-1])

        if self.KNI.initKatana(KNI_cfg_file, address) == -1:
            raise SpineError('KNI configuration file not found or'
                             ' failed to connect to hardware', KNI_cfg_file)
        print 'loaded config file', KNI_cfg_file, 'and now connected'

    def __getattr__(self,name):
        """
        """
        try:
          fct = self.KNI.__getattr__(name)
          fct.restype = LHKNI_wrapper.validate
          return fct
        except AttributeError:
          raise

    def getEncoder(self, axis):
        enc = c_int()
        self.KNI.getEncoder(axis, byref(enc))
        return enc

    def getEncoders(self):
        encs = (c_int * 6)()
        self.KNI.getEncoders(encs)
        return [ e for e in encs ]

    def getVelocity(self, axis):
        vel = c_short()
        self.KNI.getVelocity(axis, byref(vel))
        return int(vel.value)

    def getVelocities(self):
        vels = (c_int * 6)()
        self.KNI.getVelocities(vels)
        return [ v for v in vels ]

    def getMinMaxEPC(self):
        mins, maxs, EPCs = (c_int * 6)(),(c_int * 6)(),(c_int * 6)()    # *3
        self.KNI.getAllAxisMinMaxEPC(mins,maxs,EPCs)
        return zip([e for e in mins],[e for e in maxs]), [epc for epc in EPCs]
