# -*- coding: utf-8 -*-

import os
import time
import random
import sys
import subprocess
import optparse
import yaml
from serial.serialutil import SerialException
try:
    import dynamixel
except ImportError as e:
    print "dynamixel for python could not be imported."
    print "Try with easy-install or pip"
    sys.exit(4)

from consts import BAUD_RATES

"""
EXAMPLE
 
Move all attached servos randomly and read back the position they end up in.
"""

USER_ABORT = 2

def main(settings, statusReturnLevel, with_infos=False):

    portName = settings['port']
    baudRate = settings['baudRate']
    highestServoId = settings['highestServoId']

    if baudRate not in BAUD_RATES:
        print "{} isn't a standard baud rate {}".format(baudRate, BAUD_RATES)
        sys.exit(1)
    i = BAUD_RATES.index(baudRate)
    scan_allBR = False
    while i < len(BAUD_RATES):
        baudRate = BAUD_RATES[i]
        # Establish a serial connection to the dynamixel network.
        # This usually requires a USB2Dynamixel
        try:
            serial = dynamixel.SerialStream(port=portName,
                                            baudrate=baudRate,
                                            timeout=.1)
        except SerialException as e:
            print e
            sys.exit()
        except ValueError as e:
            print e
            i += 1
            continue
        net = dynamixel.DynamixelNetwork(serial)
    
        # Ping the range of servos that are attached
        print "Scanning for Dynamixels @%i bps... " % baudRate
        sys.stdout.flush()
        try:
            net.scan(1, highestServoId)
        except KeyboardInterrupt:
            sys.exit(USER_ABORT)

        myActuators = []

## Print servos' basic (or detailed) settings    
## http://support.robotis.com/en/product/dynamixel/ax_series/dxl_ax_actuator.htm

        for dyn in net.get_dynamixels():
            print "** FOUND #%i (return: status level %i (%s) -- delay %iμs)"% (
                dyn.id, dyn.status_return_level, 
                ["PING only","Rx only","Rx/Tx"][dyn.status_return_level],
                dyn.return_delay)
            if with_infos:
                print """\tmodel number: {} -- firmware: {}
\tsynchronized: {} -- lock: {}
\tAngles limit: CCW {} / CW {} => -{:.2f} / +{:.2f} deg.
\tTemperature: currently @{}°C -- limit {}°C
\tVoltage: currently @{}V -- limit low {}V / high {}V
\tTorque: {}abled -- limited @{:.2f}% ({}) / max set to {:.2f}% ({})
""".format(dyn.model_number, dyn.firmware_version,
           dyn.synchronized, dyn.lock,
           dyn.ccw_angle_limit, dyn.cw_angle_limit,
           dyn.ccw_angle_limit*.29, dyn.cw_angle_limit*.29,
           dyn.current_temperature, dyn.temperature_limit,
           dyn.current_voltage, dyn.low_voltage_limit, dyn.high_voltage_limit,
           dyn.torque_enable and "en" or "dis", 
           dyn.torque_limit/1023.*100, dyn.torque_limit,
           dyn.max_torque/1023.*100, dyn.max_torque)

            myActuators.append(net[dyn.id])
        if myActuators:
            break       #XXX: keep on scanning for others?

        print 'No Dynamixels Found!'
        if i == len(BAUD_RATES)-1:
            print "No further baud rate to check. Bailing out."
            sys.exit(3)
        if scan_allBR:
            i += 1
            continue
        rep = None
        try:
            rep = raw_input("scan with %i baud rate? [Y/n/skip/all]"%
                            BAUD_RATES[i+1])
            rep = rep and rep[0].lower()
        finally:
            if not rep or rep == 'n':
                print "user abort."
                sys.exit(USER_ABORT)
            elif rep == 's':
                i += 1
            elif rep == 'a':
                scan_allBR = True
            i += 1
    
    for actuator in myActuators:
        actuator.moving_speed = 150
        actuator.synchronized = True

        #XXX set return for all commands (otherwise timeout errors occur)
        if statusReturnLevel != None:
            if int(statusReturnLevel) == 0 and dynamixel.__version__ == '1.1.0':
                print "/!\ YOU'LL BREAK SCANNING FOR SERVOS WITH VERSION 1.1.0"\
                  " OF THE DYNAMIXEL PYTHON MODULE /!\\"
                if raw_input("Continue anyway? [N/y]").lower() != 'y':
                    sys.exit(USER_ABORT)
            print "setting #%i status return level to %s" % (actuator.id,
                                                             statusReturnLevel)
            actuator.status_return_level = int(statusReturnLevel)
        
        #XXX these accessors actually call set_register_value (Tx data)
        #XXX so they may fail with a timeout.
        for line in ("actuator.torque_enable = True",
                     "actuator.torque_limit = 1023",
                     "actuator.max_torque = 100"):
            try:
                exec(line)
            except dynamixel.stream.TimeoutException as e:
                if actuator.status_return_level > 1:
                    print "Unexpected {}: #{}> {}".format(e, actuator.id, line)

    # Randomly vary servo position within a small range
    print "Servo \tPosition"
    while True:
        for actuator in myActuators:
            actuator.goal_position = random.randrange(450, 600)
        net.synchronize()
        for actuator in myActuators:
            actuator.read_all()
            time.sleep(0.01)
        for actuator in myActuators:
            print "#%i" % actuator._id, "\t", actuator.current_position
        time.sleep(1)

def validateInput(userInput, rangeMin, rangeMax):
    """Return: valid user input or None
    """
    try:
        inTest = int(userInput)
        if inTest < rangeMin or inTest > rangeMax:
            print "ERROR: Value out of range [%s-%s]" % (rangeMin,rangeMax)
            return None
    except ValueError:
        print("ERROR: Integer required")
        return None
    
    return inTest

if __name__ == '__main__':
    
    parser = optparse.OptionParser()
    parser.add_option("-c", "--clean", dest="clean", action="store_true",
                      default=False, help="Ignore the settings.yaml file if it \
                      exists and prompt for new settings.")
    parser.add_option("-i", "--infos", dest="infos", action="store_true",
                      default=False, help="Print servos' settings.")
    parser.add_option("-r", "--set-SRL", dest="SRL", type="choice",
                      choices=('0','1','2'), default=None,
                      help="Set servos' Status Return Level (0, 1 or 2).")
    (options, args) = parser.parse_args()
    
    # Look for a settings.yaml file
    settingsFile = 'settings.yaml'
    if not options.clean and os.path.exists(settingsFile):
        with open(settingsFile, 'r') as fh:
            settings = yaml.load(fh)
    # If we were asked to bypass, or don't have settings
    else:
        settings = {}
        if os.name == "posix":
            # Get a list of ports that mention USB
            try:
                cmd = "cd /dev && ls | grep -E '(USB|ACM)'"
                possiblePorts = subprocess.check_output(cmd, shell=True).split()
                possiblePorts = ['/dev/' + port for port in possiblePorts]
            except subprocess.CalledProcessError:
                print "No USB2Dynamixel or USB2AX was found."
                sys.exit(6)
                
            counter = 1
            portCount = len(possiblePorts)
            portPrompt = "Select port to use:\n"
            for port in possiblePorts:
                portPrompt += "\t" + str(counter) + " - " + port + "\n"
                counter += 1
            portPrompt += "Enter Choice: "
            portChoice = None
            while not portChoice:                
                portTest = raw_input(portPrompt)
                portTest = validateInput(portTest, 1, portCount)
                if portTest:
                    portChoice = possiblePorts[portTest - 1]

        else:
            portChoice = raw_input("Enter USB2Dynamixel port/device name:")
    
        settings['port'] = portChoice
        
        # Baud rate
        baudRate = None
        while not baudRate:
            brTest = raw_input("Enter baud rate [Default: 1000000 bps]:")
            if not brTest:
                baudRate = 1000000
            else:
                baudRate = validateInput(brTest, 9600, 1000000)
                    
        settings['baudRate'] = baudRate
        
        # Servo ID
        highestServoId = None
        while not highestServoId:
            hsiTest = raw_input("Enter highest ID of the connected servos:")
            highestServoId = validateInput(hsiTest, 1, 255)
        
        settings['highestServoId'] = highestServoId
        
        # Save the output settings to a yaml file
        with open(settingsFile, 'w') as fh:
            yaml.dump(settings, fh)
            print("Your settings have been saved to 'settings.yaml'.\n"
                  "To change them in the future either edit that file or run "
                  "this example with -c.")
    
    main(settings, options.SRL, options.infos)
