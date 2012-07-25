#ifndef QRK_SERIAL_UTILS_H
#define QRK_SERIAL_UTILS_H

/*!
  \file
  \brief �V���A������M�̕⏕

  \author Satofumi KAMIMURA

  $Id: serial_utils.h 783 2009-05-05 08:56:26Z satofumi $

  \todo ���͂�������ɂ́Aconst ��t������
*/

#include "serial_t.h"


/*!
  \brief ���s�R�[�h����Ԃ�

  \retval true LF, CR �̂Ƃ�
  \retval false ��L�ȊO�̂Ƃ�
*/
extern int serial_isLF(const char ch);


/*!
  \brief ��M�f�[�^��ǂݔ�΂�

  ConnectionInterface::clear() �Ƃ́A�^�C���A�E�g���Ԃ��w�肵�ēǂݔ�΂���_���قȂ�

  \param[in,out] serial �V���A������̍\����
  \param[in] total_timeout �^�C���A�E�g���Ԃ̏�� [msec]
  \param[in] each_timeout ��M�f�[�^�Ԃɂ�����^�C���A�E�g���Ԃ̏�� [msec]
*/
extern void serial_skip(serial_t *serial, int total_timeout,
                        int each_timeout);


/*!
  \brief ���s�܂ł̓ǂ݂���

  ������I�[�� '\\0' ��t�����ĕԂ�

  \param[in,out] serial �V���A������̍\����
  \param[in] data ��M�f�[�^�i�[�o�b�t�@
  \param[in] data_size_max ��M�o�b�t�@�̍ő�T�C�Y
  \param[in] timeout �^�C���A�E�g [msec]

  \return ��M������
*/
extern int serial_getLine(serial_t *serial,
                          char *data, int data_size_max, int timeout);

#endif /* !QRK_SERIAL_UTILS_H */
