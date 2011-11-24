#!/usr/bin/python
# -*- coding: utf-8 -*-

# LightHead programm is a HRI PhD project at the University of Plymouth,
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

    def getVelocities(self):
        vels = (c_int * 6)()
        self.KNI.getVelocities(vels)
        return [ v for v in vels ]

    def getMinMaxEPC(self):
        mins, maxs, EPCs = (c_int * 6)(),(c_int * 6)(),(c_int * 6)()    # *3
        self.KNI.getAxisMinMaxEPC(mins,maxs,EPCs)
        return zip([e for e in mins],[e for e in maxs]), [epc for epc in EPCs]
