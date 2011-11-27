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

"""Bijective functions only.
Currently, derivatives of functions are also required.
"""

class Profile(object):
  """Generate python lambda functions from raw expressions, keeping original
    raw expressions.

    Example using raw expressions:
    p = Profile('x**2+1','2*x')
    my_fct_callable = eval('lambda x:'+ p.fct_expr.replace('x', '(x[1]+x[2])' ))
    print p.fct_callable(2)             # prints 5.
    print my_fct_callable([1,2,3])      # prints 26. Did: (x[1]+x[2])**2+1
  """

  def __init__(self, function, derivate):
    """
    function: (string) expression of the function, x being the variable.
    derivate: (string) expression of the function's derivate, x as the variable.
    """
    self.fct_expr = function
    self.drv_expr = derivate
    self.fct_callable = eval('lambda x:'+function)
    self.drv_callable = eval('lambda x:'+derivate)      #TODO: generate?


ENTRIES = {
  'smooth_step1' : Profile('(x**2)*(-2*x+3)', '-6*x*(x-1)'),
  'cos_slow' :     Profile('x-(sin(2*PI*x)/(2*PI))', '-cosf(2*x*PI)+1'),
  'linear' :       Profile('x', '1')                    # the most boring one :)
}

