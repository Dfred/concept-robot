/*
   LightHead is a programm part of CONCEPT, a HRI PhD project at the University
   of Plymouth. LightHead is a Robotic Animation System including face, eyes,
   head and other supporting algorithms for vision and basic emotions.
   Copyright (C) 2010-2011 Frederic Delaunay, frederic.delaunay@plymouth.ac.uk

   This program is free software: you can redistribute it and/or
   modify it under the terms of the GNU General Public License as
   published by the Free Software Foundation, either version 3 of the
   License, or (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

  Author : Najibe BOUZIDI
  Date   : 16/07/2012
  email  : najibe.bouzidi@free.fr

*/


typedef struct
        event {float medium_angular_position;
              long  medium_distance;
              float medium_size;
             } event_t;

#define OK 1
#define KO 0

extern int detection(event_t array[5]);

extern int init(int CaptureTimes);

extern int clean_up();
