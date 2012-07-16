#include <stdio.h>
#include <stdlib.h>

#include "URG_sdk/include/urg_ctrl.h"

#include "interne.h"

extern internal_t *Najibe;


/* Prints an error message and disconnects the URG sensor */

void urg_exit(urg_t *urg, const char *message)
{
    printf("%s: %s\n", message, urg_error(&Najibe->urg));
    urg_disconnect(&Najibe->urg);
    return KO;
}

int clean_up()
{
    urg_disconnect(&Najibe->urg);
    free(Najibe->data);
    free(Najibe->data_copy);
    free(Najibe->diff_dist);
    return OK;
}
