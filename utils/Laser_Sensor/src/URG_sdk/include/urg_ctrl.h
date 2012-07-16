#ifndef QRK_C_URG_CTRL_H
#define QRK_C_URG_CTRL_H

/*!
  \file
  \brief URG control

  \author Satofumi KAMIMURA

  $Id: urg_ctrl.h 1975 2012-02-17 01:44:20Z satofumi $

  \todo Define examples for each functions
*/

#ifdef __cplusplus
extern "C" {
#endif

#include "urg_t.h"


/*!
  \brief Parameter for object
*/
enum {
  UrgLineWidth = 64 + 1 + 1,    /*!< Maximum length of a line */
  UrgInfinityTimes = 0,         /*!< continuous data transmission */
};


/*!
  \brief Command type of URG
*/
typedef enum {
  URG_GD,                       /*!< GD command */
  URG_GD_INTENSITY,             /*!< GD command(Inclusing intensity data) */
  URG_GS,                       /*!< GS command */
  URG_MD,                       /*!< MD command */
  URG_MD_INTENSITY,             /*!< MD command(Inclusing intensity data) */
  URG_MS,                       /*!< MS command */
} urg_request_type;


/*!
  \brief To omit URG data range specification
*/
enum {
  URG_FIRST = -1, /*!< starting position when complete data is to be acquired */
  URG_LAST = -1, /*!< end position when complete data is to be acquired */

  UrgInvalidTimestamp = -1,     /*!< Error value of timestamp */
};


extern void urg_initialize(urg_t *urg);


/*!
  \brief Connection

  \param[in,out] urg Structure of URG control
  \param[in] device Connection device
  \param[in] baudrate Baudrate

  \retval 0 Normal
  \retval <0 Error

  \see gd_scan.c, md_scan.c

  Example
  \code
urg_t urg;

// Coonnection
if (urg_connect(&urg, "COM3", 115200) < 0) {
  printf("urg_connect: %s\n", urg_error(&urg));
  return -1;
}

...

urg_disconnect(&urg); \endcode
*/
extern int urg_connect(urg_t *urg, const char *device, long baudrate);


/*!
  \brief Disconnection

  \param[in,out] urg Structure of URG control

  \see urg_connect()
  \see gd_scan.c, md_scan.c
*/
extern void urg_disconnect(urg_t *urg);


/*!
  \brief Checks whether connected or not and returns the result

  \param[in,out] urg Structure of URG control

  \retval 0 if connected
  \retval <0 if disconnected

  \see urg_connect(), urg_disconnect()

  Example
  \code
if (urg_isConnected(&urg) < 0) {
  printf("not connected.\n");
} else {
  printf("connected.\n");
} \endcode
*/
extern int urg_isConnected(const urg_t *urg);


/*!
  \brief Get error message

  \param[in,out] urg Structure of URG control

  \return Error message

  \see urg_connect()
  \see gd_scan.c, md_scan.c
*/
extern const char *urg_error(const urg_t *urg);


/*!
  \brief Get string containing version information

  \param[in,out] urg Structure of URG control
  \param[out] lines Buffer having version information
  \param[in] lines_max Maximum lines in buffer

  \retval 0 Normal
  \retval <0 Error

  \attention The length of a line in the buffer should be equal to more than # UrgLineWidth[byte].

  \see get_version_lines.c
*/
extern int urg_versionLines(urg_t *urg, char* lines[], int lines_max);


/*!
  \brief URG Returns parameter

  \param[in,out] urg Structure of URG control
  \param[out] parameters Structure of URG parameter

  \retval 0 Normal
  \retval <0 Error

  \see urg_maxDistance(), urg_minDistance(), urg_scanMsec(), urg_dataMax()

  Execution example of get_parameters.c (URG-04LX)
  \verbatim
% ./get_parameters
urg_getParameters: No Error.
distance_min: 20
distance_max: 5600
area_total: 1024
area_min: 44
area_max: 725
area_front: 384
scan_rpm: 600

urg_getDistanceMax(): 5600
urg_getDistanceMin(): 20
urg_getScanMsec(): 100
urg_getDataMax(): 726 \endverbatim
*/
extern int urg_parameters(urg_t *urg, urg_parameter_t* parameters);


/*!
  \brief URG Returns the sensor type

  \param[in,out] urg Structure of URG control

  \retval URG sensor type

  \code
printf("URG type: %s\n", urg_model(&urg)); \endcode
*/
extern const char* urg_model(const urg_t *urg);


/*!
  \brief Returns the number of maximum data obtained in one scan

  \param[in,out] urg Structure of URG control

  \retval >=0 number of maximum data obtained in one scan
  \retval <0 Error

  \see gd_scan.c

  Example
  \code
enum { BufferSize = 2048 };
long data[BufferSize];

...

// Checks whether number of maximum data obtained by URG sensor does not exceeds receive buffer
// (This is not necessary if size of buffer is dynamically allocated.)
int data_max = urg_dataMax(&urg);
ASSERT(BufferSize >= data_max);
\endcode
*/
extern int urg_dataMax(const urg_t *urg);


/*!
  \brief Returns measurement time taken for one scan

  Returns measurement time when motor speed is 100% as specified.

  \param[in,out] urg Structure of URG control

  \retval >=0 measurement time taken for one scan [msec]
  \retval <0 Error

  \see urg_setMotorSpeed()

  \see md_scan.c
*/
extern int urg_scanMsec(const urg_t *urg);


/*!
  \brief Maximum measurable distance

  \param[in,out] urg Structure of URG control

  \retval >=0 Maximum measurable distance [mm]
  \retval <0 Error

  \see expand_2d.c

  Example
  \code
...
n = urg_receiveData(&urg, data, data_max);

min_distance = urg_minDistance(&urg);
max_distance = urg_maxDistance(&urg);

// Output only valid data
for (i = 0; i < n; ++i) {
  long length = data[i];
  if ((length > min_distance) && (length < max_distance)) {
    printf("%d:%d\n", i, length);
  }
}
\endcode
*/
extern long urg_maxDistance(const urg_t *urg);


/*!
  \brief Minimum measureable distance

  \param[in,out] urg Structure of URG control

  \retval >=0 Minimum measurable distance [mm]
  \retval <0 Error

  \see expand_2d.c
*/
extern long urg_minDistance(const urg_t *urg);


/* ---------------------------------------------------------------------- */


/*!
  \brief Sets the number of lines to be skiped.

  The volume of acquire data can be reduced by skipping the lines .

  \param[in,out] urg Structure of URG control
  \param[in] lines Number of lines to be skiped.

  \retval 0 Normal
  \retval <0 Error
*/
extern int urg_setSkipLines(urg_t *urg, int lines);


/*!
  \brief Sets number of scans to be skipped.

  \param[in,out] urg Structure of URG control
  \param[in] frames Number of skipped frames.

  \retval 0 Normal
  \retval <0 Error

  \attention Valid only with MD/MS command.
*/
extern int urg_setSkipFrames(urg_t *urg, int frames);


/*!
  \brief Sets  number of times the data to be acquired .

  \param[in,out] urg Structure of URG control
  \param[in] times Number of scan data

  \retval 0 Normal
  \retval <0 Error

  \attention Valid only with MD/MS command
  \attention Specify #UrgInfinityTimes to acquire data more than 100 times

  Example
  \code
// Data is supplied indefinitely
urg_setCaptureTimes(&urg, UrgInfinityTimes);

...

// Data acquistion is stopped if laser is switched off.
urg_laserOff(&urg);
  \endcode
*/
extern int urg_setCaptureTimes(urg_t *urg, int times);


/*!
  \brief Get number of remaining times on MD/MS capture

  \param[in,out] urg Structure of URG control

  \retval remaining times. (100 means infinity times)

  \see md_scan.c
*/
extern int urg_remainCaptureTimes(const urg_t *urg);


/*!
  \brief Request for distance data

  Request for distance data of [first_index, last_index].  Return all scan data when specified URG_FIRST, URG_LAST.

  \param[in,out] urg Structure of URG control
  \param[in] request_type Received data type.
  \param[in] first_index Index of the first data stored
  \param[in] last_index Index of the last received data stored.

  \retval 0 Normal
  \retval <0 Error

  \see urg_receiveData()
  \see gd_scan.c, md_scan.c

  Example
  \code
// Get one scan data from GD command
urg_requestData(&urg, URG_GD, URG_FIRST, URG_LAST);
n = urg_receiveData(&urg, data, data_max);

// Get data continuously from MD scan
urg_requestData(&urg, URG_MD, URG_FIRST, URG_LAST);
while (1) {
  n = urg_receiveData(&urg, data, data_max);
  if (n > 0) {
    // Display data etc
    ...
  }
} \endcode
*/
extern int urg_requestData(urg_t *urg,
                           urg_request_type request_type,
                           int first_index,
                           int last_index);


/*!
  \brief Receive URG data

  \param[in,out] urg Structure of URG control
  \param[out] data Storage location of received data
  \param[in] data_max Maximum number of data that can be received

  \retval 0 > Number of data received
  \retval <0 Error

  \see urg_requestData()
*/
extern int urg_receiveData(urg_t *urg, long data[], int data_max);


/*!
  \brief Get data with intensity.

  \param[in,out] urg Structure of URG control
  \param[out] data Storage location of received data
  \param[in] data_max Maximum number of data that can be received
  \param[out] intensity Storage location of intensity of received data.

  \attention Applicable only to URG-04LX (currently 2008-12-24)
*/
extern int urg_receiveDataWithIntensity(urg_t *urg, long data[], int data_max,
                                        long intensity[]);


/*!
  \brief Get partial URG data

  \param[in,out] urg Structure of URG control
  \param[out] data Storage location of received data
  \param[in] data_max Maximum number of data that can be received
  \param[in] first_index Index of the first data stored.
  \param[in] last_index Index of the last data stored

  \retval 0> Number of data received
  \retval <0 Error

  \see gd_scan.c, md_scan.c
*/
extern int urg_receivePartialData(urg_t *urg, long data[], int data_max,
                                  int first_index, int last_index);


/*!
  \brief Receive time stamp

  \param[in,out] urg Structure of URG control

  \retval Time stamp [msec]

  \see md_scan.c

  Example
  \code
urg_requestData(&urg, URG_GD, URG_FIRST, URG_LAST);
n = urg_receiveData(&urg, data, data_max);
if (n > 0) {
  long timestamp = urg_recentTimestamp(&urg);
  printf("timestamp: %d\n", timestamp);

  // Display data etc
  // !!!
} \endcode
*/
extern long urg_recentTimestamp(const urg_t *urg);


/* ---------------------------------------------------------------------- */


/*!
  \brief  Change index value into angle (radian)

  \image html urg_sensor_radian.png Front of the sensor is a positive in X axis

  \param[in,out] urg Structure of URG control
  \param[in] index Index value

  \return angle[radian]

  Example
  \code
// To operate urg_index2rad(), data from 0 to last_index is stored.
// The data of the step not measured becomes -1.
urg_requestData(&urg, URG_GD, first_index, last_index);
n = urg_receiveData(&urg, data, data_max);
for (i = 0; i < n; ++i) {
  long l = data[i];
  if (l > min_distance) {
    double rad = urg_index2rad(&urg, i);
    double x = data[i] * cos(rad);
    double y = data[i] * sin(rad);
    printf("%f, %f\n", x, y);
  }
} \endcode

  \see index_convert.c
*/
extern double urg_index2rad(const urg_t *urg, int index);


/*!
  \brief Change index into angle(degree)

  \param[in,out] urg Structure of URG control
  \param[in] index Index value

  \return Angle [degree]

  \see index_convert.c
*/
extern int urg_index2deg(const urg_t *urg, int index);


/*!
  \brief Angle(radian) is converted to index value

  \image html urg_sensor_radian.png Front of the sensor is a positive in X axis

  \param[in,out] urg Structure of URG control
  \param[in] radian Angle(radian)

  \return Index

  \see index_convert.c
*/
extern int urg_rad2index(const urg_t *urg, double radian);


/*!
  \brief Angle(degree) is converted into index

  \param[in,out] urg Structure of URG control
  \param[in] degree Angle(degre)

  \return Index value

  \see index_convert.c
*/
extern int urg_deg2index(const urg_t *urg, int degree);


/* ---------------------------------------------------------------------- */


/*!
  \brief Directs laser to switch on

  \param[in,out] urg Structure of URG control

  \retval 0 Normal
  \retval <0 Error

  \see gd_scan.c
*/
extern int urg_laserOn(urg_t *urg);


/*!
  \brief Directs laser to switch off

  \param[in,out] urg Structure of URG control

  \retval 0 Normal
  \retval <0 Error
*/
extern int urg_laserOff(urg_t *urg);


/*!
  \brief reboot

  \retval 0 Normal
  \retval <0 Error

  \attention Only Top-URG (2010-02-04)
*/
extern int urg_reboot(urg_t *urg);


/*!
  \deprecated use reboot() function.
*/
extern int urg_reset(urg_t *urg);


/* ---------------------------------------------------------------------- */


/*!
  \brief Enters into time stamp mode

  \param[in,out] urg Structure of URG control

  \retval 0 Normal
  \retval <0 Error
*/
extern int urg_enableTimestampMode(urg_t *urg);


/*!
  \brief Comes out of time stamp mode

  \param[in,out] urg Structure of URG control

  \retval 0 Normal
  \retval <0 Error
*/
extern int urg_disableTimestampMode(urg_t *urg);


/*!
  \brief Get time stamp

  Returns TM1 response.

  \param[in,out] urg Structure of URG control

  \retval >=0 Timestamp [msec]
  \retval <0 Error

  Example
  \code
// Enters into time stamp
urg_enableTimestampMode(&urg);

// Get URG time stamp continuously.
for (i = 0; i < 5; ++i) {
  long timestamp = urg_currentTimestamp(&urg);
  printf("timestamp: %ld\n", timestamp)
}

// leave tiemstamp mode
urg_disableTimestampMode(&urg); \endcode
*/
extern long urg_currentTimestamp(urg_t *urg);

#ifdef __cplusplus
}
#endif

#endif /* !QRK_C_URG_CTRL_H */
