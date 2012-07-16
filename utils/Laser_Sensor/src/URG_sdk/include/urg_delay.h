#ifndef QRK_C_URG_DELAY_H
#define QRK_C_URG_DELAY_H

/*!
  \file
  \brief 待機関数

  \author Satofumi KAMIMURA

  $Id: urg_delay.h 1975 2012-02-17 01:44:20Z satofumi $
*/

#ifdef __cplusplus
extern "C" {
#endif


/*!
  \brief 待機

  指定された時間だけ待機する

  \param[in] msec 待機時間 [msec]
*/
void urg_delay(int msec);

#ifdef __cplusplus
}
#endif

#endif /* !QRK_C_DELAY_H */
