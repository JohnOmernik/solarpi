# install SMB Bus library




sudo apt-get install python3 python3-pip python3-dev python3-numpy
sudo pip3 install smbus-cffi==0.5.1 wiringpi
sudo pip3 install pysolar pytz


git clone https://github.com/pololu/dual-g2-high-power-motor-driver-rpi && cd dual-g2-high-power-motor-driver-rpi && sudo python3 setup.py install
