/*!
  \file
  \brief �V���A���ʐM

  Serial Communication Interface ����


  \author Satofumi KAMIMURA

  $Id: serial_ctrl.c 772 2009-05-05 06:57:57Z satofumi $
*/

#include "serial_ctrl.h"

#if defined(WINDOWS_OS)
/* Windows (win32) �� */
#include "win/serial_ctrl_win.c"

#else
/* Linux, Mac �� (����) */
#include "lin/serial_ctrl_lin.c"
#endif
