#include <stdbool.h>
#include <stdlib.h>	// exit, abs
#include <stdio.h>	// printf, fflush
#include <unistd.h>	// scanf
#include <math.h>	// cos,..
#include <string.h>	// memcpy
#define __USE_BSD
#include <sys/time.h>	// gettimeofday, timeradd..

#include "LH_KNI_wrapper.h"

#define ERR_FAILED -1
#define MAX_SPEED 180	// in encoders per 10 ms => 18 000 encoders/s.
#define ACCEL	2	// 1: long accel (~sqrt) / 2: short accel (~linear)

#define NBR_AXIS 6

#define ERROR_FAC 1	// constant factor coming from the blue
#define GET_TIME(st) if (gettimeofday(&st, NULL) == -1) {printf("error gettimeofday\n");}

void print_status(int encoders[NBR_AXIS],
		  int velocities[NBR_AXIS],
		  char self_overwrite)
{
  printf("%cMotors: ", self_overwrite ? '\r':' ');
  for (int i=0; i<NBR_AXIS; i++)
    printf("(#%i : %ie %iv) ", i+1, encoders[i], velocities[i]);
  if (! self_overwrite)
    printf("\n");
}

typedef float (*p_fct)(float);

float movmt_prof1(float x)
{ return x*x*(-2*x+3); }

float movmt_prof2(float x)
{ return x-(sin(2*PI*x)/(2*PI)); }

float speed_prof1(float x)
{ return (-cosf(2*x*PI)+1); }

float speed_prof2(float x)
{ return -6*x*(x-1); }

float speed_prof3(float x)
{ return sqrt(x); }

float get_time_ratio(struct timeval begin,
		     struct timeval target,
		     struct timeval now)
{
  struct timeval elapsed, total;
  timersub(&now, &begin, &elapsed);
  timersub(&target, &begin, &total);
  /* printf("(%li+%f) / (%li+%f) = %f\n", */
  /* 	 elapsed.tv_sec, elapsed.tv_usec / 1000000.0, */
  /* 	 total.tv_sec,     total.tv_usec / 1000000.0,	  */
  /* 	 (elapsed.tv_sec + ((float)elapsed.tv_usec/1000000)) / */
  /* 	 (  total.tv_sec + ((float)  total.tv_usec/1000000))); */
  return
    (elapsed.tv_sec + ((float)elapsed.tv_usec/1000000)) /
    (  total.tv_sec + ((float)  total.tv_usec/1000000));
}

float get_time_rel(struct timeval begin, struct timeval now)
{
  struct timeval elapsed;
  timersub(&now,&begin,&elapsed);
  return elapsed.tv_sec + elapsed.tv_usec/1000000.0;
}

int get_speed(float total_dist, float total_dur,
	      float curr_dist, float curr_dur, float step_dur)
{
  p_fct M = movmt_prof2;
  float tr = curr_dur/total_dur;
  float tr_next = (curr_dur+step_dur)/total_dur;
  int dist_curr_err = M(tr)*total_dist - curr_dist;
  float dist_next_ideal = M(tr_next)*total_dist;
  // KNI defines speed in enc/10ms, so we need to convert time
  float speed = tr < 1 ? (dist_next_ideal-curr_dist+dist_curr_err)/step_dur*.01\
    : MAX_SPEED;
  if (speed > MAX_SPEED)
    {
      printf("SPEED TICKET! %.2f > %i\n", speed, MAX_SPEED);
      speed = MAX_SPEED;
    }
  return speed > 0 ? speed : 0;
}

int
calibrate_if_needed()
{
  int encoders[NBR_AXIS];
  printf("-- checking if blocked.\n");
  switch (is_blocked())
    {
    case ERR_FAILED: exit(2);
    case 1 : unblock();
    }
  getEncoders(encoders);
  printf("-- checking if calibration is needed.\n");
  for (int axis = 1; axis <= NBR_AXIS; axis++)
    if (moveMot(axis, encoders[axis-1], 10, ACCEL) == ERR_FAILED)
      {
	calibrate();
  	break;
      }
  printf("DONE testing blocked & calibration\n");
  return 0;
}

int main(int ac, char *argv[])
{
  int encoders[NBR_AXIS], velocities[NBR_AXIS];
  if (ac < 2)
    { printf("config file argument required.\n"); exit(1); }

  printf("Initializing Katana..."); fflush(stdin);
  if (initKatana(argv[1], "192.168.168.232") == -1)
    { printf("initKatana failed\n"); exit(1); }
  printf("done.\n");
  if (calibrate_if_needed() == -1)
      exit(1);

  int axis_min[NBR_AXIS], axis_max[NBR_AXIS], axis_EPC[NBR_AXIS];
  if (getAllAxisMinMaxEPC(axis_min, axis_max, axis_EPC) == -1)
    { printf("getAxisMinMaxEPC failed\n"); exit(1); }
  for (int i = 0; i < NBR_AXIS; i++)
    printf("Axis #%i encoders [%i,%i] , %i encoders per cycle\n", i+1,
	   axis_min[i], axis_max[i], axis_EPC[i]);

  int enc_base = 0, enc_diff = 0, axis = 0, secs = 0, speed = 0, updates = 0;
  struct timeval t, t_last, t_res, t_base, t_target, t_end;

  setMaxAccel(0, ACCEL);
  setMaxVelocity(0, MAX_SPEED);

  while (1)
    {
      int moving = 1;
      float r_dist, r_time;
      
      while (moving && axis > 0)	 // all axis
      	{
      	  getEncoders(encoders);
      	  //getVelocities(velocities);			// call is way too slow
      	  r_dist = (encoders[axis-1]-enc_base)/(float)(enc_diff);
      	  GET_TIME(t);
	  r_time = get_time_ratio(t_base, t_target, t);
      	  if (axis)
	    {
	      timersub(&t, &t_base, &t_res);
	      printf("%3.2f%%e (%.3fs) %.2f%%:", r_dist*100,
	  	     t_res.tv_sec+(float)t_res.tv_usec/1000000, r_time*100);
	    }
      	  if (r_time > 0.001)
      	    {
	      speed = get_speed(abs(enc_diff), secs,
				abs(enc_base - encoders[axis-1]),
				get_time_rel(t_base,t), 0.16);
	      //get_time_rel(t_last,t)
      	      setMaxVelocity(0, speed);
      	      printf("[speed:%i] ", speed);
      	    }
      	  print_status(encoders, velocities, 0);
      	  moving = is_moving(0);
      	  updates++;
	  memcpy(&t_last, &t, sizeof(t));
      	}
      
      GET_TIME(t_end)
      float diff = get_time_rel(t_base, t_end);
      if (axis > 0) printf("Done in %fs. (%f updates/s)\n", diff, updates/diff);

      getEncoders(encoders), getVelocities(velocities);
      print_status(encoders, velocities, 0);
      printf("\naxis, target, seconds > ");
      if (scanf("%i %i %i", &axis, &enc_diff, &secs) == EOF) break;
      if (axis < 1 || axis > NBR_AXIS) continue;

      enc_base = encoders[axis-1];
      enc_diff -= enc_base;				// now a relative value

      GET_TIME(t_base)
      memcpy(&t_last, &t_base, sizeof(t));
      memcpy(&t_target, &t_base, sizeof(t));
      t_target.tv_sec = t_base.tv_sec + secs;
      speed = get_speed(abs(enc_diff), secs,
			0, 0, 0.09);			// without setMaxVel..
      printf("\nmoving axis %i from %i to %i (%+i) in %is [start speed: %i]\n", 
	     axis, enc_base, enc_base+enc_diff, enc_diff, secs, speed);
      //if (setMaxVelocity(0, speed) == -1 || moveMotAndWait(axis, enc_base+enc_diff, 10) == -1)
      if (moveMot(axis, enc_base+enc_diff, speed, ACCEL) == ERR_FAILED)
	{ printf("huh?\n"); return 1; }
      updates = 1;
    }
  printf("done\n");
  return 0;
}
