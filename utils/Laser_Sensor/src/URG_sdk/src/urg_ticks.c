/*!
  \file
  \brief �^�C���X�^���v�擾�֐�

  \author Satofumi KAMIMURA

  $Id: urg_ticks.c 1733 2010-03-06 01:19:49Z satofumi $
*/

#include "urg_ticks.h"
#include "detect_os.h"
#if defined WINDOWS_OS
#include <time.h>
#else
#include <sys/time.h>
#include <stdio.h>
#endif


long urg_ticks(void)
{
  long current_ticks = 0;

#if defined(LINUX_OS)
  // Linux �� SDL ���Ȃ��ꍇ�̎����B�ŏ��̌Ăяo���� 0 ��Ԃ�
  static long first_ticks = 0;
  struct timeval tvp;
  gettimeofday(&tvp, NULL);
  long global_ticks = tvp.tv_sec * 1000 + tvp.tv_usec / 1000;
  if (first_ticks == 0) {
    first_ticks = global_ticks;
  }
  current_ticks = global_ticks - first_ticks;

#else
  current_ticks = (long)(clock() / (CLOCKS_PER_SEC / 1000.0));
#endif
  return current_ticks;
}
