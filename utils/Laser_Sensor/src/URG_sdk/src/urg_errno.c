/*!
  \file
  \brief Error code of URG

  \author Satofumi KAMIMURA

  $Id: urg_errno.c 1666 2010-02-03 03:44:15Z satofumi $
*/

#include "urg_errno.h"


/* Returns error message */
const char* urg_strerror(const int errno)
{
  const char *errorStr[] = {
    "Unknown",
    "Not Implemented.",
    "Send fail.",
    "Receive fail.",
    "SCIP1.1 protocol is not supported. Please update URG firmware.",
    "SS fail.",
    "Adjust baudrate fail.",
    "Invalid parameters.",
    "Urg invalid response.",
    "Serial connection fail.",
    "Serial receive fail.",
    "Response mismatch.",
    "No Response.",
    "UTM-30LX is not supported GD_INTENSITY. Please use MD_INTENSITY",
    "dummy.",
  };

  int n = sizeof(errorStr) / sizeof(errorStr[0]);
  if ((-errno >= n) || (errno > 0)) {
    return errorStr[0];
  }

  return errorStr[-errno];
}
