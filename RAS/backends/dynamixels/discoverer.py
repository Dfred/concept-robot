# -*- coding: utf-8 -*-

import os
import time
import random
import sys
import subprocess
import optparse
import yaml
from serial.serialutil import SerialException

from __init__ import BAUD_RATES
from dynamixel_ext import DynamixelNetworkEx, DynamixelEx

import dynamixel

"""
EXAMPLE
 
Move all attached servos randomly and read back the position they end up in.
"""

USER_ABORT = 2
MIN_BAUD_RATE = 7350 # 7343
MAX_BAUD_RATE = 1000000
MOD_BAUD_RATE = 75
SERIAL_TIMEOUT = .5

def create_net(portName, baudRate):
    # Establish a serial connection to the dynamixel network.
    # This usually requires a USB2Dynamixel
    try:
        serial = dynamixel.SerialStream(port=portName,
                                        baudrate=baudRate,
                                        timeout=SERIAL_TIMEOUT)
    except SerialException as e:
        print "Error: ", e
        sys.exit()
#    return dynamixel.DynamixelNetwork(serial)
    return DynamixelNetworkEx(serial)

def show_info(dyn):
    dyn.read_all()
    print """\tmodel number:\t {} -- firmware: {}
\tAlarm shutdown:\t {} {}
\tAngles limit:\t CCW {} / CW {} => -{:.2f} / +{:.2f} deg.
\tTemperature:\t currently @{}°C -- limit {}°C
\tVoltage:\t currently @{}V -- limit low {}V / high {}V
\tTorque:\t\t {}abled -- limited @{:.2f}% ({}) / max set to {:.2f}% ({})
""".format(dyn.model_number, dyn.firmware_version,
           dyn.alarm_shutdown, net.error_text(dyn.alarm_shutdown),
           dyn.ccw_angle_limit, dyn.cw_angle_limit,
           dyn.ccw_angle_limit*.29, dyn.cw_angle_limit*.29,
           dyn.current_temperature, dyn.temperature_limit,
           dyn.current_voltage, dyn.low_voltage_limit, dyn.high_voltage_limit,
           dyn.torque_enable and "en" or "dis", 
           dyn.torque_limit/1023.*100, dyn.torque_limit,
           dyn.max_torque/1023.*100, dyn.max_torque)

def set_SRL(dyn, statusReturnLevel):
    ## set return for all commands (otherwise timeout errors occur)
    if int(statusReturnLevel) == 0 and dynamixel.__version__ == '1.1.0':
        print "/!\ YOU'LL BREAK SCANNING FOR SERVOS WITH VERSION "\
          "1.1.0 OF THE DYNAMIXEL PYTHON MODULE /!\\"
        if raw_input("Continue anyway? [N/y]").lower() != 'y':
            sys.exit(USER_ABORT)
        print "-*-*- setting #%i status return level to %s" % (
            dyn.id, statusReturnLevel)
        dyn.status_return_level = int(statusReturnLevel)

def discover(portName, baudRate, highestServoId):
    myActuators = []
    net = create_net(portName, baudRate)
    
    # Ping the range of servos that are attached
    try:
        print "Scanning for Dynamixels @%i bps... max ID: %i" % (
            baudRate, highestServoId)
        net.scan(1, highestServoId)
    except KeyboardInterrupt:
        sys.exit(USER_ABORT)

## Print servos' basic (or detailed) settings    
## http://support.robotis.com/en/product/dynamixel/ax_series/dxl_ax_actuator.htm

    for dyn in net.get_dynamixels():
        print "** FOUND #%i (return: status level %s (%i) -- delay %iμs)"% (
            dyn.id, ["PING only","Rx only","Rx/Tx"][dyn.status_return_level],
            dyn.status_return_level, dyn.return_delay)
        myActuators.append(net[dyn.id])
    return myActuators

def discover_loop(portName, baudRates, highestServoId):
    myActuators, found_baud_rates = [], []
    BD_it = baudRates.__iter__()
    baud_rate, BD_next = None, None
    scan_allBR = False
    try:
        while True:
            if baud_rate is None:
                try:
                    baud_rate = BD_it.next()
                except StopIteration:
                    if baud_rate is None:
                        break;
            try:
                acts = discover(portName, baud_rate, highestServoId)
                acts and myActuators.extend(acts)
            except KeyboardInterrupt:
                break
            try:
                BD_next = BD_it.next()
            except StopIteration:
                BD_next = None
            if BD_next and not scan_allBR:
                try:
                    rep = 'n'
                    rep = raw_input("scan with %i baud rate? [Y/n/skip/all]"%
                                    BD_next).lower()
                finally:
                    if not rep:
                        pass
                    elif rep[0] == 'n':
                        print "\nUser abort."
                        sys.exit(USER_ABORT)
                    elif rep[0] == 's':
                        BD_next = BD_it.next()
                    elif rep[0] == 'a':
                        scan_allBR = True
            baud_rate = BD_next
            BD_next = None
    finally:
        print "\nBaud rates found with replying servos: ", found_baud_rates
        return myActuators

def main(portName, highestServoId, baudRate, 
         newStatusReturnLevel, newBaudRate, newServoId,
         with_infos=False):
    if newBaudRate and newBaudRate not in BAUD_RATES:
        print "{} isn't a standard baud rate {}".format(newBaudRate, BAUD_RATES)
        sys.exit(1)
    
    try:
        BD_i = BAUD_RATES.index(baudRate)
    except ValueError:
        if baudRate >= MIN_BAUD_RATE:
            ## Non standard baud rate, full scan starting from baudRate
            ordered_bd = range(baudRate, MAX_BAUD_RATE+MOD_BAUD_RATE,
                               MOD_BAUD_RATE)
        else:
            ## scan with all BRs (not possible with USB2AX)
            ordered_bd = range(MIN_BAUD_RATE, MAX_BAUD_RATE+MOD_BAUD_RATE,
                               MOD_BAUD_RATE)
        nbr_tries = len(ordered_bd)*(highestServoId-1)
        print "Will scan %i IDs with %i baud rates (%i every %.2fs) => "\
        "%i tries" % (highestServoId-1, len(ordered_bd),
                      MOD_BAUD_RATE, SERIAL_TIMEOUT, nbr_tries)
        print "Will finish around %s" % time.ctime(time.time() +
                                                  nbr_tries * SERIAL_TIMEOUT)
    else:
        ## Requested a standard baud rate, that might fail..
        ordered_bd = BAUD_RATES[:]
        ordered_bd[0] = ordered_bd[BD_i]
        ordered_bd[BD_i] = BAUD_RATES[0]
    myActuators = discover_loop(portName, ordered_bd, highestServoId)

    ## Summary
    for actuator in myActuators:
        ## critical settings 1st...
        if new_baudRate != None:                        ## set servo's baud rate
            print "-*-*- setting #%i baud rate @%ibps" % (dyn.id, baudRate)
#            dyn.baud_rate = new_baudRate
        if statusReturnLevel != None:
            set_SRL(statusReturnLevel)
        if with_infos:
            show_infos(dyn)
        ## now more generic settings
        actuator.moving_speed = 0xff
        actuator.synchronized = True

        #XXX these accessors actually call set_register_value (Tx data)
        #XXX so they may fail with a timeout.
        for line in ("actuator.torque_enable = False",
                     "actuator.torque_limit = 1023",
                     "actuator.max_torque = 1023"):
            try:
                exec(line)
            except dynamixel.stream.TimeoutException as e:
                if actuator.status_return_level > 1:
                    print "Unexpected {}: #{}> {}".format(e, actuator.id, line)

    if not myActuators:
        return
    # Randomly vary servo position within a small range
    print myActuators, "Position"
    while True:
        for actuator in myActuators:
            actuator.goal_position = random.randrange(0, 1023)
        net.synchronize()
        for actuator in myActuators:
            actuator.read_all()
            time.sleep(0.01)
        for actuator in myActuators:
            print "#%i" % actuator._id, "\t", actuator.current_position
        time.sleep(2)

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
    parser.add_option("-b", "--use-baud-rate", dest="BR", type="int",
                      default=None, help="Use any of %s or 0 to scan using baud"
                      " rates from %i to %i bps (quite long), 1 to do the same"
                      " but without stopping on 1st find(very long)" % (
            [0]+BAUD_RATES, MIN_BAUD_RATE, MAX_BAUD_RATE) )
    parser.add_option("-i", "--infos", dest="infos", action="store_true",
                      default=False, help="Print servos' settings.")
    parser.add_option("-B", "--set-baud-rate", dest="newBR", type="choice",
                      choices=[str(br) for br in BAUD_RATES], default=None,
                      help="Set servo's Baud Rate. Works if a single servo is "
                      "found. Possible baud rates are %s." % BAUD_RATES)
    parser.add_option("-I", "--set-ID", dest="newID", type="int", default=0,
                      help="Set servo's ID. Works if a single servo is found.")
    parser.add_option("-R", "--set-SRL", dest="newSRL", type="choice",
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

    
    main(settings['port'], settings['highestServoId'], 
         settings['baudRate'] if options.BR is None else int(options.BR),
         options.newSRL, options.newBR, options.newID, options.infos)
