#!/usr/bin/python3

from pysolar import solar
import time
import datetime
import pytz

MYLAT = 44.6870417
MYLNG = -89.268059
strtz = "America/Chicago"






def main():

    timezone = pytz.timezone(strtz)

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
