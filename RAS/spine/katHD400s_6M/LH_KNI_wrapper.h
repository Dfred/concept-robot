/*******************************************************************************
 * kni_wrapper.h - 
 * A wrapper for the kni library so that the C++ library 
 * can be accessed by C based environments (MatLab, LabView ...)
 * Copyright (C) Neuronics AG
 * Philipp Keller, Tino Perucchi, 2008
 ******************************************************************************/

/*******************************************************************************
 * Frederic Delaunay @ plymouth.ac.uk: appended functions:
- getEncoders
- getVelocities
- getAxisMinMaxEPC
- moveMotFaster
- is_moving
- is_blocked
 also applied cosmetics to original KNI files.
 ******************************************************************************/


/* define EXPORT_FCNS before including this file in source files that build the
   library*/

#ifndef _KNI_WRAPPER_H_
#define _KNI_WRAPPER_H_

#ifdef EXPORT_FCNS
# include "kniBase.h"
# include "common/exception.h"
# include <vector>
# ifdef WIN32
#  define DLLEXPORT __declspec(dllexport)
# else
#  define DLLEXPORT 
# endif

#else	// EXPORT_FCNS
# ifdef WIN32
#  define DLLEXPORT __declspec(dllimport)
# else
#  define DLLEXPORT
# endif
#endif

const double PI = 3.14159265358979323846;
//additional error codes
enum{ 
  ERR_NONE = 0,
  ERR_SUCCESS = 1
};

/******************************************************************************/

#ifdef __cplusplus
extern "C" {
#endif

  //!structure representing a point & orientation in space
  struct TPos{
    //!The position in cartesian space
    double X, Y, Z;
    //!the orientation of the TCP
    double phi, theta, psi;
  };

  //!the transition types for a movement
  typedef enum {
    //!Point-to-point movement
    PTP = 1,
    //!linear movement
    LINEAR = 2
  } ETransition;

  //!structure for the 
  struct TMovement{
    //!The position, see above struct TPos
    struct TPos pos;
    //!the transition to this position, PTP or LINEAR
    ETransition transition;
    //!The velocitiy for this particular movement
    int velocity;
    //!the acceleration for this particular movement
    int acceleration;
  };

  //!structure for the currently active axis
  struct TCurrentMot{
    int idx;
    bool running;
    bool dir;
  };

  //////////////////////////////////////////////////////////////////////////////
  //!Switches all axes off
  //!@return returns -1 on failure, 1 if successful
  DLLEXPORT int  
  allMotorsOff();
	
  //!Puts all axes into hold state
  //!@return returns -1 on failure, 1 if successful
  DLLEXPORT int  
  allMotorsOn();

  //!Closes the Katana session
  //!@return returns -1 on failure, 1 if successful
  DLLEXPORT int  
  calibrate();
	
  //!Clears the movebuffers
  DLLEXPORT int  
  clearMoveBuffers();
	
  //!Closes the gripper if available
  //!@return returns ERR_FAILURE on failure, 
  //!ERR_INVALID_ARGUMENT if an argument is out of range,
  //!ERR_STATE_MISMATCH if the command was given to a wrong state, 
  //!1 if successful
  DLLEXPORT int  
  closeGripper();	
  
  //!Deletes a movement from the stack
  //!@param name the name of the stack
  //!@param index the index of the movement to delete
  DLLEXPORT int  
  deleteMovementFromStack(char* name, int index);	
	
  //!Deletes a movemnt stack
  DLLEXPORT int  
  deleteMovementStack(char* name);	
	
  //!Executes a connected movement
  //!@param movement	a TMovement struct to execute
  //!@param startPos	start position, can be omitted if first=true
  //!@param first	first of the connected movements (start at current pos)
  //!@param last	last of the connected movements (wait for end of move)
  DLLEXPORT int executeConnectedMovement(struct TMovement *movement,
					 struct TPos *startPos,
					 bool first, bool last);
	
  //!Executes a movement
  //!@param movement movement to execute, starting from the current position
  DLLEXPORT int  
  executeMovement(struct TMovement *movement);
	
  //!Flushes all the movebuffers
  DLLEXPORT int flushMoveBuffers();
	
  //!Gets the axis firmware version and returns it in the value argument
  // length of value array at least 12, will be '\0' terminated
  DLLEXPORT int  
  getAxisFirmwareVersion(int axis, char value[]);	
	
  //!Gets the pwm and returns it in the value argument
  //!@param axis The axis to send the command to
  //!@return returns ERR_FAILURE on failure, 
  //!ERR_INVALID_ARGUMENT if an argument is out of range,
  //!ERR_STATE_MISMATCH if the command was given to a wrong state, 
  //!1 if successful
  DLLEXPORT int  
  getDrive(int axis, int *value);	
	
  //!Gets the position and returns it in the value argument
  //!@param axis The axis to send the command to
  //!@return returns ERR_FAILURE on failure, 
  //!ERR_INVALID_ARGUMENT if an argument is out of range,
  //!ERR_STATE_MISMATCH if the command was given to a wrong state, 
  //!1 if successful
  DLLEXPORT int  
  getEncoder(int axis, int *value);

  //!Returns the number of motors configured
  DLLEXPORT int  
  getNumberOfMotors();

  //!Gets a position
  DLLEXPORT int  
  getPosition(struct TPos *pos);

  //!Gets the velocity and returns it in the value argument
  //!@param axis The axis to send the command to
  //!@return returns -1 on failure, 1 if successful
  /*DLLEXPORT int  
    getVelocity(int axis, int *value);
  */

  //!Gets the controlboard firmware version and returns it in the value argument
  // length of value array at least 8, will be '\0' terminated
  DLLEXPORT int  
  getVersion(char value[]);
	
  //!This initializes the Katana (communication etc)
  DLLEXPORT int  
  initKatana(char* configFile, char* ipaddress);
	
  //!Reads an input from the digital I/O and returns it in the value argument
  //!@return returns ERR_FAILURE on failure, 
  //!ERR_INVALID_ARGUMENT if an argument is out of range,
  //!ERR_STATE_MISMATCH if the command was given to a wrong state, 
  //!1 if successful
  DLLEXPORT int  
  IO_readInput(int inputNr, int *value);

  //I/O Interface
  //!Sets an output of the digital I/Os
  //!@param ouputNr 1, or 2 for OutA or OutB
  //!@return returns -1 on failure, 1 if successful
  DLLEXPORT int  
  IO_setOutput(char output, int value);

  //!Reads a value from the register 'address'(connect to the IP in katana.conf)
  // and returns it in the value argument given by reference
  //!@return returns -1 on failure, the read value if successful
  DLLEXPORT int  
  ModBusTCP_readWord(int address, int *value);
  
  //!Writes a value to the register 'address' (connect to the IP in katana.conf)
  //!@return returns -1 on failure, 1 if successful
  DLLEXPORT int  
  ModBusTCP_writeWord(int address, int value);

  //!Switches an axis off
  //!@param axis The axis to send the command to
  //!@return returns ERR_FAILURE on failure, 
  //!ERR_INVALID_ARGUMENT if an argument is out of range,
  //!ERR_STATE_MISMATCH if the command was given to a wrong state, 
  //!1 if successful
  DLLEXPORT int  
  motorOff(int axis);
	
  //!Switches an axis on
  //!@param axis The axis to send the command to
  //!@return returns ERR_FAILURE on failure, 
  //!ERR_INVALID_ARGUMENT if an argument is out of range,
  //!ERR_STATE_MISMATCH if the command was given to a wrong state, 
  //!1 if successful
  DLLEXPORT int  
  motorOn(int axis);
	
  //!PTP movement
  //!@param axis The axis to send the command to
  //!@param enc the target position
  //!@return returns ERR_FAILURE on failure, 
  //!ERR_INVALID_ARGUMENT if an argument is out of range,
  //!ERR_STATE_MISMATCH if the command was given to a wrong state, 
  //!1 if successful
  DLLEXPORT int  
  moveMot(int axis, int enc, int speed, int accel);
  
  //!Calls MoveMot() and WaitForMot()
  //!@param axis The axis to send the command to
  //!@param tolerance in encoder values (0 means wait until reached)
  //!@return returns ERR_FAILURE on failure, 
  //!ERR_INVALID_ARGUMENT if an argument is out of range,
  //!ERR_STATE_MISMATCH if the command was given to a wrong state,  
  //!ERR_RANGE_MISMATCH if the target position is out of range
  //!1 if successful
  DLLEXPORT int  
  moveMotAndWait(int axis, int targetpos, int tolerance);
	
  //!Moves in IK
  DLLEXPORT int  
  moveToPos(struct TPos *pos, int velocity, int acceleration);
  
  //!Moves all axes to a target encoder value
  //!@param enc (encX) the target positions
  //!@param tolerance in encoders. sent unscaled to axis and handled there.
  //!WaitForMot (and MoveMOtAndWait) checks the tolerance though.
  //!@param wait wait for the movement to finish
  //!@return returns ERR_FAILURE on failure, 
  //!ERR_INVALID_ARGUMENT if an argument is out of range,
  //!ERR_STATE_MISMATCH if the command was given to a wrong state, 
  //!1 if successful
  DLLEXPORT int  
  moveToPosEnc(int enc1, int enc2, int enc3, int enc4, int enc5, int enc6,
	       int velocity, int acceleration, int tolerance, bool _wait);
	
  //!Moves in LM
  DLLEXPORT int  
  moveToPosLin(struct TPos *targetPos, int velocity, int acceleration);
  
  //!Opens the gripper if available
  //!@return returns ERR_FAILURE on failure, 
  //!ERR_INVALID_ARGUMENT if an argument is out of range,
  //!ERR_STATE_MISMATCH if the command was given to a wrong state, 
  //!1 if successful
  DLLEXPORT int  
  openGripper();

  //!Checks the alive state of an axis
  //!@param axis 0 = get all axes
  //!@return If axis 0: 1 if all axes are present,
  //!negative value is the inverted number of the first axis found failing,
  //!0 if no data is available. If axis != 0: 1 if heartbeat found,
  //!-1 if failed, 0 if no data is available.
  DLLEXPORT int  
  ping(int axis);

  //!Pushes a movement onto a stack
  //!@param movement structure filled with position and movement parameters
  //!@param name the name of the stack to push it onto
  DLLEXPORT int  
  pushMovementToStack(struct TMovement *movement, char* name);

  //!Runs through the movement stack, executes the movements
  //!@param name the name of the stack to run through
  //!@param loops the number of loops to run
  DLLEXPORT int  
  runThroughMovementStack(char* name, int loops);

  //Linear Movement
  //!Sends a single polynomial to an axis (G)
  //!@param axis The axis to send the command to
  //!@return returns ERR_FAILURE on failure, 
  //!ERR_INVALID_ARGUMENT if an argument is out of range,
  //!ERR_STATE_MISMATCH if the command was given to a wrong state,  
  //!ERR_RANGE_MISMATCH if the target position is out of range
  //!1 if successful
  DLLEXPORT int  
  sendSplineToMotor(int axis, int targetpos, int duration,
				   int p0, int p1, int p2, int p3);
  
  //!Sets the collision detection on the axes. 
  //!@param state true = on
  //!@param axis 0 = set all axes
  //!@return returns ERR_FAILURE on failure, 
  //!ERR_INVALID_ARGUMENT if an argument is out of range,
  //!ERR_STATE_MISMATCH if the command was given to a wrong state, 
  //!1 if successful
  DLLEXPORT int  
  setCollisionDetection(int axis, bool state);
  
  //!Sets the collision parameters
  //!this function calls setPositionCollisionLimit and setVelocityCollisionLimit
  //!@param axis 0 = set all axes
  //!@param position range 1-10
  //!@param velocity range 1-10
  DLLEXPORT int  
  setCollisionParameters(int axis, int position, int velocity);
  
  //!Sets the controller parameters
  //!@param axis 0 = set all axes
  //!@return returns ERR_FAILURE on failure, 
  //!ERR_INVALID_ARGUMENT if an argument is out of range,
  //!ERR_STATE_MISMATCH if the command was given to a wrong state, 
  //!1 if successful
  DLLEXPORT int  
  setControllerParameters(int axis, int ki, int kspeed, int kpos);
  
  //!Sets or unsets whether the Katana has a Gripper
  //!@param hasGripper true if gripper present. Startup default: false
  //!@return returns ERR_FAILURE on failure, 
  //!ERR_INVALID_ARGUMENT if an argument is out of range,
  //!ERR_STATE_MISMATCH if the command was given to a wrong state, 
  //!1 if successful
  DLLEXPORT int  
  setGripper(bool hasGripper);	

  //!Sets the maximum acceleration (allowed values are only 1 and 2)
  //!@param axis 0 = set all axes
  //!@return returns ERR_FAILURE on failure, 
  //!ERR_INVALID_ARGUMENT if an argument is out of range,
  //!ERR_STATE_MISMATCH if the command was given to a wrong state, 
  //!1 if successful
  DLLEXPORT int  
  setMaxAccel(int axis, int acceleration);
  
  //!Sets the maximum velocity
  //!@param axis 0 = set all axes
  //!@param vel 1-180 are valid
  //!@return returns ERR_FAILURE on failure, 
  //!ERR_INVALID_ARGUMENT if an argument is out of range,
  //!ERR_STATE_MISMATCH if the command was given to a wrong state, 
  //!1 if successful
  DLLEXPORT int  
  setMaxVelocity(int axis, int vel);
  
  //!Sets the position collision limit
  //!@param axis 0 = all axes
  DLLEXPORT int  
  setPositionCollisionLimit(int axis, int limit);
  
  //!Sets the velocity collision limit
  //!@param axis 0 = all axes
  DLLEXPORT int  
  setVelocityCollisionLimit(int axis, int limit); 
  
  //!Sets the force limit
  //!@param axis 0 = all axes
  //!@param limit limit in percent
  DLLEXPORT int  
  setForceLimit(int axis, int limit); 
  
  //!Sets the current force
  DLLEXPORT int  
  getForce(int axis); 
  
  //!Sets the current controller limit
  //!@return 0 for position controller, 1 for current controller
  DLLEXPORT int  
  getCurrentControllerType(int axis); 
  
  //!Starts the linear movement (G+128)
  //!@return returns -1 on failure, 1 if successful
  DLLEXPORT int  
  startSplineMovement(int contd, int exactflag);
  
  //!Unblocks the robot after collision/instantstop
  DLLEXPORT int  
  unblock();

  //!Waits for a motor
  //!@param axis The axis to wait for
  //!@param targetpos (only relevant if mode is 0)
  //!@param tolerance (only relevant if mode is 0) in encoder values
  //!@return returns ERR_FAILURE on failure, 
  //!ERR_INVALID_ARGUMENT if an argument is out of range,
  //!ERR_STATE_MISMATCH if the command was given to a wrong state, 
  //!ERR_RANGE_MISMATCH if the target position is out of range
  //!1 if successful
  DLLEXPORT int  
  waitForMot(int axis, int targetpos, int tolerance);

# define MAX_MOTORS 6

  //!Gets all motors encoder at once
  //!@param dest_encs An array of int
  //!@return returns -1 on failure, 1 if successful
  DLLEXPORT int
  getEncoders(int dest_encs[MAX_MOTORS]);

  //!Gets all motors velocity at once
  //!@param dest_vels An array of int
  //!@return returns -1 on failure, 1 if successful
  DLLEXPORT int  
  getVelocities(int dest_vels[6]);

  //!Gets minimum and maximum encoder values and Encoders Per Cycle for all axis
  //!@param dest_mins allocated table receiving minimum encoder values
  //!@param dest_mins allocated table receiving maximum encoder values
  //!@param dest_mins allocated table receiving encoder per cycle values
  //!@return returns -1 on failure, 1 if successful
  DLLEXPORT int
  getAllAxisMinMaxEPC(int dest_mins[MAX_MOTORS], 
		      int dest_maxs[MAX_MOTORS],
		      int dest_EPCs[MAX_MOTORS]);

  //!Faster version of moveMot (doesn't set speed nor acceleration)
  //!@param axis index of the motor to use
  //!@param enc_value encoder value
  //!@return returns -1 on failure, 1 if successful
  DLLEXPORT int
  moveMotFaster(int axis, int enc_value);

  //!Checks if a particular axis is blocked.
  //!@return returns -1 on failure, 0 if not blocked, 1 if axis is blocked.
  DLLEXPORT int
  is_blocked();

  //!Gets the moving status of one or all axis
  //!@param axis index of the motor to use. If 0, use all.
  //!@return returns -1 on failure, 0 if not moving, 1 if axis is moving.
  DLLEXPORT int
  is_moving(int axis);

#ifdef __cplusplus
}
#endif

#endif //_KNI_WRAPPER_H_
