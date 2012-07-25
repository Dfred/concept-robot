#ifndef QRK_C_SERIAL_ERRNO_H
#define QRK_C_SERIAL_ERRNO_H

/*!
  \file
  \brief �V���A������M�̃G���[��`

  \author Satofumi KAMIMURA

  $Id: serial_errno.h 1300 2009-09-15 06:36:54Z satofumi $
*/

enum {
  SerialNoError = 0,            /*!< ���� */
  SerialNotImplemented = -1,    /*!< ������ */
  SerialConnectionFail = -2,    /*!< �ڑ��G���[ */
  SerialSendFail = -3,          /*!< ���M�G���[ */
  SerialRecvFail = -4,          /*!< ��M�G���[ */
  SerialSetBaudrateFail = -5,   /*!< �{�[���[�g�ݒ�G���[ */

  /* !!! */
};

#endif /* !QRK_C_SERIAL_ERRNO_H */
