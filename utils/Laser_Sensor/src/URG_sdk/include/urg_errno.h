#ifndef QRK_C_URG_ERRNO_H
#define QRK_C_URG_ERRNO_H

/*!
  \file
  \brief Error code of URG

  \author Satofumi KAMIMURA

  $Id: urg_errno.h 1714 2010-02-21 20:53:28Z satofumi $
*/


enum {
  UrgNoError = 0,               /*!< Normal */
  UrgNotImplemented = -1,       /*!< Not implemented */
  UrgSendFail = -2,
  UrgRecvFail = -3,
  UrgScip10 = -4,               /*!< Response from SCIP1.0  */
  UrgSsFail = -5,               /*!< Error in response from SS command */
  UrgAdjustBaudrateFail = -6,   /*!< Fails to adjust baudrate */
  UrgInvalidArgs = -7,          /*!< Invalid argument specification */
  UrgInvalidResponse = -8,      /*!< Response error from URG side */
  UrgSerialConnectionFail = -9, /*!< Fail to establish serial connection */
  UrgSerialRecvFail = -10,      /*!< Fail to receive data */
  UrgMismatchResponse = -11,    /*!< Mismatch in echoback in response */
  UrgNoResponse = -12,          /*!< No response */
  UtmNoGDIntensity = -13, /*!< Coudn't receive intensity data by GD */
};


/*!
  \brief Returns error message

  \param[in] urg_errno Error value of URG

  \return error message
*/
extern const char* urg_strerror(const int urg_errno);

#endif /* !QRK_C_URG_ERRNO_H */
