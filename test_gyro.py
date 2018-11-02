#!/usr/bin/python3

# Distributed with a free-will license.
# Use it any way you want, profit or free, provided it fits in the licenses of its associated works.
# MPU-6000
# This code is designed to work with the MPU-6000_I2CS I2C Mini Module available from ControlEverything.com.
# https://www.controleverything.com/content/Accelorometer?sku=MPU-6000_I2CS#tabs-0-product_tabset-2

import smbus
import time

# Get I2C bus
busloc = 0x68 # Default for the MPU-6000 - Shouldn't need to change this. 
bus = smbus.SMBus(1)


def main ():
    global bus
    global busloc
    initsensor(bus, busloc)

    while True:
        xa, ya, za = getreading(bus, "accel", busloc)
        xg, yg, zg = getreading(bus, "gyro", busloc)
        print("------------------------------------------------------")
        print("Acceleration in X-Axis : %d" % xa)
        print("Acceleration in Y-Axis : %d" % ya)
        print("Acceleration in Z-Axis : %d" % za)
        print("X-Axis of Rotation : %d" % xg)
        print("Y-Axis of Rotation : %d" % yg)
        print("Z-Axis of Rotation : %d" % zg)
        print("")
        time.sleep(1)

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
