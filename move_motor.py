#!/usr/bin/python3
import json
import datetime
import smbus
import socket
import time
from collections import OrderedDict
from pysolar import solar
import pytz
import os.path
import sys
from dual_g2_hpmd_rpi import motors, MAX_SPEED

#480 is Positive 100% voltage
#-480 is Negative 100% voltage
#240 is Positive 50% voltage
#-240 is Negative 50% voltage

#0 is Stop

MYLAT = 1000.0
MYLNG = 1000.0
EAST_POS=0.0
WEST_POS=0.0
EAST_ANGLE=0.0
WEST_ANGLE=0.0
STRTZ = ""

ENV_FILE = "env.list"

if not os.path.isfile(ENV_FILE):
    print("ENV_FILE at %s not found - exiting")
    sys.exit(1)

e = open(ENV_FILE, "r")

lines = e.read()
e.close()
for line in lines.split("\n"):
    myline = line.strip()
    if myline.find("#") == 0:
        pass
    elif myline != "":
        arline = myline.split("=")
        if arline[0] == "MYLAT":
            MYLAT = float(arline[1])
        if arline[0] == "MYLNG":
            MYLNG = float(arline[1])
        if arline[0] == "STRTZ":
            STRTZ = arline[1]
        if arline[0] == "WEST_ANGLE":
            WEST_ANGLE = float(arline[1])
        if arline[0] == "EAST_ANGLE":
            EAST_ANGLE = float(arline[1])
        if arline[0] == "WEST_POS":
            WEST_POS = float(arline[1])
        if arline[0] == "EAST_POS":
            EAST_POS = float(arline[1])


ECONV = EAST_POS / EAST_ANGLE
WCONV = WEST_POS / WEST_ANGLE

if MYLAT == 1000.0 or MYLNG == 1000.0 or STRTZ == "" or EAST_ANGLE == 0.0 or WEST_ANGLE == 0.0 or WEST_POS == 0.0 or EAST_POS == 0.0:
    print("ENV Values not found please check your env.list file to ensure valid values exist for MYLAT, MYLNG, and STRTZ")
    sys.exit(1)
print("==================")
print("Starting with values:")
print("MYLAT: %s" % MYLAT)
print("MYLNG: %s" % MYLNG)
print("STRTZ: %s" % STRTZ)
print("EAST_ANGLE: %s" % EAST_ANGLE)
print("WEST_ANGLE: %s" % WEST_ANGLE)
print("EAST_POS: %s" % EAST_POS)
print("WEST_POS: %s" % WEST_POS)
print("ECONV: %s" % ECONV)
print("WCONV: %s" % WCONV)
print("=================")
print("")

# Get I2C bus
busloc = 0x68 # Default for the MPU-6000 - Shouldn't need to change this. 
bus = smbus.SMBus(1)
myhostname = socket.gethostname()


def main():
    global bus
    global busloc

    initsensor(bus, busloc)
    timezone = pytz.timezone(STRTZ)
    motors.enable()
    motors.setSpeeds(0, 0)

    inp = ""
    while inp != "q":
        cur_pos = mydeg(get_pos())
        try:
            inp = input("Current Angle: %s - a, f, b, s, or q: " % cur_pos)
        except:
            print("\nNo fun exiting")
            motors.setSpeeds(0, 0)
            motors.disable()
            sys.exit(0)

        if inp == "f": 
            motors.motor1.setSpeed(-480)
        elif inp == "b":
            motors.motor1.setSpeed(480)
        elif inp == "s":
            motors.motor1.setSpeed(0)
        elif inp == "q":
            motors.setSpeeds(0, 0)
            motors.disable()
            sys.exit(0)
        elif inp == "a":
            print("Oh cool, you want to set an angle! Type it here, oh, use whole numbers for now")
            print("")
            myangle = input("Set a whole number angle between %s (East) and %s (West): " % (EAST_ANGLE, WEST_ANGLE))
            if 1 == 1:
                ang = int(myangle)
                print("Using %s as your angle (you entered %s, we int() it)" % (ang, myangle))
                print("Setting Now")
                goto_angle(ang)
                print("Set complete")
                print("")
            else:
                print("We couldn't int your angle, ignoring you for now")
                continue
        else:
            print("nope")

def goto_angle(setangle):
    global ECONV
    global WCONV
    global motors
    CONV = 0.0
    if setangle < 0:
        CONV = WCONV
    elif setangle > 0:
        CONV = ECONV
    TARGET_POS = CONV * setangle
    # Get Current Location
    curcnt = 0
    cursum = 0.0
    failcnt = 0
    for x in range(10):
        try:
            xa, ya, za = getreading(bus, "accel", busloc)
            curcnt += 1
            cursum += xa
        except:
            failcnt += 1
            if failcnt > 20:
                break
                print("Reading Fail!!")
            else:
                continue
    CURRENT_POS = get_pos()
    print("The current location is %s and you want to go to %s (%s in angle form)" % (CURRENT_POS, TARGET_POS, setangle))
    finished = False

    if CURRENT_POS > TARGET_POS:
        # We want to move west
        motor_dir = -480
    elif CURRENT_POS < TARGET_POS:
        motor_dir = 480
    else:
        motor_dir = 0
        finished = True
        print("No change!")
    motors.motor1.setSpeed(motor_dir)
    while finished == False:
        if motor_dir < 0:
            NEW_POS = get_pos()
            if NEW_POS <= TARGET_POS:
                motors.motor1.setSpeed(0)
                finished = True
        elif motor_dir > 0:
            NEW_POS = get_pos()
            if NEW_POS >= TARGET_POS:
                motors.motor1.setSpeed(0)
                finished = True
#motors.motor1.setSpeed(-480)
def mydeg(pos):
    retval = 0
    if pos > 0:
        retval = pos / ECONV
    elif pos < 0:
        retval = pos / WCONV
    return retval

def get_pos():
    global bus
    global busloc
    curcnt = 0
    cursum = 0.0
    failcnt = 0
    for x in range(5):
        try:
            xa, ya, za = getreading(bus, "accel", busloc)
            curcnt += 1
            cursum += xa
        except:
            failcnt += 1
            if failcnt > 20:
                break
                print("Reading Fail!!")
            else:
                continue
    return cursum / curcnt

def initsensor(bus, busloc):
    # Initialize things:

    # Select gyroscope configuration register, 0x1B(27)
    #       0x18(24)    Full scale range = 2000 dps
    bus.write_byte_data(busloc, 0x1B, 0x18)
    # MPU-6000 address, 0x68(104)
    # Select accelerometer configuration register, 0x1C(28)
    #       0x18(24)    Full scale range = +/-16g
    bus.write_byte_data(busloc, 0x1C, 0x18)
    # MPU-6000 address, 0x68(104)
    # Select power management register1, 0x6B(107)
    #       0x01(01)    PLL with xGyro referenc
    bus.write_byte_data(busloc, 0x6B, 0x01)
    #
    time.sleep(0.8)

def getreading(bus, src, busloc):
# src is accel or gyro

    if src == "accel":
        srcval = 0x3B
    elif src == "gyro":
        srcval = 0x43
    else:
        srcval = 0x00
        print("Invalid src")
        return (0,0,0)
    data = bus.read_i2c_block_data(busloc, srcval, 6)
    x = convertreading(data[0], data[1])
    y = convertreading(data[2], data[3])
    z = convertreading(data[4], data[5])
    return x, y, z

def convertreading(val1, val2):
    retval = val1 * 256 + val2
    if retval > 32767:
        retval -= 65536
    return retval

if __name__ == '__main__':
    main()

