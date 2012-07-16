#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

#include "URG_sdk/include/urg_ctrl.h"

#include "interne.h"

internal_t *Najibe = NULL;


int init()
{

    Najibe->CaptureTimes = 99;

    /* To get data continuously for more than 100 times, set capture times equal to infinity times (UrgInfinityTimes)
       urg_setCaptureTimes(&urg, UrgInfinityTimes); */
    assert(Najibe->CaptureTimes < 100);


#ifdef WINDOWS_OS
  const char device[] = "COM12"; /* For Windows: check COM's number when Urg is plugged */
#else
  const char device[] = "/dev/ttyACM0"; /* For Linux */
#endif


    if (Najibe)
      return KO;

    Najibe = malloc(sizeof(internal_t));

    if (!Najibe)
      return OK;

    memset(Najibe, 0, sizeof(internal_t)); // on l'initialise à zéro


    /**************************** Connection PC - URG sensor **********************************/

    if ( urg_connect(&Najibe->urg, device, 115200) < 0)
    {
        urg_exit(&Najibe->urg, "urg_connect()");
        return(KO);
    }


    /**************************** Storage of distances *********************************/

    Najibe->data_max = urg_dataMax(&Najibe->urg); /* size of the array data : 726 boxes */
    Najibe->data = (long*) malloc(sizeof(long) * Najibe->data_max);

    if (Najibe->data == NULL)
    {
        fprintf(stderr, "data_max: %d\n", Najibe->data_max);
        perror("data buffer");
        return(KO);
    }

    urg_parameters(&Najibe->urg, &Najibe->parameter);

    Najibe->scan_msec = urg_scanMsec(&Najibe->urg);

    urg_setCaptureTimes(&Najibe->urg, Najibe->CaptureTimes);

    if (urg_requestData(&Najibe->urg, URG_MD, URG_FIRST, URG_LAST) < 0)
    {
        urg_exit(&Najibe->urg, "urg_requestData()");
        return(KO);
    }

    Najibe->data_copy = (long*) malloc(sizeof(long) * Najibe->data_max);
    Najibe->diff_dist = (long*) malloc(sizeof(long) * Najibe->data_max);


}








