#!/usr/bin/python3
import time
from dual_g2_hpmd_rpi import motors, MAX_SPEED

#480 is Positive 100% voltage
#-480 is Negative 100% voltage
#240 is Positive 50% voltage
#-240 is Negative 50% voltage

#0 is Stop


def main():
    motors.enable()
    motors.setSpeeds(0, 0)
    
    print("Setting Motor 1 to +480")
    motors.motor1.setSpeed(480)
    time.sleep(10)
    print("Stopping Motor")
    motors.motor1.setSpeed(0)
    time.sleep(10)
    print("seeting Motor 1 to -480")
    motors.motor1.setSpeed(-480)
    time.sleep(10)
    print("Stopping Motor")
    print("Running end to disable")
    motors.setSpeeds(0, 0)
    motors.disable()
    print("Motors Disabled")
    

if __name__ == '__main__':
    main()

