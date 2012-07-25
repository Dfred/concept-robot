#ifndef RING_BUFFER_H
#define RING_BUFFER_H

/*!
  \file
  \brief �����O�o�b�t�@

  \author Satofumi KAMIMURA

  $Id: ring_buffer.h 1811 2010-04-30 16:12:05Z satofumi $
*/


//! �����O�o�b�t�@�̊Ǘ����
typedef struct
{
    char *buffer;                 //!< �o�b�t�@�ւ̃|�C���^
    int buffer_size;              //!< �o�b�t�@�T�C�Y
    int first;                    //!< �o�b�t�@�̐擪�ʒu
    int last;                     //!< �o�b�t�@�̍ŏI�ʒu
} ringBuffer_t;


/*!
  \brief ������

  \param[in] ring �����O�o�b�t�@�̍\����
  \param[in] buffer ���蓖�Ă�o�b�t�@
  \param[in] shift_length �o�b�t�@�T�C�Y�� 2 �̏搔
*/
extern void ring_initialize(ringBuffer_t *ring,
                            char *buffer, const int shift_length);


/*!
  \brief �����O�o�b�t�@�̃N���A

  \param[in] ring �����O�o�b�t�@�̍\����
*/
extern void ring_clear(ringBuffer_t *ring);


/*!
  \brief �i�[�f�[�^����Ԃ�

  \param[in] ring �����O�o�b�t�@�̍\����
*/
extern int ring_size(const ringBuffer_t *ring);


/*!
  \brief �ő�̊i�[�f�[�^����Ԃ�

  \param[in] ring �����O�o�b�t�@�̍\����
*/
extern int ring_capacity(const ringBuffer_t *ring);


/*!
  \brief �f�[�^�̊i�[

  \param[in] ring �����O�o�b�t�@�̍\����
  \param[in] data �f�[�^
  \param[in] size �f�[�^�T�C�Y

  \return �i�[�����f�[�^��
*/
extern int ring_write(ringBuffer_t *ring, const char *data, int size);


/*!
  \brief �f�[�^�̎��o��

  \param[in] ring �����O�o�b�t�@�̍\����
  \param[out] buffer �f�[�^
  \param[in] size �ő�̃f�[�^�T�C�Y

  \return ���o�����f�[�^��
*/
extern int ring_read(ringBuffer_t *ring, char *buffer, int size);

#endif /* ! RING_BUFFER_H */
