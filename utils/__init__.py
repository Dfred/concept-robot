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


class Frame(object):
    """Object with 2D coordinates and length for each dimension.
    members: x, y, w, h
    """

    def __init__(self, values=(0,)*4):
        """
        values: 4 tuple for x,y,w,h members
        """
        for i, att in enumerate('xywh'):
            setattr(self, att, values[i])

    def __repr__(self):
        return __repr__(tuple(self.x, self.y, self.w, self.h))

    def get_inner(self, factor):
        """Returns a Frame with dimensions cropped by 'factor'.
        factor: normal value (float), e.g: 0.66 => 66% from width and height.
        """
        assert factor > 0, 'factor cannot be negative'
        w,h = factor * self.w, factor * self.h
        x,y = (self.w - w)/2, (self.h - h)/2
        return Frame((x,y,w,h))

    def is_within(self, x, y):
        """Return True if coordinates are on or within the frame boundaries.
        """
        return self.w - self.x - x >= 0 and self.h - self.y - y >= 0
        
