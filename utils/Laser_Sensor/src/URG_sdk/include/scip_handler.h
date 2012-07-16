#ifndef QRK_C_SCIP_HANDLER_H
#define QRK_C_SCIP_HANDLER_H

/*!
  \file
  \brief Process SKIP commands

  \author Satofumi KAMIMURA

  $Id: scip_handler.h 1948 2011-04-19 09:59:29Z satofumi $
*/

#include "urg_parameter_t.h"
#include "serial_t.h"


enum {
  ScipNoWaitReply = 0,          /*!< Dont wait for reply */
  ScipWaitReply = 1,            /*!< Wait for reply */
  ScipLineWidth = 64 + 1 + 1,   /*!< Maximum length of one line */
};


/*!
  \brief Send command

  \param[out] serial Structure of serial control
  \param[in] send_command Command to be sent

  \retval 0 Normal
  \retval < 0 Error
*/
extern int scip_send(serial_t *serial, const char *send_command);


/*!
  \brief Receive command response

  Store the response of the command if "ret" value is zero.\n

  When the command response is included in expected_ret, the return value of this function becomes 0 (normality).

  \param[out] serial Structure of serial control
  \param[in] command_first first command
  \param[out] return_code Return value
  \param[in] expected_ret Return value considered to be normal
  \param[in] timeout Time out [msec]

  \retval 0 Normal
  \retval < 0 Error
*/
extern int scip_recv(serial_t *serial, const char *command_first,
                     int* return_code, int expected_ret[],
                     int timeout);


/*!
  \brief Transit to SCIP2.0 mode

  Return 0(Normal) when changed to SCIP2.0 mode

  \param[in,out] serial Structure of serial control

  \retval 0 Normal
  \retval < 0 Error
*/
extern int scip_scip20(serial_t *serial);


/*!
  \brief Stop measurement and turn off the laser.

  If the purpose is to stop MD, then send QT command without waiting for the response from MD command.
  Process the response of QT in urg_receiveData()

  \param[in,out] serial Structure of serial control
  \param[in] return_code Response from QT command
  \param[in] wait_reply ScipNoWaitReply when response is not waited. ScipWaitReply when response is waited.

  \retval 0 Normal
  \retval < 0 Error
*/
extern int scip_qt(serial_t *serial, int *return_code, int wait_reply);


/*!
  \brief Get Parameter information

  \param[in,out] serial Structure of serial control
  \param[out] parameters urg_parameter_t Structure member

  \retval 0 Normal
  \retval < 0 Error

*/
extern int scip_pp(serial_t *serial, urg_parameter_t *parameters);


/*!
  \brief Get version information

  \param[in,out] serial Structure of serial control
  \param[out] lines Storage location of characters containing version information.
  \param[in] lines_max Maximum number of character string

  \retval 0 Normal
  \retval < 0 Error
*/
extern int scip_vv(serial_t *serial, char *lines[], int lines_max);


/*!
  \brief Change baudrate

  \param[in,out] serial Structure of serial control
  \param[in] baudrate Baudrate

  \retval 0 Normal
  \retval < 0 Error
*/
extern int scip_ss(serial_t *serial, long baudrate);

#endif /* !QRK_C_SCIP_HANDLER_H */
