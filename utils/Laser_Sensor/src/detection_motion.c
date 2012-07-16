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
#include <math.h>
#include <assert.h>
#include "laser_detection.h"
#include "URG_sdk/include/urg_ctrl.h"
#include "interne.h"


internal_t *MyStruct = NULL;


/***************************** This function prints an error message and disconnects the URG sensor **********************/

void urg_exit(urg_t *urg, const char *message)
{
    printf("%s: %s\n", message, urg_error(&MyStruct->urg));
    urg_disconnect(&MyStruct->urg);
}




/****************************** This function initializes the URG sensor **********************************/

int init(int CaptureTimes)
{

#ifdef WINDOWS_OS
    const char device[] = "COM12"; /* For Windows: check COM's number when URG sensor is plugged */
#else
    const char device[] = "/dev/ttyACM0"; /* For Linux */
#endif


    if (MyStruct)
        return KO;

    MyStruct = malloc(sizeof(internal_t));

    if (!MyStruct)
        return OK;

    memset(MyStruct, 0, sizeof(internal_t));


    /* To get data continuously for more than 100 times, set capture times equal to infinity times (UrgInfinityTimes)
       urg_setCaptureTimes(&urg, UrgInfinityTimes); */
    assert(CaptureTimes < 100);


    /* We print an error message if the connection is not established */
    if ( urg_connect(&MyStruct->urg, device, 115200) < 0)
    {
        urg_exit(&MyStruct->urg, "urg_connect()");
        return(KO);
    }


    MyStruct->data_max = urg_dataMax(&MyStruct->urg); /* defines the size of the array data (726 boxes) */
    MyStruct->data = (long*) malloc(sizeof(long) * MyStruct->data_max);

    /* We print an error message if the array data has no allocated memory */
    if (MyStruct->data == NULL)
    {
        fprintf(stderr, "data_max: %d\n", MyStruct->data_max);
        perror("data buffer");
        return(KO);
    }

    urg_parameters(&MyStruct->urg, &MyStruct->parameter);

    MyStruct->scan_msec = urg_scanMsec(&MyStruct->urg);

    urg_setCaptureTimes(&MyStruct->urg, CaptureTimes);


    /* We print an error message if the request is invalid */
    if (urg_requestData(&MyStruct->urg, URG_MD, URG_FIRST, URG_LAST) < 0)
    {
        urg_exit(&MyStruct->urg, "urg_requestData()");
        return(KO);
    }

    /* The array data_copy stores the distances of the previous scan */
    MyStruct->data_copy = (long*) malloc(sizeof(long) * MyStruct->data_max);

    /* The array diff_dist stores the differences of distances between two scans */
    MyStruct->diff_dist = (long*) malloc(sizeof(long) * MyStruct->data_max);

    return OK;
}




/***************************** This function is used for disconnect the URG sensor and free the memory ******************************/

int clean_up()
{
    urg_disconnect(&MyStruct->urg);
    free(MyStruct->data);
    free(MyStruct->data_copy);
    free(MyStruct->diff_dist);
    return OK;
}




/****************************** This function makes a copy of 'array1' into an other array 'array2' ***********************************/

void save(long* array1, long* array2, int size)
{
    int i;

    for(i=0; i<size; i++)
    {
        array2[i] = array1[i];
    }
}




/***************************** Ths function allows the detection of motions ***********************************/

int detection(event_t array[5],int CaptureTimes)
{

    int i,ind,p,k;
    int nb;
    int stepMin;
    int stepMax;

    int flag = 0;


    /* medium angular position (degrees) */
    float som1;
    float medium_angular_position;

    /* medium distance (mm) */
    long som2;
    long medium_distance;

    /* medium size (mm) */
    double alpha;
    float medium_size;


    struct event ev; /* This structure is used for storage the three characteristics of the object */


    for (i = 0; i < CaptureTimes; i++)
    {
        nb = 0;
        stepMin = 0;
        stepMax = 0;
        som1 = 0;
        medium_angular_position = 0;
        som2 = 0;
        medium_distance = 0;
        alpha = 0;
        medium_size = 0;

        printf("Scan %d\n\n\n",i);

        if(i >= 1)
        {
            save(MyStruct->data,MyStruct->data_copy,MyStruct->data_max);
        }


        /* Reception */
        if (urg_receiveData(&MyStruct->urg, MyStruct->data, MyStruct->data_max) < 0)
        {
            urg_exit(&MyStruct->urg, "urg_receiveData()");
        }


        if (i >= 1)
        {
            for(ind = 44; ind < MyStruct->data_max; ind++)
            {
                // calculate the difference of distance for each point of measurement
                MyStruct->diff_dist[ind] = abs(MyStruct->data[ind] - MyStruct->data_copy[ind]);
            }


            for(p = 134; p < 635; p++)
            {
                if(MyStruct->diff_dist[p] > 20) // the noise is inferior to 20mm
                {
                    stepMin = p;
                    p++;
                    while(MyStruct->diff_dist[p] > 20 && p < 635)
                    {
                        p++;
                        nb++;
                    }
                }
            }

            stepMax = stepMin + nb;


            if(nb > 10) // when 10 points have changed, it means that there has been a real movement (not noise)
            {

                for(k = stepMin; k <= stepMax; k++)
                {
                    som1 = som1 + k*0.36;
                    som2 = som2 + MyStruct->data[k];
                }

                /* We calculate the three characteristics of the object */

                // position
                medium_angular_position = (float) (som1 / (stepMax-stepMin+1));

                // distance
                medium_distance = (long) (som2 / (stepMax-stepMin+1));

                // size
                alpha = (stepMax-stepMin+1)*0.36;
                alpha = (alpha*3.14)/180;
                medium_size = sqrt( pow(MyStruct->data[stepMin],2) + pow(MyStruct->data[stepMax],2) - 2*MyStruct->data[stepMin]*MyStruct->data[stepMax]*cos(alpha) );


                printf("position moy = %f\n",medium_angular_position);
                printf("distance moy = %f\n",medium_distance);
                printf("taille moy = %f\n",medium_size);


                ev.medium_angular_position = medium_angular_position;
                ev.medium_distance = medium_distance;
                ev.medium_size = medium_size;


                /* storage in the array of structures */
                if(flag < 5)
                {
                    array[flag] = ev;
                    flag++;
                }


            }

        }

        MyStruct->remain_times = urg_remainCaptureTimes(&MyStruct->urg);

        if(MyStruct->remain_times <= 0)
        {
            break;
        }

    }

    /*It is necessary to explicitly stop the data acquisition to get data for more than 99 times */
    if (CaptureTimes > 99)
    {
        urg_laserOff(&MyStruct->urg);
    }

    return OK;
}





























