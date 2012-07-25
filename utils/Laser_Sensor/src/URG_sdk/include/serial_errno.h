#ifndef QRK_C_SERIAL_ERRNO_H
#define QRK_C_SERIAL_ERRNO_H

/*!
  \file
  \brief シリアル送受信のエラー定義

  \author Satofumi KAMIMURA

  $Id: serial_errno.h 1300 2009-09-15 06:36:54Z satofumi $
*/

enum {
  SerialNoError = 0,            /*!< 正常 */
  SerialNotImplemented = -1,    /*!< 未実装 */
  SerialConnectionFail = -2,    /*!< 接続エラー */
  SerialSendFail = -3,          /*!< 送信エラー */
  SerialRecvFail = -4,          /*!< 受信エラー */
  SerialSetBaudrateFail = -5,   /*!< ボーレート設定エラー */

  /* !!! */
};

#endif /* !QRK_C_SERIAL_ERRNO_H */
