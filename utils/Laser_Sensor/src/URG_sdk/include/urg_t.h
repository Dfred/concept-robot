#ifndef QRK_C_URG_T_H
#define QRK_C_URG_T_H

/*!
  \file
  \brief Structure for URG control

  \author Satofumi KAMIMURA

  $Id: urg_t.h 1714 2010-02-21 20:53:28Z satofumi $
*/

#include "urg_parameter_t.h"
#include "serial_t.h"


/*!
  \brief Constant for URG control
*/
typedef enum {
  UrgLaserOff = 0,
  UrgLaserOn,
  UrgLaserUnknown,
} urg_laser_state_t;


/*!
  \brief Structure for URG control
*/
typedef struct {

  serial_t serial_;              /*!< Structure of serial control */
  int errno_;                    /*!< Store error number */
  urg_parameter_t parameters_;   /*!< Sensor parameter */

  int skip_lines_;   /*!< Number of lines to be skipped in one scan */
  int skip_frames_; /*!< Number of scans to be skipped(Apply only to MD/MS) */
  int capture_times_; /*!< Frequency of data acquisition(Apply only to MD/MS) */

  urg_laser_state_t is_laser_on_; /*!< 0 when laser is turned off */

  long last_timestamp_;         /*!< Final time stamp */
  int remain_times_;            /*!< remain times of capture */

  char remain_data_[3];
  int remain_byte_;

} urg_t;

#endif /* !QRK_C_URG_T_H */
