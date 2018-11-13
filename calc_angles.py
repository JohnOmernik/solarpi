#!/usr/bin/python3

from pysolar import solar
import time
import datetime
import pytz
import os.path
from collections import OrderedDict
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

    date = datetime.datetime.now()
    mydate = timezone.localize(date)
    getstartstopaz(mydate, 20.0)

    date = datetime.datetime(2018, 3, 20, 0, 0, 0, 0)
    mydate = timezone.localize(date)
    getstartstopaz(mydate, 20.0)

    date = datetime.datetime(2018, 6, 20, 0, 0, 0, 0)
    mydate = timezone.localize(date)
    getstartstopaz(mydate, 20.0)

    date = datetime.datetime(2018, 9, 20, 0, 0, 0, 0)
    mydate = timezone.localize(date)
    getstartstopaz(mydate, 20.0)

    date = datetime.datetime(2018, 12, 20, 0, 0, 0, 0)
    mydate = timezone.localize(date)
    getstartstopaz(mydate, 20.0)

#    mystrtime = mydate.strftime("%Y-%m-%d %H:%M:%S")
#    mystrdate = mydate.strftime("%Y-%m-%d")


def getstartstopaz(dt, thresval):
    mydict = OrderedDict()
    print("Loading Daily Table")
    for x in range(1439):
        myx = x + 1 
        myhr = myx // 60
        mymin = myx % 60
        dval = datetime.datetime(dt.year, dt.month, dt.day, myhr, mymin, 0, 0, dt.tzinfo)
        myalt, myaz = get_alt_az(dval)
        mydict[str(dval)] = [myalt, myaz - 180]
    print("Table load complete")
    print("")
    startval = 0.0
    endval = 0.0
    starttime = None
    endtime = None
    for x in mydict:
#        print("%s - %s" % (x, mydict[x]))
        if mydict[x][0] >= thresval and startval == 0.0 and mydict[x][1] < 0 and mydict[x][0] >= 0:
            startval = mydict[x][1]
            starttime = x
            print("Found startval and time: %s - %s " % (startval, starttime))
        elif mydict[x][0] <= thresval and endval == 0.0 and mydict[x][1] > 0 and mydict[x][0] >= 0:
            endval = mydict[x][1]
            endtime = x
            print("Found endval and time: %s - %s" % (endval, endtime))
        if starttime is not None and endtime is not None:
            print("Both found - exiting")
            break
    print("")
    print("On %s we start moving at %s at %s  and end moving at %s at %s" % (dt, startval, starttime, endval, endtime))
    print("")
        
#        print("%s - %s:%s" % (dval, myalt, myaz))
    
    

    #date = datetime.datetime(2018, 10, 22, 13, 20, 10, 130320)


#    while True:
#        date = datetime.datetime.now()
#        mydate = timezone.localize(date)
#        mystrtime = mydate.strftime("%Y-%m-%d %H:%M:%S")#

#        curalt, curaz = get_alt_az(mydate)


 #       print("%s - Alt: %s - Az: %s" % (mystrtime, curalt, curaz))

 #       time.sleep(10)

def get_alt_az(dt):
    alt = solar.get_altitude(MYLAT, MYLNG, dt)
    az = solar.get_azimuth(MYLAT, MYLNG, dt)
    return alt, az



if __name__ == '__main__':
    main()
