#!/usr/bin/python3

from pysolar import solar
import time
import datetime
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






def main():

    timezone = pytz.timezone(STRTZ)

    #date = datetime.datetime(2018, 10, 22, 13, 20, 10, 130320)


    while True:
        date = datetime.datetime.now()
        mydate = timezone.localize(date)
        mystrtime = mydate.strftime("%Y-%m-%d %H:%M:%S")

        curalt, curaz = get_alt_az(mydate)


        print("%s - Alt: %s - Az: %s" % (mystrtime, curalt, curaz))

        time.sleep(10)

def get_alt_az(dt):
    alt = solar.get_altitude(MYLAT, MYLNG, dt)
    az = solar.get_azimuth(MYLAT, MYLNG, dt)
    return alt, az



if __name__ == '__main__':
    main()
