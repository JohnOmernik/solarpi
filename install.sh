# install SMB Bus library




sudo apt-get install python3 python3-pip python3-dev
sudo pip3 install smbus-cffi==0.5.1
sudo pip3 install pysolar
sudo pip3 install  wiringpi


git clone https://github.com/pololu/dual-g2-high-power-motor-driver-rpi
cd dual-g2-high-power-motor-driver-rpi
sudo python setup.py install
