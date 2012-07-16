#ifndef QRK_C_URG_TICKS_H
#define QRK_C_URG_TICKS_H

/*!
  \file
  \brief タイムスタンプ取得関数

  \author Satofumi KAMIMURA

  $Id: urg_ticks.h 1975 2012-02-17 01:44:20Z satofumi $
*/

#ifdef __cplusplus
extern "C" {
#endif


/*!
  \brief タイムスタンプの取得

  \retval タイムスタンプ [msec]
*/
extern long urg_ticks(void);

#ifdef __cplusplus
}
#endif

#endif /* !QRK_C_TICKS_H */
