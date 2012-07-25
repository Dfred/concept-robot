#ifndef QRK_C_SERIAL_T_LIN_H
#define QRK_C_SERIAL_T_LIN_H

/*!
  \file
  \brief �V���A������̍\���� (Linux, Mac ����)

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
  \brief �V���A������̍\����
*/
typedef struct
{
  int errno_;                                /*!< �G���[�ԍ� */
  char error_string_[SerialErrorStringSize]; /*!< �G���[������ */
  int fd_;                                   /*!< �ڑ����\�[�X */
  struct termios sio_;                       /*!< �^�[�~�i������ */
  ringBuffer_t ring_;                        /*!< �����O�o�b�t�@ */
  char buffer_[RingBufferSize];
  char has_last_ch_;            /*!< �����߂������������邩�̃t���O */
  char last_ch_;                             /*!< �����߂����P���� */

} serial_t;

#endif /*! QRK_C_SERIAL_T_LIN_H */
