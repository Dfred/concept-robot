/*!
  \file
  \brief Process SKIP commands

  \author Satofumi KAMIMURA

  $Id: scip_handler.c 1846 2010-06-13 23:26:56Z satofumi $

  \todo Check the checksum of acquired line
  \todo Add an argument to distinguish the line that contain version information.
*/

#include "scip_handler.h"
#include "serial_errno.h"
#include "serial_ctrl.h"
#include "serial_utils.h"
#include "urg_errno.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#if defined(WINDOWS_OS)
#define snprintf _snprintf
#endif

// error in xcode 3.2.2
//extern int snprintf(char *, size_t, const char *, ...);


/*! \todo Standardize with urg_ctrl.c */
enum {
  ScipTimeout = 1000,           /*!< [msec] */
  EachTimeout = 100,		/*!< [msec] */
};


/* Send command */
int scip_send(serial_t *serial, const char *send_command)
{
  int n = (int)strlen(send_command);
  return serial_send(serial, send_command, n);
}


/*!
  \brief Receive the response from command

  \todo Test the checksum
*/
int scip_recv(serial_t *serial, const char *command_first,
              int* return_code, int expected_ret[], int timeout)
{
  char recv_ch = '\0';
  int ret_code = 0;
  int n;
  int i;

  /* Receive the response */
  char buffer[ScipLineWidth];

  /* Skip the first response */
  n = serial_getLine(serial, buffer, ScipLineWidth, timeout);
  if (n < 0) {
    return UrgSerialRecvFail;
  }

  /* ignore 0x00 response after connection */
  if (! ((n == 1) && (buffer[0] == 0x00))) {
    if (strncmp(buffer, command_first, 2)) {
      /* Treat as an error,if there is mismatch with sent characters */
      return UrgMismatchResponse;
    }
  }

  /* Read and pass the response characters. */
  n = serial_getLine(serial, buffer, ScipLineWidth, timeout);

  /* restore last character, and use next proccessing */
  n = serial_recv(serial, &recv_ch, 1, timeout);
  if ((n == 1) && (! serial_isLF(recv_ch))) {
    serial_ungetc(serial, recv_ch);
  }

  /* Returns 0, if received response characters are as expected */
  ret_code = strtol(buffer, NULL, 16);
  if (return_code != NULL) {
    *return_code = ret_code;
  }
  for (i = 0; expected_ret[i] != -1; ++i) {
    if (ret_code == expected_ret[i]) {
      return 0;
    }
  }
  return ret_code;
}


/* Transition to SCIP 2.0 */
int scip_scip20(serial_t *serial)
{
  int expected_ret[] = { 0x0, 0xE, -1 };
  int ret;

  ret = scip_send(serial, "SCIP2.0\n");
  if (ret != 8) {
    return ret;
  }

  return scip_recv(serial, "SC", NULL, expected_ret, ScipTimeout);
}


/* Send QT command */
int scip_qt(serial_t *serial, int *return_code, int wait_reply)
{
  int expected_ret[] = { 0x0, -1 };
  int ret;

  ret = scip_send(serial, "QT\n");
  if (ret != 3) {
    return ret;
  }

  if (wait_reply == ScipNoWaitReply) {
    return 0;
  }

  ret = scip_recv(serial, "QT", return_code, expected_ret, ScipTimeout);
  if (return_code && (*return_code == 0xE)) {
    *return_code = -(*return_code);
    return UrgScip10;
  }

  return ret;
}


/* Get PP information */
int scip_pp(serial_t *serial, urg_parameter_t *parameters)
{
  int send_n;
  int ret = 0;
  int expected_reply[] = { 0x0, -1 };
  int n;
  int i;

  char buffer[ScipLineWidth];

  send_n = scip_send(serial, "PP\n");
  if (send_n != 3) {
    return SerialSendFail;
  }

  /* Receive the response */
  ret = scip_recv(serial, "PP", NULL, expected_reply, ScipTimeout);
  if (ret < 0) {
    return ret;
  }

  /* Reception of parameter characters  */
  for (i = 0; i < UrgParameterLines; ++i) {
    n = serial_getLine(serial, buffer, ScipLineWidth, ScipTimeout);
    if (n <= 0) {
      return ret;
    }

    /* !!! It is necessary to check the character string like AMIN */

    if (i == 0) {
      strncpy(parameters->sensor_type,  &buffer[5], 8);
      parameters->sensor_type[8] = '\0';

    } else if (i == 1) {
      parameters->distance_min_ = atoi(&buffer[5]);

    } else if (i == 2) {
      parameters->distance_max_ = atoi(&buffer[5]);

    } else if (i == 3) {
      parameters->area_total_ = atoi(&buffer[5]);

    } else if (i == 4) {
      parameters->area_min_ = atoi(&buffer[5]);

    } else if (i == 5) {
      parameters->area_max_ = atoi(&buffer[5]);

    } else if (i == 6) {
      parameters->area_front_ = atoi(&buffer[5]);

    } else if (i == 7) {
      parameters->scan_rpm_ = atoi(&buffer[5]);
    }
  }

  return 0;
}


/* Reception of VV response*/
int scip_vv(serial_t *serial, char *lines[], int lines_max)
{
  int send_n;
  int ret = 0;
  int expected_reply[] = { 0x0, -1 };
  int n;
  int i;

  /* Initialize by an empty message */
  for (i = 0; i < lines_max; ++i) {
    *lines[i] = '\0';
  }

  /* Send VV command */
  send_n = scip_send(serial, "VV\n");
  if (send_n != 3) {
    return SerialSendFail;
  }

  /* Receive response */
  ret = scip_recv(serial, "VV", NULL, expected_reply, ScipTimeout);
  if (ret < 0) {
    return ret;
  }

  /* Receive version information */
  for (i = 0; i < lines_max; ++i) {
    n = serial_getLine(serial, lines[i], ScipLineWidth, ScipTimeout);
    if (n <= 0) {
      return ret;
    }
  }

  serial_skip(serial, ScipTimeout, EachTimeout);
  return ret;
}


/* Change baud rate according to SS command */
int scip_ss(serial_t *serial, long baudrate)
{
  int expected_reply[] = { 0x0, 0x3, 0x4, -1 };
  int send_n;
  int ret;

  /* !!! Should be treated as an error if baud rate is not with in range of
         defined range */

  /* Send SS command */
  char buffer[] = "SSxxxxxx\n";
  snprintf(buffer, 10, "SS%06ld\n", baudrate);
  send_n = scip_send(serial, buffer);
  if (send_n != 9) {
    return SerialSendFail;
  }

  /* Receive response */
  ret = scip_recv(serial, "SS", NULL, expected_reply, ScipTimeout);
  if (ret < 0) {
    return ret;
  }

  return 0;
}
