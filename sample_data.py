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
MYLAT = 1000.0
MYLNG = 1000.0
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



if MYLAT == 1000.0 or MYLNG == 1000.0 or STRTZ == "":
    print("ENV Values not found please check your env.list file to ensure valid values exist for MYLAT, MYLNG, and STRTZ")
    sys.exit(1)
print("==================")
print("Starting with values:")
print("MYLAT: %s" % MYLAT)
print("MYLNG: %s" % MYLNG)
print("STRTZ: %s" % STRTZ)
print("=================")
print("")

# Get I2C bus
busloc = 0x68 # Default for the MPU-6000 - Shouldn't need to change this. 
bus = smbus.SMBus(1)
myhostname = socket.gethostname()

def main ():
    global bus
    global busloc
    initsensor(bus, busloc)
    timezone = pytz.timezone(STRTZ)

    # Open File
    curtime = datetime.datetime.now()
    curday = curtime.strftime("%Y-%m-%d")
    mystrtime = curtime.strftime("%Y-%m-%d %H:%M:%S")
    fileday = curday
    myfile = "./solardata_%s_%s.json" % (myhostname, fileday)
    fh = open(myfile, "a")

    while True:
        # Setup time vars
        curtime = datetime.datetime.now()
        curday = curtime.strftime("%Y-%m-%d")
        mystrtime = curtime.strftime("%Y-%m-%d %H:%M:%S")
        epochtime = int(time.time())
        mydate = timezone.localize(curtime)

        # Get Readings
        curalt, curaz = get_alt_az(mydate)
        xa, ya, za = getreading(bus, "accel", busloc)
        xg, yg, zg = getreading(bus, "gyro", busloc)

        # Check to see if day changed so we can change the file
        if curday != fileday:
            fh.close()
            fileday = curday
            myfile = "./solardata_%s_%s.json" % (myhostname, fileday)
            fh = open(myfile, "a")

        myrec = OrderedDict()
        myrec["ts"] = mystrtime
        myrec["epochts"] = epochtime
        myrec["array"] = myhostname
        myrec["accel_x"] = xa
        myrec["accel_y"] = ya
        myrec["accel_z"] = za
        myrec["gyro_x"] = xg
        myrec["gyro_y"] = yg
        myrec["gyro_z"] = zg
        myrec["alt"] = curalt
        myrec["az"] = curaz

        fh.write(json.dumps(myrec) + "\n")
        fh.flush()
        time.sleep(5)

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


def get_alt_az(dt):
    alt = solar.get_altitude(MYLAT, MYLNG, dt)
    az = solar.get_azimuth(MYLAT, MYLNG, dt)
    return alt, az

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
