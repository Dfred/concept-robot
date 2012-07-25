#ifndef QRK_URG_PARAMETER_T_H
#define QRK_URG_PARAMETER_T_H

/*!
  \file
  \brief Parameter information of URG

  \author Satofumi KAMIMURA

  $Id: urg_parameter_t.h 1684 2010-02-10 23:56:38Z satofumi $
*/


enum {
  UrgParameterLines = 8 + 1 + 1,
  SensorTypeLineMax = 80,
};


/*!
  \brief URG parameters
*/
typedef struct {
  char sensor_type[SensorTypeLineMax]; /*!< Sensor type */
  long distance_min_;                  /*!< DMIN Information */
  long distance_max_;                  /*!< DMAX Information */
  int area_total_;                     /*!< ARES Information */
  int area_min_;                       /*!< AMIN Information */
  int area_max_;                       /*!< AMAX Information */
  int area_front_;                     /*!< AFRT Information */
  int scan_rpm_;                       /*!< SCAN Information */
} urg_parameter_t;

#endif /* !QRK_URG_PARAMETER_T_H */
