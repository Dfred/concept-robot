/*!
  \file
  \brief ƒVƒŠƒAƒ‹’ÊM

  Serial Communication Interface §Œä


  \author Satofumi KAMIMURA

  $Id: serial_ctrl.c 772 2009-05-05 06:57:57Z satofumi $
*/

#include "serial_ctrl.h"

#if defined(WINDOWS_OS)
/* Windows (win32) ŠÂ‹« */
#include "win/serial_ctrl_win.c"

#else
/* Linux, Mac ŠÂ‹« (‹¤’Ê) */
#include "lin/serial_ctrl_lin.c"
#endif
