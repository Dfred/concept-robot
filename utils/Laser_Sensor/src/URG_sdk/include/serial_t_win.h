#ifndef QRK_C_SERIAL_T_WIN_H
#define QRK_C_SERIAL_T_WIN_H

/*!
  \file
  \brief シリアル制御の構造体 (Windows 実装)

  \author Satofumi KAMIMURA

  $Id: serial_t_win.h 1559 2009-12-01 13:13:08Z satofumi $
*/

#include "ring_buffer.h"
#include <windows.h>


enum {
  SerialErrorStringSize = 256,
  RingBufferSizeShift = 10,
  RingBufferSize = 1 << RingBufferSizeShift,
};


/*!
  \brief シリアル制御の構造体
*/
typedef struct {
  int errno_;                   /*!< エラー番号 */
  HANDLE hCom_;                 /*!< 接続リソース */
  int current_timeout_;         /*!< タイムアウトの設定時間 [msec] */
  ringBuffer_t ring_;           /*!< リングバッファ */
  char buffer_[RingBufferSize];
  char has_last_ch_;            /*!< 書き戻した文字があるかのフラグ */
  char last_ch_;                /*!< 書き戻した１文字 */

} serial_t;

#endif /* !QRK_C_SERIAL_T_LIN_H */
