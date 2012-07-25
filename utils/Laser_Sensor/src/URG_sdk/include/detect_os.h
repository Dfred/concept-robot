#ifndef QRK_C_DETECT_OS_H
#define QRK_C_DETECT_OS_H

/*!
  \file
  \brief ����OS�̌��o

  \author Satofumi KAMIMURA

  $Id: detect_os.h 1939 2010-11-22 02:05:24Z satofumi $
*/

#if defined _MSC_VER || defined __CYGWIN__ || defined __MINGW32__
#define WINDOWS_OS

#if defined _MSC_VER
#define MSC
#elif defined __CYGWIN__
#define Cygwin
#elif defined __MINGW32__
#define MinGW
#endif

#elif defined __linux__
#define LINUX_OS

#else
// ���o�ł��Ȃ��Ƃ����AMac �����ɂ��Ă��܂�
#define MAC_OS
//#define EMBEDDED_OS
#endif

#endif /* !QRK_C_DETECT_OS_H */
