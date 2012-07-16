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



#include <stdio.h>
#include <stdlib.h>
#include <urg_ctrl.h>
#include <assert.h>
#include "laser_detection.h"


int main(int argc, char *argv[])
{  
    /* array of structures */
    event_t array[5];

    /* Initialization of URG sensor
       You can choose the number of scans (here 50 scans).
       Since a scan corresponds to 100msec, you can easily choose the length of detection (here 5sec) */
    if (init(49) != OK)
        printf("init fail\n");

    /* Detection of motions */
    else if (detection(array,49) != OK)
        printf("detect fail\n");

    /* Disconnects URG sensor and frees the memory */
    else if (clean_up() != OK)
        printf("clean up fail\n");

    return 0;

}






