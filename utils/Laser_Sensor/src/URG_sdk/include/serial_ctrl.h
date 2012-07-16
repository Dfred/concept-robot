#ifndef QRK_C_SERIAL_CTRL_H
#define QRK_C_SERIAL_CTRL_H

/*!
  \file
  \brief �V���A���ʐM

  Serial Communication Interface ����

  \author Satofumi KAMIMURA

  $Id: serial_ctrl.h 1553 2009-11-29 15:47:05Z satofumi $
*/

#include "serial_t.h"


extern void serial_initialize(serial_t *serial);


/*!
  \brief �ڑ�

  \param[in,out] serial �V���A������̍\����
  \param[in] device �ڑ��f�o�C�X
  \param[in] baudrate �ڑ��{�[���[�g

  \retval 0 ����
  \retval < 0 �G���[
*/
extern int serial_connect(serial_t *serial, const char *device, long baudrate);


/*!
  \brief �ؒf

  \param[in,out] serial �V���A������̍\����
*/
extern void serial_disconnect(serial_t *serial);


/*!
  \brief �ڑ�������Ԃ�

  \param[in] serial �V���A������̍\����

  \retval 1 �ڑ���
  \retval 0 �ؒf��
*/
extern int serial_isConnected(const serial_t *serial);


/*!
  \brief �{�[���[�g�̕ύX

  \param[in,out] serial �V���A������̍\����
  \param[in] baudrate �{�[���[�g

  \retval 0 ����
  \retval < 0 �G���[
*/
extern int serial_setBaudrate(serial_t *serial, long baudrate);


/*!
  \brief ���M

  \param[in,out] serial �V���A������̍\����
  \param[in] data ���M�f�[�^
  \param[in] data_size ���M�T�C�Y

  \retval >= 0 ���M�T�C�Y
  \retval < 0 �G���[
*/
extern int serial_send(serial_t *serial, const char *data, int data_size);


/*!
  \brief ��M

  \param[in,out] serial �V���A������̍\����
  \param[in] data ��M�f�[�^�i�[�o�b�t�@
  \param[in] data_size_max ��M�o�b�t�@�̍ő�T�C�Y
  \param[in] timeout �^�C���A�E�g [msec]

  \retval >= 0 ��M�T�C�Y
  \retval < 0 �G���[
*/
extern int serial_recv(serial_t *serial,
                       char *data, int data_size_max, int timeout);


/*!
  \brief ��M�����P�����������߂�

  \param[in,out] serial �V���A������̍\����
  \param[in] ch �����߂��P����

  \attention �ǂݏo�����s�킸�ɁA�A�����ď����߂��Ă͂Ȃ�Ȃ�
*/
extern void serial_ungetc(serial_t *serial, char ch);


/*!
  \brief ����M�o�b�t�@��j��
*/
extern void serial_clear(serial_t* serial);

#endif /* !QRK_C_SERIAL_CTRL_H */
