#!/usr/bin/python3
import json
import datetime
import smbus
import socket
import math
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
axis_azi = 0.0
axis_tilt = 0.0
MOVE_INTERVAL=600
NIGHT_POS=0.0
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
        if arline[0] == "AXIS_AZI":
            axis_azi = float(arline[1])
        if arline[0] == "AXIS_TILT":
            axis_tilt = float(arline[1])
        if arline[0] == "MOVE_INTERVAL":
            MOVE_INTERVAL = int(arline[1])

INVERT_SENSOR = True # We installed our sensor apparently "upside down" therefore we need to invert the reading to align with the solar function

ECONV = EAST_POS / EAST_ANGLE
WCONV = WEST_POS / WEST_ANGLE

if MYLAT == 1000.0 or MYLNG == 1000.0 or STRTZ == "" or EAST_ANGLE == 0.0 or WEST_ANGLE == 0.0 or WEST_POS == 0.0 or EAST_POS == 0.0 or axis_azi == 0.0 or axis_tilt == 0.0:
    print("ENV Values not found please check your env.list file to ensure valid values exist for EAST and WEST_POS, EAST and WEST_ANGLE, AXIS_AZI, AXIS_TILE, MYLAT, MYLNG, and STRTZ")
    sys.exit(1)
print("==================")
print("Starting with values:")
print("MYLAT: %s" % MYLAT)
print("MYLNG: %s" % MYLNG)
print("STRTZ: %s" % STRTZ)
print("AXIS_AZI: %s" % axis_azi)
print("AXIS_TILT: %s" % axis_tilt)
print("EAST_ANGLE: %s" % EAST_ANGLE)
print("WEST_ANGLE: %s" % WEST_ANGLE)
print("EAST_POS: %s" % EAST_POS)
print("WEST_POS: %s" % WEST_POS)
print("ECONV: %s" % ECONV)
print("WCONV: %s" % WCONV)
print("MOVE_INTERVAL: %s" % MOVE_INTERVAL)
print("INVERT_SENSOR: %s" % INVERT_SENSOR)
print("=================")
print("")

# Get I2C bus
busloc = 0x68 # Default for the MPU-6000 - Shouldn't need to change this. 
bus = smbus.SMBus(1)
myhostname = socket.gethostname()


def main():
    global bus
    global busloc
    global axis_tilt
    global axis_azi
    initsensor(bus, busloc)
    timezone = pytz.timezone(STRTZ)
    motors.enable()
    motors.setSpeeds(0, 0)
    RUNNING = True
    last_set_val = 0
    last_set_time = 0
    while RUNNING:
        curtime = datetime.datetime.now()
        curday = curtime.strftime("%Y-%m-%d")
        mystrtime = curtime.strftime("%Y-%m-%d %H:%M:%S")
        epochtime = int(time.time())
        mydate = timezone.localize(curtime)
        curalt, curaz = get_alt_az(mydate)
        cur_r = mydeg(get_pos())
        track_err = False
        if curalt > 0:
            # We only check if there is a track error if the sun is up, no point in correcting all night long
            if math.fabs(math.fabs(cur_r) - math.fabs(last_set_val)) > 2.0:
                print("%s - Track error, going to set track_err to true: cur_r: %s - last_set_val: %s" % (mystrtime, cur_r, last_set_val))
                track_err = True
            sun_r = getR(curalt, curaz, axis_tilt, axis_azi)
            if INVERT_SENSOR:
                sun_r = -sun_r
            print("%s - Sun is up! -  Sun Alt: %s - Sun Azi: %s - Cur Rot: %s - Potential Sun Rot: %s" % (mystrtime, curalt, curaz, cur_r, sun_r))
            NEW_SET_VAL = None
            if sun_r <= EAST_ANGLE and sun_r >= WEST_ANGLE:
                print("%s - Potential new val: %s - cur: %s" % (mystrtime, sun_r, cur_r))
                NEW_SET_VAL = sun_r
            elif sun_r > EAST_ANGLE and (last_set_val != EAST_ANGLE or track_err == True):
                print("%s - Sun Rot (%s) is Beyond East(%s), and array needs to move there" % (mystrtime, sun_r, EAST_ANGLE))
                NEW_SET_VAL = EAST_ANGLE
            elif sun_r < WEST_ANGLE and (last_set_val != WEST_ANGLE or track_err == True):
                print("%s - Sun Rot (%s) is Beyond West(%s), and array needs to move there" % (mystrtime, sun_r, WEST_ANGLE))
                NEW_SET_VAL = WEST_ANGLE
            if epochtime - last_set_time >= MOVE_INTERVAL and NEW_SET_VAL is not None:
                print("%s Setting New val: %s from %s" % (mystrtime, NEW_SET_VAL, cur_r))
                last_set_time = epochtime
                last_set_val = NEW_SET_VAL
                goto_angle(NEW_SET_VAL)
        else:
            if last_set_val != NIGHT_POS:
                print("%s - Sun is down setting to %s for the night" % (mystrtime, NIGHT_POS))
                goto_angle(NIGHT_POS)
                last_set_val = NIGHT_POS
                last_set_time = epochtime
        time.sleep(60)

def getR(sun_alt, sun_azi, axis_tilt, axis_azi):
    # Return in Degrees
    sun_zen = 90 - sun_alt
    x_1 = (math.sin(math.radians(sun_zen)) * math.sin(math.radians(sun_azi) - math.radians(axis_azi)))
    x_2 = (math.sin(math.radians(sun_zen)) * math.cos(math.radians(sun_azi) - math.radians(axis_azi)) * math.sin(math.radians(axis_tilt)))
    x_3 = (math.cos(math.radians(sun_zen)) * math.cos(math.radians(axis_tilt)))
    x_4 = x_2 + x_3
    X = x_1 / x_4
    if X == 0.0 or (X > 0 and (sun_azi - axis_azi) > 0) or (X < 0 and (sun_azi - axis_azi) < 0):
        mypsi = math.radians(0.0)
    elif X < 0 and (sun_azi - axis_azi) > 0:
        mypsi = math.radians(180.0)
    elif X > 0 and (sun_azi - axis_azi) < 0:
        mypsi = math.radians(-180.0)
    else:
        print("awe crap")
        mypsi = 0
    R = math.atan(X) + mypsi

    return math.degrees(R)

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
    tcnt = 0

    while finished == False:
        tcnt += 1
        NEW_POS = get_pos()
        if motor_dir < 0:
            if NEW_POS <= TARGET_POS:
                motors.motor1.setSpeed(0)
                finished = True
        elif motor_dir > 0:
            if NEW_POS >= TARGET_POS:
                motors.motor1.setSpeed(0)
                finished = True
        elif tcnt >= 1200:
            print("It has taken over 5 minutes of waiting and we didn't get to where you want, we are giving up at at %s"  % NEW_POS)
            finished = True
        time.sleep(0.5)
    print("Finished setting position")
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

def get_alt_az(dt):
    alt = solar.get_altitude(MYLAT, MYLNG, dt)
    az = solar.get_azimuth(MYLAT, MYLNG, dt)
    return alt, az

if __name__ == '__main__':
    main()

