/*!
  \file
  \brief �V���A���ʐM (Windows ����)

  Serial Communication Interface ����

  \author Satofumi KAMIMURA

  $Id: serial_ctrl_win.c 1559 2009-12-01 13:13:08Z satofumi $
*/

#include "serial_ctrl.h"
#include "serial_errno.h"
#include "ring_buffer.h"
#include <stdio.h>


enum {
  False = 0,
  True,
};


static void setTimeout(serial_t *serial, int timeout)
{
  COMMTIMEOUTS timeouts;
  GetCommTimeouts(serial->hCom_, &timeouts);

  timeouts.ReadIntervalTimeout = (timeout == 0) ? MAXDWORD : 0;
  timeouts.ReadTotalTimeoutConstant = timeout;
  timeouts.ReadTotalTimeoutMultiplier = 0;

  SetCommTimeouts(serial->hCom_, &timeouts);
}


void serial_initialize(serial_t *serial)
{
  serial->hCom_ = INVALID_HANDLE_VALUE;
  serial->errno_ = SerialNoError;
  serial->has_last_ch_ = False;

  ring_initialize(&serial->ring_, serial->buffer_, RingBufferSizeShift);
}


/* �ڑ� */
int serial_connect(serial_t *serial, const char *device, long baudrate)
{
  // COM10 �ȍ~�ւ̑Ή��p
  enum { NameLength = 11 };
  char adjusted_device[NameLength];

  serial_initialize(serial);

  /* COM �|�[�g���J�� */
  _snprintf(adjusted_device, NameLength, "\\\\.\\%s", device);
  serial->hCom_ = CreateFileA(adjusted_device, GENERIC_READ | GENERIC_WRITE, 0,
                              NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);

  if (serial->hCom_ == INVALID_HANDLE_VALUE) {
    printf("open failed: %s\n", device);
    return -1;
  }

  /* �ʐM�T�C�Y�̍X�V */
  SetupComm(serial->hCom_, 4096 * 8, 4096);

  /* �{�[���[�g�̕ύX */
  serial_setBaudrate(serial, baudrate);

  /* �V���A������\���̂̏����� */
  serial->has_last_ch_ = False;

  /* �^�C���A�E�g�̐ݒ� */
  serial->current_timeout_ = 0;
  setTimeout(serial, serial->current_timeout_);

  return 0;
}


/* �ؒf */
void serial_disconnect(serial_t *serial)
{
  if (serial->hCom_ != INVALID_HANDLE_VALUE) {
    CloseHandle(serial->hCom_);
    serial->hCom_ = INVALID_HANDLE_VALUE;
  }
}


int serial_isConnected(const serial_t *serial)
{
  return (serial->hCom_ == INVALID_HANDLE_VALUE) ? 0 : 1;
}


/* �{�[���[�g�̕ύX */
int serial_setBaudrate(serial_t *serial, long baudrate)
{
  long baudrate_value;
  DCB dcb;

  switch (baudrate) {

  case 4800:
    baudrate_value = CBR_4800;
    break;

  case 9600:
    baudrate_value = CBR_9600;
    break;

  case 19200:
    baudrate_value = CBR_19200;
    break;

  case 38400:
    baudrate_value = CBR_38400;
    break;

  case 57600:
    baudrate_value = CBR_57600;
    break;

  case 115200:
    baudrate_value = CBR_115200;
    break;

  default:
    baudrate_value = baudrate;
  }

  GetCommState(serial->hCom_, &dcb);
  dcb.BaudRate = baudrate_value;
  dcb.ByteSize = 8;
  dcb.Parity = NOPARITY;
  dcb.fParity = FALSE;
  dcb.StopBits = ONESTOPBIT;
  SetCommState(serial->hCom_, &dcb);

  return 0;
}


/* ���M */
int serial_send(serial_t *serial, const char *data, int data_size)
{
  DWORD n;

  if (data_size < 0) {
    return 0;
  }

  if (! serial_isConnected(serial)) {
    return SerialConnectionFail;
  }

  WriteFile(serial->hCom_, data, (DWORD)data_size, &n, NULL);
  return n;
}


static int internal_receive(char data[], int data_size_max,
                            serial_t* serial, int timeout)
{
  int filled = 0;
  DWORD n;

  if (timeout != serial->current_timeout_) {
    setTimeout(serial, timeout);
    serial->current_timeout_ = timeout;
  }

  ReadFile(serial->hCom_, &data[filled],
           (DWORD)data_size_max - filled, &n, NULL);

  return filled + n;
}


/* ��M */
int serial_recv(serial_t *serial, char* data, int data_size_max, int timeout)
{
  int filled = 0;
  int buffer_size;
  int read_n;

  if (data_size_max <= 0) {
    return 0;
  }

  /* �����߂����P����������΁A�����o�� */
  if (serial->has_last_ch_) {
    data[0] = serial->last_ch_;
    serial->has_last_ch_ = False;
    ++filled;
  }

  if (! serial_isConnected(serial)) {
    if (filled > 0) {
      return filled;
    }
    return SerialConnectionFail;
  }

  buffer_size = ring_size(&serial->ring_);
  read_n = data_size_max - filled;
  if (buffer_size < read_n) {
    // �����O�o�b�t�@���̃f�[�^�ő���Ȃ���΁A�f�[�^��ǂݑ���
    char buffer[RingBufferSize];
    int n = internal_receive(buffer,
                             ring_capacity(&serial->ring_) - buffer_size,
                             serial, 0);
    ring_write(&serial->ring_, buffer, n);
  }
  buffer_size = ring_size(&serial->ring_);

  // �����O�o�b�t�@���̃f�[�^��Ԃ�
  if (read_n > buffer_size) {
    read_n = buffer_size;
  }
  if (read_n > 0) {
    ring_read(&serial->ring_, &data[filled], read_n);
    filled += read_n;
  }

  // �f�[�^���^�C���A�E�g�t���œǂݏo��
  filled += internal_receive(&data[filled],
                             data_size_max - filled, serial, timeout);
  return filled;
}


/* �P���������߂� */
void serial_ungetc(serial_t *serial, char ch)
{
  serial->has_last_ch_ = True;
  serial->last_ch_ = ch;
}


void serial_clear(serial_t* serial)
{
  PurgeComm(serial->hCom_,
            PURGE_RXABORT | PURGE_TXABORT | PURGE_RXCLEAR | PURGE_TXCLEAR);

  serial->has_last_ch_ = False;
}
