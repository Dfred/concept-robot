#ifndef QRK_C_SERIAL_T_LIN_H
#define QRK_C_SERIAL_T_LIN_H

/*!
  \file
  \brief シリアル制御の構造体 (Linux, Mac 実装)

  \author Satofumi KAMIMURA

  $Id: serial_t_lin.h 1557 2009-12-01 12:38:06Z satofumi $
*/

#include "ring_buffer.h"
#include <termios.h>


enum {
  SerialErrorStringSize = 256,
  RingBufferSizeShift = 10,
  RingBufferSize = 1 << RingBufferSizeShift,
};


/*!
  \brief シリアル制御の構造体
*/
typedef struct
{
  int errno_;                                /*!< エラー番号 */
  char error_string_[SerialErrorStringSize]; /*!< エラー文字列 */
  int fd_;                                   /*!< 接続リソース */
  struct termios sio_;                       /*!< ターミナル制御 */
  ringBuffer_t ring_;                        /*!< リングバッファ */
  char buffer_[RingBufferSize];
  char has_last_ch_;            /*!< 書き戻した文字があるかのフラグ */
  char last_ch_;                             /*!< 書き戻した１文字 */

} serial_t;

#endif /*! QRK_C_SERIAL_T_LIN_H */
