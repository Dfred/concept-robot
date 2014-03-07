import os
import time
import random
import sys
import subprocess
import optparse
import yaml

try:
    import dynamixel
except ImportError as e:
    print "dynamixel for python could not be imported. try with easy-install or pip"
    sys.exit(4)

"""
EXAMPLE
 
Move all attached servos randomly every 2 seconds and read back the position
they end up in.
"""

ACCEPTABLE_RATES = [ int(br[5:]) for br in sorted(dynamixel.BAUD_RATE.keys()) ]

def main(settings):

    portName = settings['port']
    baudRate = settings['baudRate']
    highestServoId = settings['highestServoId']

    if baudRate not in ACCEPTABLE_RATES:
        print "non-standard baud rate %s" % baudRate
        sys.exit(1)
    i = ACCEPTABLE_RATES.index(baudRate)
    scan_allBR = False
    while i < len(ACCEPTABLE_RATES):
        baudRate = ACCEPTABLE_RATES[i]
        # Establish a serial connection to the dynamixel network.
        # This usually requires a USB2Dynamixel
        try:
            serial = dynamixel.SerialStream(port=portName,
                                            baudrate=baudRate,
                                            timeout=1)
        except ValueError as e:
            print e
            i += 1
            continue
        net = dynamixel.DynamixelNetwork(serial)
    
        # Ping the range of servos that are attached
        print "Scanning for Dynamixels @%i bps... " % baudRate,
        sys.stdout.flush()
        try:
            net.scan(1, highestServoId)
        except KeyboardInterrupt:
            sys.exit(2)

        myActuators = []
    
        for dyn in net.get_dynamixels():
            print "found #%i !!!" % dyn.id
            myActuators.append(net[dyn.id])
        if myActuators:
            break       #XXX: keep on scanning for others?

        print 'No Dynamixels Found!'
        if i == len(ACCEPTABLE_RATES)-1:
            print "No further baud rate to check. Bailing out."
            sys.exit(3)
        if scan_allBR:
            i += 1
            continue
        rep = None
        try:
            rep = raw_input("scan with %i baud rate? [Y/n/skip/all]"%
                            ACCEPTABLE_RATES[i+1])
            rep = rep and rep[0].lower()
        finally:
            if not rep or rep == 'n':
                print "user abort."
                sys.exit(2)
            elif rep == 's':
                i += 1
            elif rep == 'a':
                scan_allBR = True
            i += 1
    
    for actuator in myActuators:
        actuator.moving_speed = 50
        actuator.synchronized = True
        actuator.torque_enable = True
        actuator.torque_limit = 800
        actuator.max_torque = 800
    
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
            print actuator._id, "\t", actuator.current_position
        time.sleep(1)

def validateInput(userInput, rangeMin, rangeMax):
    '''
    Returns valid user input or None
    '''
    try:
        inTest = int(userInput)
        if inTest < rangeMin or inTest > rangeMax:
            print "ERROR: Value out of range [" + str(rangeMin) + '-' + str(rangeMax) + "]"
            return None
    except ValueError:
        print("ERROR: Please enter an integer")
        return None
    
    return inTest

if __name__ == '__main__':
    
    parser = optparse.OptionParser()
    parser.add_option("-c", "--clean",
                      action="store_true", dest="clean", default=False,
                      help="Ignore the settings.yaml file if it exists and \
                      prompt for new settings.")
    
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
            portPrompt = "Which port corresponds to your USB2Dynamixel? \n"
            # Get a list of ports that mention USB
            try:
                possiblePorts = subprocess.check_output('cd /dev && ls ttyACM*',
                                                        shell=True).split()
                possiblePorts = ['/dev/' + port for port in possiblePorts]
            except subprocess.CalledProcessError:
                sys.exit("USB2Dynamixel not found. Please connect one.")
                
            counter = 1
            portCount = len(possiblePorts)
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
            portPrompt = "Please enter the port name to which the USB2Dynamixel is connected: "
            portChoice = raw_input(portPrompt)
    
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
            hsiTest = raw_input("Please enter the highest ID of the connected servos: ")
            highestServoId = validateInput(hsiTest, 1, 255)
        
        settings['highestServoId'] = highestServoId
        
        # Save the output settings to a yaml file
        with open(settingsFile, 'w') as fh:
            yaml.dump(settings, fh)
            print("Your settings have been saved to 'settings.yaml'. \nTo " +
                   "change them in the future either edit that file or run " +
                   "this example with -c.")
    
    main(settings)
