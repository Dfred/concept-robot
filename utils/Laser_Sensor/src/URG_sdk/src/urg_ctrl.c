/*!
  \file
  \brief URG control

  \author Satofumi KAMIMURA

  $Id: urg_ctrl.c 1950 2011-05-07 08:18:39Z satofumi $
*/

#include "math_utils.h"
#include "urg_ctrl.h"
#include "scip_handler.h"
#include "urg_errno.h"
#include "serial_ctrl.h"
#include "serial_utils.h"
#include "serial_errno.h"
#include "urg_ticks.h"
#include "urg_delay.h"
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

#if defined(WINDOWS_OS)
#define snprintf _snprintf
#endif


enum {
  ScipTimeout = 1000,      /*!< [msec] */
  EachTimeout = 100 * 2,   /*!< URG series timeout x 2 [msec] */

  InvalidRange = -1,
};


void urg_initialize(urg_t *urg)
{
  serial_initialize(&urg->serial_);
  urg->errno_ = UrgNoError;
  urg->last_timestamp_ = 0;
}


static int urg_firstConnection(urg_t *urg, long baudrate)
{
  long try_baudrates[] = { 115200, 19200, 38400 };
  int try_size = sizeof(try_baudrates) / sizeof(try_baudrates[0]);
  long pre_ticks;
  int reply = 0;
  int ret;
  int i;

  /* The baud rate to be connected is replaced with the first element
     of the array. */
  for (i = 1; i < try_size; ++i) {
    if (baudrate == try_baudrates[i]) {
      long swap_tmp = try_baudrates[i];
      try_baudrates[i] = try_baudrates[0];
      try_baudrates[0] = swap_tmp;
      break;
    }
  }

  /* Try to connect with the specified baudrate , and check for response */
  for (i = 0; i < try_size; ++i) {

    /* Change host side baudrate  */
    ret = serial_setBaudrate(&urg->serial_, try_baudrates[i]);
    if (ret < 0) {
      return ret;
    }

    serial_clear(&urg->serial_);

    /* Send QT command */
    ret = scip_qt(&urg->serial_, &reply, ScipWaitReply);
    if (ret == UrgSerialRecvFail) {
      /* If there is no response, consider that there is mismatch in baudrate */
      continue;
    }

    if ((ret == UrgMismatchResponse) && (reply != -0xE)) {
      /* Process when response from MD/MS command is received  */
      /* Read out all data and then proceed for the next one */
      /* (reply == -0xE) means SCIP1.1 error 'E' */
      serial_clear(&urg->serial_);
      serial_skip(&urg->serial_, ScipTimeout, EachTimeout);
      reply = 0x00;
    }

    /* If the response is returned, consider that sensor is already in SCIP2.0
       mode and no need to send SCIP2.0 */
    if (reply != 0x00) {
      if ((ret = scip_scip20(&urg->serial_)) < 0) {
        /* If there is no response , continue with other baudrate */
        continue;
      }
      if (ret == 12) {
        /* SCIP1.1 protocol */
        return UrgScip10;
      }
    }

    /* Returns if there is no need to change baudrate */
    if (baudrate == try_baudrates[i]) {
      return 0;
    }

    /* Change the baud rate as specified by URG */
    pre_ticks = urg_ticks();
    if (scip_ss(&urg->serial_, baudrate) < 0) {
      return UrgSsFail;

    } else {
      /* In case of serial communication, it is necessary to wait for
         one scan after baud rate is changed. */
      long reply_msec = urg_ticks() - pre_ticks;
      urg_delay((reply_msec * 4 / 3) + 10);

      return serial_setBaudrate(&urg->serial_, baudrate);
    }
  }

  return UrgAdjustBaudrateFail;
}


static void urg_t_initialize(urg_t *urg)
{
  urg->parameters_.area_max_ = 0;
  urg->parameters_.scan_rpm_ = 0;
  urg->parameters_.sensor_type[0] = '\0';
  urg->remain_byte_ = 0;
}


/* Open serial device and initialize URG */
int urg_connect(urg_t *urg, const char *device, long baudrate)
{
  int ret;
  urg_t_initialize(urg);

  /* Open serial communication */
  ret = serial_connect(&urg->serial_, device, baudrate);
  if (ret != 0) {
    urg->errno_ = UrgSerialConnectionFail;
    return ret;
  }
  // change timestamp resolution in Windows OS
  urg_delay(0);

  /* URG connection */
  ret = urg_firstConnection(urg, baudrate);
  if (ret < 0) {
    urg->errno_ = ret;
    serial_disconnect(&urg->serial_);
    return ret;
  }

  /* Update parameter information, nothing but an initialization */
  ret = scip_pp(&urg->serial_, &urg->parameters_);
  if (ret < 0) {
    urg->errno_ = ret;
    serial_disconnect(&urg->serial_);
    return ret;
  }
  urg->skip_lines_ = 1;
  urg->skip_frames_ = 0;
  urg->capture_times_ = 0;
  urg->is_laser_on_ = UrgLaserUnknown;
  urg->remain_times_ = 0;

  urg->errno_ = UrgNoError;
  return 0;
}


void urg_disconnect(urg_t *urg)
{
  /* To stop MD/MS command */
  urg_laserOff(urg);
  serial_skip(&urg->serial_, ScipTimeout, EachTimeout);

  /* Disconnect serial connection */
  serial_disconnect(&urg->serial_);
}


int urg_isConnected(const urg_t *urg)
{
  /* Return 0, if serial connectionis valid */
  return serial_isConnected(&urg->serial_);
}


const char *urg_error(const urg_t *urg)
{
  return urg_strerror(urg->errno_);
}


int urg_versionLines(urg_t *urg, char* lines[], int lines_max)
{
  if (! urg_isConnected(urg)) {
    return -1;
  }
  return scip_vv(&urg->serial_, lines, lines_max);
}


/* Send PP command. Analyse and store the response */
int urg_parameters(urg_t *urg, urg_parameter_t* parameters)
{
  if (urg_isConnected(urg)) {
    *parameters = urg->parameters_;
  } else {
    scip_pp(&urg->serial_, &urg->parameters_);
    if (parameters) {
      *parameters = urg->parameters_;
    }
  }

  urg->errno_ = UrgNoError;
  return 0;
}


const char* urg_model(const urg_t *urg)
{
  return urg->parameters_.sensor_type;
}


int urg_dataMax(const urg_t *urg)
{
  return urg->parameters_.area_max_ + 1;
}


int urg_scanMsec(const urg_t *urg)
{
  int scan_rpm = urg->parameters_.scan_rpm_;
  return (scan_rpm <= 0) ? 1 : (1000 * 60 / scan_rpm);
}


long urg_maxDistance(const urg_t *urg)
{
  return urg->parameters_.distance_max_;
}


long urg_minDistance(const urg_t *urg)
{
  return urg->parameters_.distance_min_;
}


int urg_setSkipLines(urg_t *urg, int lines)
{
  /* Register number of lines to be skipped */
  if (lines == 0) {
    lines = 1;
  }
  if ((lines < 0) || (lines > 99)) {
    return -1;
  }

  urg->skip_lines_ = lines;
  return 0;
}


int urg_setSkipFrames(urg_t *urg, int frames)
{
  /* Register number of frames to be skipped */
  if ((frames < 0) || (frames > 9)) {
    return -1;
  }

  urg->skip_frames_ = frames;
  return 0;
}


int urg_setCaptureTimes(urg_t *urg, int times)
{
  /* Register frequency at which MD/MS data is received */
  if ((times < 0) || (times >= 100)) {
    urg->capture_times_ = 0;
  } else {
    urg->capture_times_ = times;
  }

  return 0;
}


int urg_remainCaptureTimes(const urg_t *urg)
{
  if (urg->capture_times_ == 0) {
    /* Get data infinitely */
    return 100;

  } else {
    return urg->remain_times_;
  }
}


int urg_requestData(urg_t *urg,
                    urg_request_type request_type,
                    int first_index,
                    int last_index)
{
  char buffer[] = "MDsssseeeellstt\n";

  if (first_index == URG_FIRST) {
    first_index = urg->parameters_.area_min_;
  }
  if (last_index == URG_LAST) {
    last_index = urg->parameters_.area_max_;
  }

  if ((request_type == URG_GD) || (request_type == URG_GS) ||
      (request_type == URG_GD_INTENSITY)) {

    /* In case of GD/GS */
    snprintf(buffer, 14, "G%c%04d%04d%02d\n",
             (((request_type == URG_GD) ||
               (request_type == URG_GD_INTENSITY)) ? 'D' : 'S'),
             first_index, last_index,
             urg->skip_lines_);

    /* Switch on the laser if laser is in off state */
    if (urg->is_laser_on_ != UrgLaserOn) {
      int ret = urg_laserOn(urg);
      if (ret < 0) {
        return ret;
      }
    }

  } else if ((request_type == URG_MD) || (request_type == URG_MS) ||
             (request_type == URG_MD_INTENSITY)) {
    char type = (request_type == URG_MS) ? 'S' : 'D';

    /* In case of MD/MS */
    snprintf(buffer, 17, "M%c%04d%04d%02d%d%02d\n",
             type,
             first_index, last_index,
             urg->skip_lines_,
             urg->skip_frames_,
             urg->capture_times_);
    urg->remain_times_ = urg->capture_times_;

  } else {
    urg->errno_ = UrgInvalidArgs;;
    return urg->errno_;
  }

  if ((request_type == URG_GD_INTENSITY) ||
      (request_type == URG_MD_INTENSITY)) {
    if (! strcmp("UTM-30LX", urg->parameters_.sensor_type)) {
      if (request_type == URG_GD_INTENSITY) {
        urg->errno_ = UtmNoGDIntensity;
        return urg->errno_;
      }
      /* use ME command in TOF series */
      buffer[0] = 'M';
      buffer[1] = 'E';

      /* cluster value */
      buffer[10] = '0';
      buffer[11] = '2';

    } else {
      /* AM series */
      buffer[10] = 'F';
      buffer[11] = 'F';
    }
  }

  return scip_send(&urg->serial_, buffer);
}




/* Decode 6bit data of URG */
static long decode(const char* data, int data_byte)
{
  const char* p = data;
  const char* last_p = p + data_byte;

  int value = 0;
  while (p < last_p) {
    value <<= 6;
    value &= ~0x3f;
    value |= *p++ - 0x30;
  }
  return value;
}


static int convertRawData(long data[], int data_max,
                          const char* buffer, int buffer_size, int filled,
                          int data_bytes, int skip_lines,
                          int store_last, urg_t* urg)
{
  int n;
  int i;
  int j;
  int remain_byte = urg->remain_byte_;
  long length;
  long *data_p = data + filled;

  if (data_max > store_last) {
    data_max = store_last;
  }

  if (filled == 0) {
    /* Initialize the number of data, which are remained when the first time
       is called  */
    remain_byte = 0;
  }

  if (buffer_size <= 0) {
    return filled;
  }

  /* If there is any data left, then process that data */
  if (remain_byte > 0) {
    memcpy(&urg->remain_data_[remain_byte], buffer, data_bytes - remain_byte);
    n = skip_lines;
    if ((filled + n) > data_max) {
      n = data_max - filled;
    }
    length = decode(urg->remain_data_, data_bytes);
    for (j = 0; j < n; ++j) {
      *data_p++ = length;
    }
    filled += n;
  }

  /* Process one line of data */
  n = buffer_size - data_bytes;
  for (i = (data_bytes - remain_byte) % data_bytes; i <= n; i += data_bytes) {
    length = decode(&buffer[i], data_bytes);
    for (j = 0; j < skip_lines; ++j) {
      if (filled >= data_max) {
        return data_max;
      }
      *data_p++ = length;
      ++filled;
    }
  }

  /* Save the remaining data */
  urg->remain_byte_ = buffer_size - i;
  memcpy(urg->remain_data_, &buffer[i], urg->remain_byte_);

  return filled;
}


static int checkSum(const char buffer[], int size, char actual_sum)
{
  const char *p = buffer;
  const char *last_p = p + size;
  char expected_sum = 0x00;

  while (p < last_p) {
    expected_sum += *p++;
  }
  expected_sum = (expected_sum & 0x3f) + 0x30;

  return (expected_sum == actual_sum) ? 0 : -1;
}


static int atoi_substr(const char *str, size_t len)
{
  char buffer[13];

  strncpy(buffer, str, len);
  buffer[len] = '\0';

  return atoi(buffer);
}


static int internal_receiveData(urg_t *urg, long data[], int data_max,
                                int store_first, int store_last,
                                int skip_lines)
{
  enum {
    EchoBack = 0,
    ReplyCode,
    Timestamp,

    False = 0,
    True = 1,

    MD_MS_Length = 15,          /* Length of MD, MS */
    GD_GS_Length = 12,          /* Length of GD, GS */
  };

  int lines = 0;
  char buffer[UrgLineWidth];
  int filled = 0;
  int is_echoback = False;
  int n;

  char current_type[] = "xx";
  int current_first = -1;
  //int current_last = -1;
  //int current_skip_lines = -1;
  //int current_skip_frames = -1;
  //int current_capture_times = -1;
  int current_data_bytes = 3;
  int dummy_last;
  int timeout = ScipTimeout;

  /* Initialization of time stamp */
  urg->last_timestamp_ = UrgInvalidTimestamp;

  urg->errno_ = UrgNoResponse;

  while (1) {
    n = serial_getLine(&urg->serial_, buffer, ScipLineWidth, timeout);
    //fprintf(stderr, "%d: %s\n", urg_ticks(), buffer);
    if (n <= 0) {
      if (is_echoback) {
        is_echoback = False;
        lines = 0;
        continue;
      }
      break;
    }

    if (lines > 0) {
      /* ignore echoback */
      if (checkSum(buffer, n - 1, buffer[n - 1]) < 0) {
        urg->errno_ = UrgInvalidResponse;
        lines = 0;
        filled = 0;
        is_echoback = False;
        continue;
      }
    }

    if (lines > Timestamp) {
      /* convert data */
      filled = convertRawData(data, data_max, buffer, n - 1, filled,
                              current_data_bytes, skip_lines,
                              store_last, urg);

    } else if (lines == EchoBack) {

      if ((n != GD_GS_Length) && (n != MD_MS_Length)) {
        /* Return if response is not GD/GS, MD/MS */
        urg->errno_ = UrgInvalidResponse;
        lines = 0;
        filled = 0;
        is_echoback = False;
        continue;
      }
      /* Response command */
      current_type[0] = buffer[0];
      current_type[1] = buffer[1];

      /* Initialisation of receiving settings */
      current_first = atoi_substr(&buffer[2], 4);
      //current_last = atoi_substr(&buffer[6], 4);
      //current_skip_lines = atoi_substr(&buffer[10], 2);

      if ((current_first - store_first) >= data_max) {
        /* no data */
        return 0;
      }

      /* Arrangement of dummy data */
      dummy_last = current_first - store_first;
      for (filled = 0; filled < dummy_last; ++filled) {
        data[filled] = InvalidRange;
      }

      if (n == GD_GS_Length) {
        /* Ignore receive frame settings and number of frames settings for
           GD/GS command */
        urg->remain_times_ = 0;

      } else {
        //current_skip_frames = atoi_substr(&buffer[12], 1);
        //current_capture_times = atoi_substr(&buffer[13], 2);

        /* In case of MD/MS, store the remaining number of scans. */
        urg->remain_times_ = atoi(&buffer[13]);
      }
      current_data_bytes = (current_type[1] == 'S') ? 2 : 3;

    } else if (lines == ReplyCode) {
      if (! strncmp(buffer, "10", 2)) {
        urg->is_laser_on_ = UrgLaserOff;
      }

      /* If response is "0B", ignore all response. Because there is a
         possibility that the correspondence of the response shifts. */
      if (! strncmp(buffer, "0B", 2)) {
        serial_skip(&urg->serial_, ScipTimeout, timeout);
      }

      /* In case of MD/MS, response = "00" means transition request and hence
         readout one more line, and then reset the process */
      if (current_type[0] == 'M' && (! strncmp(buffer, "00", 2))) {
        is_echoback = True;
      }

    } else if (lines == Timestamp) {
      urg->last_timestamp_ = decode(buffer, 4);
    }

    ++lines;
    timeout = EachTimeout;
  }

  if (filled <= 0) {
    return urg->errno_;
  } else {
#if 0
    // fill to urg->parameters_.area_max_ or data_max
    int last_index = data_max;
    if (urg->parameters_.area_max_ < last_index) {
      last_index = urg->parameters_.area_max_;
    }
    for (; filled <= last_index; ++filled) {
      data[filled] = InvalidRagne;
    }
#endif

    return filled;
  }
}


int urg_receiveData(urg_t *urg, long data[], int data_max)
{
  if (! urg_isConnected(urg)) {
    return -1;
  }
  return internal_receiveData(urg, data, data_max,
                              0, data_max, urg->skip_lines_);
}


int urg_receiveDataWithIntensity(urg_t *urg, long data[], int data_max,
                                 long intensity[])
{
  int i;
  int n;

  n = internal_receiveData(urg, data, data_max,
                           0, data_max, urg->skip_lines_);

  for (i = 0; i < n; i += 2) {
    long length = data[i];

    if ((i + 1) < data_max) {
      long intensity_value = data[i + 1];
      intensity[i] = intensity_value;
      intensity[i + 1] = intensity_value;
      data[i + 1] = length;
    }
  }
  return n;
}


int urg_receivePartialData(urg_t *urg, long data[], int data_max,
                           int first_index, int last_index)
{
  return internal_receiveData(urg, data, data_max, first_index, last_index, 1);
}


long urg_recentTimestamp(const urg_t *urg)
{
  /* Return latest time stamp */
  return urg->last_timestamp_;
}


double urg_index2rad(const urg_t *urg, int index)
{
  double radian = (2.0 * M_PI) *
    (index - urg->parameters_.area_front_) / urg->parameters_.area_total_;

  return radian;
}


int urg_index2deg(const urg_t *urg, int index)
{
  int degree = (int)floor((urg_index2rad(urg, index) * 180 / M_PI) + 0.5);

  return degree;
}


int urg_rad2index(const urg_t *urg, double radian)
{
  int index =
    (int)floor((((radian * urg->parameters_.area_total_) / (2.0*M_PI))
                + urg->parameters_.area_front_) + 0.5);

  if (index < 0) {
    index = 0;
  } else if (index > urg->parameters_.area_max_) {
    index = urg->parameters_.area_max_;
  }
  return index;
}


int urg_deg2index(const urg_t *urg, int degree)
{
  return urg_rad2index(urg, M_PI * degree / 180.0);
}


int urg_laserOn(urg_t *urg)
{
  /* send BM command */
  int expected_ret[] = { 0, 2, -1 };
  int send_n = scip_send(&urg->serial_, "BM\n");
  if (send_n != 3) {
    /* !!! urg->errno = UrgSendFail; */
    return SerialSendFail;
  }
  if (scip_recv(&urg->serial_, "BM", NULL, expected_ret, ScipTimeout) == 0) {
    urg->is_laser_on_ = UrgLaserOn;
  }

  return 0;
}


int urg_laserOff(urg_t *urg)
{
  return scip_qt(&urg->serial_, NULL, ScipWaitReply);
}


int urg_reboot(urg_t *urg)
{
  int expected_ret[][2] = {
    { 1, -1 },
    { 0, -1 },
  };
  int send_n;
  int recv_n;
  int i;

  urg_laserOff(urg);

  /* send RB twice */
  for (i = 0; i < 2; ++i) {
    send_n = scip_send(&urg->serial_, "RB\n");
    if (send_n != 3) {
      return SerialSendFail;
    }

    recv_n = scip_recv(&urg->serial_, "RB", NULL,
                       expected_ret[i], ScipTimeout);
    if (recv_n < 0) {
      return recv_n;
    }
  }

  /* disconnect immediately */
  urg_disconnect(urg);

  return 0;
}


int urg_reset(urg_t *urg)
{
  return urg_reboot(urg);
}


int urg_enableTimestampMode(urg_t *urg)
{
  /* Send TM0 */
  int expected_ret[] = { 0, 2, -1 };
  int send_n = scip_send(&urg->serial_, "TM0\n");
  if (send_n != 4) {
    return SerialSendFail;
  }
  return scip_recv(&urg->serial_, "TM", NULL, expected_ret, ScipTimeout);
}


int urg_disableTimestampMode(urg_t *urg)
{
  /* Send TM2 */
  int expected_ret[] = { 0, 3, -1 };
  int send_n = scip_send(&urg->serial_, "TM2\n");
  if (send_n != 4) {
    return SerialSendFail;
  }
  return scip_recv(&urg->serial_, "TM", NULL, expected_ret, ScipTimeout);
}


long urg_currentTimestamp(urg_t *urg)
{
  char buffer[ScipLineWidth];
  long timestamp = -1;
  int ret = 0;
  int n;

  /* Send TM1 */
  int expected_ret[] = { 0, -1 };
  int send_n = scip_send(&urg->serial_, "TM1\n");
  if (send_n != 4) {
    return SerialSendFail;
  }
  ret = scip_recv(&urg->serial_, "TM", NULL, expected_ret, ScipTimeout);
  if (ret != 0) {
    return ret;
  }

  /* Decode the timestamp and return */
  n = serial_getLine(&urg->serial_, buffer, ScipLineWidth, ScipTimeout);
  if (n == 5) {
    timestamp = decode(buffer, 4);
  }

  /* Read and throw the last response */
  n = serial_recv(&urg->serial_, buffer, 1, ScipTimeout);
  if (! serial_isLF(buffer[0])) {
    serial_ungetc(&urg->serial_, buffer[0]);
  }

  return timestamp;
}
