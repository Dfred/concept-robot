/*

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






