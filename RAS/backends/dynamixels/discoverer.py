# -*- coding: utf-8 -*-

# ARAS is the open source software (OSS) version of the basic component of
# Syntheligence's software suite. This software is provided for academic
# research only. Any other use is not permitted.
# Syntheligence SAS is a robotics and software company established in France.
# For more information, visit http://www.syntheligence.com .

# ARAS stands for Abstract Robotic Animation System, and features actuator,
# sensor, animation and remote management high-level interfaces.
# Copyright 2013 Syntheligence, fdelaunay@syntheligence.com

# This software was originally named LightHead, the Human-Robot-Interaction part
# of the CONCEPT project, which took place at the University of Plymouth (UK).
# The project originated as the PhD pursued by Frédéric Delaunay, who was under
# the supervision of Prof. Tony Belpaeme.
# This PhD project started in late 2008 and ended in late 2011.
# Visit http://www.tech.plym.ac.uk/SoCCE/CONCEPT/ for more information.

#  This program is free software: you can redistribute it and/or
#   modify it under the terms of the GNU General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.

#  This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   General Public License for more details.

#  You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Inspired by the python dynamixel module's example (from Patrick Goebel).
Added all options but -c. This is covered by the GPL.

--- Original comment ---
Move all attached servos randomly and read back the position they end up in.
"""

import os
import time
import random
import sys
import subprocess
import optparse
import yaml
from serial.serialutil import SerialException

from __init__ import BAUD_RATES, ALL_BAUD_RATES, MAX_BAUD_RATE, MIN_BAUD_RATE
from dynamixel_ext import DynamixelNetworkEx, DynamixelEx

import dynamixel

USER_ABORT = 2
MOD_BAUD_RATE = 75
SERIAL_TIMEOUT = .1


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


def show_infos(net, dyn):
    dyn.read_all()
    print """\tmodel number:\t {} -- firmware: {}
\tConfigured Alarm shutdown:\t {}
\tAngles limit:\t CCW {} / CW {} => -{:.2f} / +{:.2f} deg.
\tTemperature:\t currently @{}°C -- limit {}°C
\tVoltage:\t currently @{}V -- limit low {}V / high {}V
\tTorque:\t\t {}abled -- limited @{:.2f}% ({}) / max set to {:.2f}% ({})
""".format(dyn.model_number, dyn.firmware_version,
           net.error_text(dyn.alarm_shutdown),
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

#    "Smin": [-1.2215, -1.047, -0.5235],
#    "Smax": [1.2215, 0.5235, 0.5235]


def discover(portName, baudRate, highestServoId):
    myActuators = []
    net = create_net(portName, baudRate)
    
    # Ping the range of servos that are attached
    print "Scanning for Dynamixels @%i bps... max ID: %i" % (
        baudRate, highestServoId)
    net.scan(0, highestServoId)
#    net.add_dynamixel(1)

## Print servos' basic (or detailed) settings    
## http://support.robotis.com/en/product/dynamixel/ax_series/dxl_ax_actuator.htm

    for dyn in net.get_dynamixels():
        print "*-*-* FOUND #%i (return: status level %s (%i) -- delay %iμs)" % (
            dyn.id, ["PING only","Rx only","Rx/Tx"][dyn.status_return_level],
            dyn.status_return_level, dyn.return_delay)
        myActuators.append(net[dyn.id])
    return net, myActuators


def discover_loop(portName, baudRates, highestServoId):
    myActuators, found_baud_rates = [], []
    BD_it = baudRates.__iter__()
    baud_rate, BD_next = None, None
    scan_allBR = False
    net = None
    while True:
        if baud_rate is None:
            try:
                baud_rate = BD_it.next()
            except StopIteration:
                if baud_rate is None:
                    break;
        try:
            net, acts = discover(portName, baud_rate, highestServoId)
            if acts:
                myActuators.extend(acts)
                found_baud_rates.append(baud_rate)
        except KeyboardInterrupt:
            break
        try:
            BD_next = BD_it.next()
        except StopIteration:
            BD_next = None
        if BD_next and not scan_allBR:
            try:
                rep = 'y'
                rep = raw_input("scan with %i baud rate? "
                                "[Yes/all/skip/done/quit]" % BD_next ).lower()
            except KeyboardInterrupt:
                print ""
                rep = 'q'
            finally:
                if not rep:
                    pass
                elif rep[0] == 'd':
                    break
                elif rep[0] == 's':
                    BD_next = BD_it.next()
                elif rep[0] == 'a':
                    scan_allBR = True
                elif rep[0] == 'q':
                    sys.exit(2)
        baud_rate = BD_next
        BD_next = None
    print "\nBaud rates found with replying servos: ", found_baud_rates
    if found_baud_rates:
        if len(found_baud_rates) == 1:
            net, myActuators = discover(portName, found_baud_rates[0],
                                        max([d.id for d in myActuators]))
        else:
            print "various baud rates. Exiting"
            sys.exit(0)
    return net, myActuators


def main(portName, highestServoId, baudRate, 
         newStatusReturnLevel, newBaudRate, newServoId,
         with_infos=False, rand_range=None):
    if newBaudRate and newBaudRate not in BAUD_RATES:
        print "{} isn't a standard baud rate {}".format(newBaudRate, BAUD_RATES)
        sys.exit(1)

    #TDL iterate pings of a specific ID over all baud rates, then next ID.
    try:
        BD_i = BAUD_RATES.index(baudRate)
    except ValueError:
        if baudRate >= MIN_BAUD_RATE:
            ordered_bd = [ bd for bd in ALL_BAUD_RATES if bd >= baudRate ]
        else:
            ## scan with all BRs (not possible with USB2AX)
            ordered_bd = ALL_BAUD_RATES
        nbr_tries = len(ordered_bd)*(highestServoId-1)
        print "Will scan %i IDs with %i baud rates %i tries (@%.2fs/try)" % (
            highestServoId, len(ordered_bd), nbr_tries, SERIAL_TIMEOUT)
        print "Will finish around %s" % time.ctime(time.time() +
                                                  nbr_tries * SERIAL_TIMEOUT)
    else:
        ## Requested a standard baud rate, that might fail..
        ordered_bd = BAUD_RATES[:]
        ordered_bd[0] = ordered_bd[BD_i]
        ordered_bd[BD_i] = BAUD_RATES[0]
    net, myActuators = discover_loop(portName, ordered_bd, highestServoId)

    ## Summary
    for actuator in myActuators:
        ## critical settings 1st...
        if newBaudRate != None:                        ## set servo's baud rate
            print "-*-*- setting #%i baud rate @%ibps" % (actuator.id,
                                                          newBaudRate)
            actuator.baud_rate = newBaudRate
        if newStatusReturnLevel != None:
            set_SRL(newStatusReturnLevel)
        if newServoId != None:
            print "-*-*- setting #%i to #%i and quitting." % (actuator.id,
                                                              newServoId)
            actuator.id = newServoId
            print "done"
            return
        if with_infos:
            show_infos(net, actuator)
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
    try:
        # Randomly vary servo position within a small range
        print "ID\tPosition"
        while True:
            if rand_range:
                for actuator in myActuators:
                    actuator.goal_position = random.randrange(*rand_range)
                net.synchronize()
            for actuator in myActuators:
                actuator.read_all()
                time.sleep(0.01)
            for actuator in myActuators:
                print "#%i" % actuator._id, "\t", actuator.current_position
            time.sleep(2)
    except KeyboardInterrupt:
        return


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
    
    parser = optparse.OptionParser("%s [options] [serial_comm]" % sys.argv[0])
    parser.add_option("-c", "--clean", dest="clean", action="store_true",
                      default=False, help="Ignore the settings.yaml file if it "
                      "exists and prompt for new settings.")
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
    parser.add_option("-I", "--set-ID", dest="newID", type="int", default=None,
                      help="Set servo's ID. Works if a single servo is found.")
    parser.add_option("-R", "--set-SRL", dest="newSRL", type="choice",
                      choices=('0','1','2'), default=None,
                      help="Set servos' Status Return Level (0, 1 or 2).")
    parser.add_option("-r", "--rand-values", dest="rand", type="int", nargs=2,
                      default=False, help="send random values in set range.")
    
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

    if options.rand:
        options.rand = (validateInput(options.rand[0], 0, 1023),
                        validateInput(options.rand[1], 0, 1023) )
        if options.rand[0] > options.rand[1]:
            options.rand = sorted(options.rand)

    main(len(args) and args[0] or settings['port'],
         settings['highestServoId'], 
         settings['baudRate'] if options.BR is None else int(options.BR),
         options.newSRL, options.newBR, options.newID, options.infos,
         options.rand )
