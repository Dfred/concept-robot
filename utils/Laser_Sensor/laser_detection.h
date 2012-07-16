
typedef struct
        event {float medium_angular_position;
              long  medium_distance;
              float medium_size;
             } event_t;

#define OK 1
#define KO 0

extern int detection(event_t array[5],int CaptureTimes);

extern int init(int CaptureTimes);

extern int clean_up();
