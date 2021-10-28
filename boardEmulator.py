import serial #install modules serial and pyserial
import time, math, sys
from ltc2986 import *

conn = serial.Serial("COM2", BAUDRATE, timeout = 1)


cmdArrIndex = 0
cmdArr = []

def getCmd():
	cmdIndex = 0
	cmd = ""
	
	while 1:
		byte = conn.read(1)

		if byte:
			decoded = byte.decode('ascii')
			if decoded == 'x' or decoded == 'X':
				return decoded
			cmdIndex += 1
			cmd = cmd+decoded
			if cmdIndex == 3:
				return cmd

def toBytes(value):
	if value > 0:
		frac, whole = math.modf(value)
		frac = format(int(frac * 2**10), "010b")
		whole = format(int(whole), "014b")
			
		value = int(whole+frac, 2)
		print(whole+frac)
		
		val1 = (value  & 0xff0000 ) >> 16
		val2 = (value  & 0xff00 ) >> 8
		val3 = value & 0xff
		
		return [0x01, val1, val2, val3]

tempVal = 20.999

while 1:
	#receive setup
	for i in range(0, 6):
		getCmd()
		
	#receive data ready request	
	for i in range(0, 5):
		getCmd()
	time.sleep(0.1)
	
	conn.write(b'FF')
	getCmd()
	
	#send data 5x times	
	for i in range(0, 5):
		data = toBytes(tempVal)
		for i in range(0, 8):
			getCmd()
		time.sleep(0.2)
		for b in data:
			conn.write(binToASCII(b))
		getCmd()
		time.sleep(0.2)
	
	tempVal -= 1
	time.sleep(1)
			