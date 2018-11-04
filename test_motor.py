#!/usr/bin/python3
import time
import sys
from dual_g2_hpmd_rpi import motors, MAX_SPEED

#480 is Positive 100% voltage
#-480 is Negative 100% voltage
#240 is Positive 50% voltage
#-240 is Negative 50% voltage

#0 is Stop


def main():
    motors.enable()
    motors.setSpeeds(0, 0)

    inp = ""
    while inp != "q":
        try:
            inp = input("f, b, s, or q: ")
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
        else:
            print("nope")

if __name__ == '__main__':
    main()

