#ifndef QRK_C_SERIAL_T_WIN_H
#define QRK_C_SERIAL_T_WIN_H

/*!
  \file
  \brief �V���A������̍\���� (Windows ����)

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
  \brief �V���A������̍\����
*/
typedef struct {
  int errno_;                   /*!< �G���[�ԍ� */
  HANDLE hCom_;                 /*!< �ڑ����\�[�X */
  int current_timeout_;         /*!< �^�C���A�E�g�̐ݒ莞�� [msec] */
  ringBuffer_t ring_;           /*!< �����O�o�b�t�@ */
  char buffer_[RingBufferSize];
  char has_last_ch_;            /*!< �����߂������������邩�̃t���O */
  char last_ch_;                /*!< �����߂����P���� */

} serial_t;

#endif /* !QRK_C_SERIAL_T_LIN_H */
