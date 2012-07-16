#ifndef INTERNE_H
#define INTERNE_H

typedef struct internal_s {
    urg_t urg;                    /* references the URG sensor */
    urg_parameter_t parameter;
    int remain_times;             /* remaining time */
    int scan_msec;                /* scan time (msec) */
    long* data;                   /* the array storing the distances */
    int   data_max;               /* size of the array data */
    long* data_copy;              /* the array storing former distances */
    long* diff_dist;              /* the array containing the differences of distance */
} internal_t;

#endif // INTERNE_H
