import time
import sys
import glob
from datetime import datetime
import textwrap
import math
import sys
import os

import serial #install modules serial and pyserial

DFAULT_LOG_NAME = "test.csv"

BAUDRATE = 115200

# specify number of max channels of datalogger
CH_COUNT = 10

senseResMapping = {
	"Sense R @ CH2-CH1":	2, 
	"Sense R @ CH3-CH2":	3, 
	"Sense R @ CH4-CH3":	4, 
	"Sense R @ CH5-CH4":	5, 
	"Sense R @ CH6-CH5":	6, 
	"Sense R @ CH7-CH6":	7, 
	"Sense R @ CH8-CH7":	8, 
	"Sense R @ CH9-CH8":	9, 
	"Sense R @ CH10-CH9":	10
}

wireMapping = {
	"2-wire":					0, 
	"3-wire":					1, 
	"4-wire":					2, 
	"4-wire, Kelvin Rsense":	3
}

excitationMapping = {
	"No rotation/no sharing":	0,
	"No rotation/sharing":		1,
	"Rotation/sharing":			2
}

excitationCurrentMapping = {
	"external":					0,
	"5uA":						1,
	"10uA":						2,
	"25uA":						3,
	"50uA":						4,
	"100uA":					5,
	"250uA":					6,
	"500uA":					7,
	"1mA":						8
}

rtdCurveMapping = {
	"European":					0, 
	"American":					1, 
	"Japanese":					2, 
	"ITS-90":					3
}

diffMapping = {
	"Diff":						0,
	"Single":					1
}

numReadingsMapping = {
	"2 readings":				0,
	"3 readings":				1
}

averagingMapping = {
	"AVG off":					0,
	"AVG on":					1
}

diodeCurrentMapping = {
	"10uA/40uA/80uA":			0, 
	"20uA/80uA/160uA":			1,
	"40uA/160uA/320uA":			2,
	"80uA/320uA/640uA":			3
}

CMD_STAT_REG = 0x000
MUL_CONV_MASK_REG = [0x0f6, 0x0f7]

START = (1 << 7)
DONE = (1 << 6)

SPI_WRITE = b"02"
SPI_READ = b"03"

channelSelectionBits = {
	"CH1":	(1 << 0),
	"CH2":	(1 << 1),
	"CH3":	(1 << 2),
	"CH4":	(1 << 3),
	"CH5":	(1 << 4),
	"CH6":	(1 << 5),
	"CH7":	(1 << 6),
	"CH8":	(1 << 7),
	"CH9":	(1 << 0),
	"CH10":	(1 << 1)
}

channelAssigmentAddr = {
	"CH1":	0x200,
	"CH2":	0x204,
	"CH3":	0x208,
	"CH4":	0x20C,
	"CH5":	0x210,
	"CH6":	0x214,
	"CH7":	0x218,
	"CH8":	0x21C,
	"CH9":	0x220,
	"CH10":	0x224
}

channelDataAddr = {
	"CH1":	0x010,
	"CH2":	0x014,
	"CH3":	0x018,
	"CH4":	0x01C,
	"CH5":	0x020,
	"CH6":	0x024,
	"CH7":	0x028,
	"CH8":	0x02C,
	"CH9":	0x030,
	"CH10":	0x034
}

channelMapping = {
	"multiple":	0,
	"CH1":		1,
	"CH2":		2,
	"CH3":		3,
	"CH4":		4,
	"CH5":		5,
	"CH6":		6,
	"CH7":		7,
	"CH8":		8,
	"CH9":		9,
	"CH10":		10,
	"sleep": 	0b10111
}

channelNumbering = {
	0:			"CH1",
	1:			"CH2",
	2:			"CH3",
	3:			"CH4",
	4:			"CH5",
	5:			"CH6",
	6:			"CH7",
	7:			"CH8",
	8:			"CH9",
	9:			"CH10"
}

sensorTypesBits = {
	"Unassigned": 											(0 << 3),
	"Type J Thermocouple":									(1 << 3),
	"Type K Thermocouple":									(2 << 3),
	"Type E Thermocouple":									(3 << 3),
	"Type N Thermocouple":									(4 << 3),
	"Type R Thermocouple":									(5 << 3),
	"Type S Thermocouple":									(6 << 3),
	"Type T Thermocouple":									(7 << 3),
	"Type B Thermocouple":									(8 << 3),
	"Custom Thermocouple":									(9 << 3),
	"RTD PT-10":											(10 << 3),
	"RTD PT-50":											(11 << 3),
	"RTD PT-100":											(12 << 3),
	"RTD PT-200":											(13 << 3),
	"RTD PT-500":											(14 << 3),
	"RTD PT-1000":											(15 << 3),
	"RTD 1000 (0.00375)":									(16 << 3),
	"RTD NI-120":											(17 << 3),
	"RTD Custom":											(18 << 3),
	"Thermistor 44004/44033 2.252k at 25 C":				(19 << 3),
	"Thermistor 44005/44030 3k at 25 C":					(20 << 3),
	"Thermistor 44007/44034 5k at 25 C":					(21 << 3),
	"Thermistor 44006/44031 10k at 25 C":					(22 << 3),
	"Thermistor 44008/44032 30k at 25 C":					(23 << 3),
	"Thermistor YSI 400 2.252k at 25 C":					(24 << 3),
	"Thermistor Spectrum 1003k 1k":							(25 << 3),
	"Thermistor Custom Steinhart-Hart":						(26 << 3),
	"Thermistor Custom Table":								(27 << 3),
	"Diode":												(28 << 3),
	"Sense Resistor":										(29 << 3),
	"Direct ADC":											(30 << 3),
	"Analog Temperature Sensor"	:							(31 << 3)
}

errBitMapping = {
	(1 << 0):	"valid",
	(1 << 1):	"ADC out of range",
	(1 << 2):	"Sensor under range",
	(1 << 3):	"Sensor over range",
	(1 << 4):	"CJ soft fault",
	(1 << 5):	"CJ hard fault",
	(1 << 6):	"ADC hard fault",
	(1 << 7):	"Sensor hard fault"
}

"""accepts one byte to convert it to HEX in ASCII representation"""
def binToASCII(byte):
	return ("%0.2X" % byte).encode('ascii')
	
def decToBin(number, fractionBitCount):
	import math
	whole, frac = math.modf(number)

	
def rawToVolatge(raw):
	# get status byte
	statusByte = (raw & 0xff000000) >> 24
	raw = raw & 0x00ffffff

	# get if signed
	if raw & 0x00800000:
		raw = raw - 1
		raw = ~raw
		raw = raw & 0x00ffffff
		result = -(raw / 2**21)
	else:
		result = (raw / 2**21)
			
	return result
	
def logMeasurement(measurString, statusString, raw = [], expName = ""):
	timestamp = datetime.now()
	if expName == "":
		fname = DFAULT_LOG_NAME
	else:
		fname = "csv/%s.csv" % (expName)	
		
	os.makedirs(os.path.dirname(fname), exist_ok=True)
	with open(fname, "a") as f:
		measurString = timestamp.strftime("%Y-%m-%dT%H:%M:%S")+measurString
		f.write(measurString+"\n")
		print(measurString)
		
	fname = fname.replace("csv","telemetry")
	os.makedirs(os.path.dirname(fname), exist_ok=True)
	with open(fname, "a") as f:
		statusString = timestamp.strftime("%Y-%m-%dT%H:%M:%S\t")+statusString
		f.write(statusString+"\n")
		
	if raw != []:
		fname = fname.replace("telemetry", "raw")
		os.makedirs(os.path.dirname(fname), exist_ok=True)
		with open(fname, "a") as f:
			string = timestamp.strftime("%Y-%m-%dT%H:%M:%S\t")+str(raw)
			f.write(string+"\n")
		
def logString(string, expName = "", telemetry = False, printAllow = True):
	timestamp = datetime.now()
	if expName == "":
		fname = DFAULT_LOG_NAME
	else:
		fname = "csv/%s.csv" % (expName)	
	
	if telemetry == False:
		os.makedirs(os.path.dirname(fname), exist_ok=True)
		with open(fname, "a") as f:
			string = timestamp.strftime("%Y-%m-%dT%H:%M:%S")+string
			f.write(string+"\n")
			if printAllow:
				print(string)
	else:
		fname = fname.replace("csv","telemetry")
		os.makedirs(os.path.dirname(fname), exist_ok=True)
		with open(fname, "a") as f:
			string = timestamp.strftime("%Y-%m-%dT%H:%M:%S\t")+string
			f.write(string+"\n")
			if printAllow:
				print(string)

class LTC2986:
	def __init__(self, port = ""):
		self.port = ""
		self.conn = None
		
		if port == "":
			if sys.platform.startswith('win'):
				ports = ['COM%s' % (i + 1) for i in range(20)]
			elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
				# this excludes your current terminal "/dev/tty"
				ports = glob.glob('/dev/tty[A-Za-z]*')
			else:
				raise EnvironmentError('Unsupported platform')
				
			print("Looking for datalogger...")
			for port in ports:
				try:
					conn = serial.Serial(port, BAUDRATE, timeout=3)
					hello = conn.read(6).decode("utf-8")
					if "hello" not in hello:
						conn.close()
						continue
					conn.write(b"I")
					output = conn.read(100).decode("utf-8")
					if "LTC2986" in output:	
						print("Port for datalogger: %s" % (port))
						self.port = port
						self.conn = conn
						break
					else:
						conn.close()
						
				except (OSError, serial.SerialException):
					pass
			
			if self.port == "":
				print("No port candidate")
				
		else:
			print("Connecting directly via %s" % (port))
			self.port = port
			self.conn = serial.Serial(port, BAUDRATE, timeout=2)
			hello = self.conn.read(6).decode("utf-8")
			
	def __enter__(self):
		return self

	def __exit__(self, type, value, traceback):
		try:
			self.conn.close()
		except Exception as e:
			print(e)
			pass
			
	"""set CS low to initiate SPI transfer"""
	def _startCmd(self):
		self.conn.write(b'x')
		
	"""set CS high to initiate SPI transfer"""
	def _endCmd(self):
		self.conn.write(b'X')
			
	def _sendCmd(self, startAddr, byteList, rw = SPI_WRITE, bytesToRead = 4):
		data = ""
		self._startCmd()
		self.conn.write(b'S')
		self.conn.write(rw)
		
		hiByte = int(startAddr / 0x100) 
		loByte = startAddr & 0xff
		
		self.conn.write(b'S')
		self.conn.write(binToASCII(hiByte))
		
		self.conn.write(b'S')
		self.conn.write(binToASCII(loByte))
		
		for byte in byteList:
			self.conn.write(b'S')
			self.conn.write(binToASCII(byte))
			
		if rw == SPI_READ:
			request = "T00"*bytesToRead
			self.conn.write(request.encode('ascii'))
			data = self.conn.read(2*bytesToRead)
			
		self._endCmd()
		return data
		
	def setDirectADC(self, channel):
		bytes = [
			sensorTypesBits["Direct ADC"] | 0b100,
			0,
			0,
			0
		]
		
		self._sendCmd(channelAssigmentAddr[channel], bytes)
	
	
	def setDiode(self, channel, 
				single = 1,
				readCount = 1,
				avgOn = 0,
				excitationCurrent = 0b000,
				ideality = 1.05499):
		
		frac, whole = math.modf(ideality)
		
		frac = format(int(frac * 2**20), "020b")
		whole = format(int(whole), "02b")
		
		ideality = int(whole+frac, 2)
		
		idealityHi = (ideality & 0x3F0000) >> 16
		idealityMid = (ideality & 0x00ff00) >> 8
		idealityLo = (ideality & 0xff)
		
		bytes = [
			sensorTypesBits["Diode"] | (single << 2) | (readCount << 1) | avgOn,
			excitationCurrent << 6 | idealityHi,
			idealityMid,
			idealityLo
		]
				
		self._sendCmd(channelAssigmentAddr[channel], bytes)
		
	def setResitor(self, channel, resistance):
		frac, whole = math.modf(resistance)
		frac = format(int(frac * 2**10), "010b")
		whole = format(int(whole), "017b")
			
		resistance = int(whole+frac, 2)
		
		res1 = (resistance  & 0x7000000 ) >> 24
		res2 = (resistance  & 0xff0000 ) >> 16
		res3 = (resistance  & 0xff00 ) >> 8
		res4 = resistance & 0xff
		
		bytes = [
			sensorTypesBits["Sense Resistor"] | res1,
			res2,
			res3,
			res4
		]
		
		# bytes = [
			# 0xe8,
			# 0x2d,
			# 0xc8,
			# 0x00
		# ]
		self._sendCmd(channelAssigmentAddr[channel], bytes)
		
	def setRTD(self, channel, 
			senseResistor = 0b10, 
			wire = 0,
			excitationMode = 0b01, 
			excitationCurrent = 0b101, 
			rtdCurve = 0):		
			
		customAddress = 0
		customLength = 0
		
		####
		senseResistorHi = (senseResistor >> 2) & 0b111
		senseResistorLo = senseResistor & 0b11
		excitationCurrentHi = (excitationCurrent >> 2) & 0b11
		excitationCurrentLo = excitationCurrent & 0b11
		customAddressHi = (customAddress >> 2) & 0b1111
		customAddressLo = customAddress & 0b11
	
		bytes = [
			sensorTypesBits["RTD PT-1000"] | senseResistorHi,
			senseResistorLo << 6 | wire << 4 | excitationMode << 2 | excitationCurrentHi,
			excitationCurrentLo << 6 | rtdCurve << 4 | customAddressHi,
			customAddressLo << 6 | customLength
		]
				
		self._sendCmd(channelAssigmentAddr[channel], bytes)
		
	def initiateCorvesion(self, channel):
		bytes = [
			START | channelMapping[channel]
		]
		
		self._sendCmd(CMD_STAT_REG, bytes)
		
	def selectChannels(self, channelList):
	
		bytesHi = 0
		bytesLo = 0
		
		for ch in channelList:
			if ch == "CH9" or ch == "CH10":
				bytesHi = bytesHi | channelSelectionBits[ch]
			else:
				bytesLo = bytesLo | channelSelectionBits[ch]
		
		self._sendCmd(MUL_CONV_MASK_REG[0], [bytesHi])
		self._sendCmd(MUL_CONV_MASK_REG[1], [bytesLo])
		
	def selectAllChannels(self):
		bytes = [
			0x03
		]
		
		self._sendCmd(MUL_CONV_MASK_REG[0], bytes)
		
		bytes = [
			0xff
		]
		
		self._sendCmd(MUL_CONV_MASK_REG[1], bytes)
	
	def waitConversion(self):
		timeout = time.time() + 10
		while (time.time() < timeout):
			raw = self._sendCmd(CMD_STAT_REG, [], rw = SPI_READ, bytesToRead = 1)
			status = int(raw.decode(), 16)
			if (status & DONE):
				return 1
				
		print("Wait conversion timeout")
		return 0
		
	def readChannelData(self, channel):
		return self._sendCmd(channelDataAddr[channel], [], rw = SPI_READ)
		
	def readAllChannelData(self):
		return self._sendCmd(channelDataAddr["CH1"], [], rw = SPI_READ, bytesToRead=10*4)
		
	def convertStringToVoltage(self, bytes):
		# convert hex in ascci to integer
		raw = int(bytes.decode(), 16)	
		return rawToVolatge(raw)
	
	def convertAllStringsToVoltage(self, data):
		data = data.decode('ascii')
		data = textwrap.wrap(data, 8)
		retVal = []
		for d in data:
			raw = int(d, 16)	
			retVal.append(rawToVolatge(raw))
		
		return retVal
		
	def getStatusByte(self, bytes):
		raw = int(bytes.decode(), 16)
		return (raw & 0xff000000) >> 24
		
	def decodeStatusByte(self, statusByte):
		bitmask = 1
		retVal = []
		if statusByte & bitmask:
			retVal.append(errBitMapping[bitmask])
		else:
			retVal.append("Not valid!")
			
		for i in range(1, 8):
			bitmask = 1 << i
			if (statusByte & bitmask):
				retVal.append(errBitMapping[bitmask])
			
		return retVal
		
	def getStatusMsg(self, data):
		statusByte = self.getStatusByte(data)
		return self.decodeStatusByte(statusByte)
		
	def convertAllRawToTemperature(self, data):
		data = data.decode('ascii')
		data = textwrap.wrap(data, 8)
		retVal = []
		for d in data:
			raw = int(d, 16)
			# get rid of status byte
			raw = raw & 0x00ffffff
			
			# get if signed
			if raw & 0x00800000:
				raw = raw - 1
				raw = ~raw
				raw = raw & 0x00ffffff
				result = -(raw / 2**10)
			else:
				result = (raw / 2**10)
					
				retVal.append(result)
		
		return retVal
		
	def convertRawToTemperature(self, bytes):
		# convert hex in ascci to integer
		raw = int(bytes.decode(), 16)
		
		# get rid of status byte
		raw = raw & 0x00ffffff
			
		# get if signed
		if raw & 0x00800000:
			raw = raw - 1
			raw = ~raw
			raw = raw & 0x00ffffff
			result = -(raw / 2**10)
		else:
			result = (raw / 2**10)
		
		return result
		
if __name__ == "__main__":
	with LTC2986(port = sys.argv[1]) as datalogger:
		# #one channel adc demo:
		# datalogger.setDirectADC("CH1")
		# datalogger.initiateCorvesion("CH1")
		# datalogger.waitConversion()
		# data = datalogger.readChannelData("CH1")
		# result = datalogger.convertStringToVoltage(data)
		# print(data)
		# print(result)
		
		
		# all channel adc demo
		# chList = ["CH1", "CH2", "CH3", "CH4", "CH5", "CH6", "CH7", "CH8", "CH9", "CH10"]
		# for ch in chList:
			# datalogger.setDirectADC(ch)
		# datalogger.selectAllChannels()
		# while 1:
			# datalogger.initiateCorvesion("multiple")
			# datalogger.waitConversion()
			# string = ""
			# data = datalogger.readAllChannelData()
			# result = datalogger.convertAllStringsToVoltage(data)
			# for r in result:
				# string += ",%.10f" % (r)
			# logString(string)
			
			
		# # calibrate diode
		# channelsToRead = ["CH6","CH10"]
		# datalogger.selectChannels(channelsToRead)
		# datalogger.setRTD("CH6")
		# datalogger.setResitor("CH2", 2930)
		# ideality = 1.
		# errTable = []
		# while ideality < 1.090:
			# datalogger.setDiode("CH10", ideality = ideality)
			# time.sleep(0.1)
			# datalogger.initiateCorvesion("multiple")
			# datalogger.waitConversion()
			# data = datalogger.readChannelData("CH6")
			# rtdTemp = datalogger.convertRawToTemperature(data)
			# data = datalogger.readChannelData("CH10")
			# diodeTemp = datalogger.convertRawToTemperature(data)
			
			# err = math.fabs(rtdTemp - diodeTemp)
			# print(ideality, err)
			# errTable.append([err, ideality])
			# ideality += 0.001
			
		# minErr = errTable[0][0]
		# for entry in errTable:
			# if entry[0] < minErr:
				# minErr = entry[0]
				# ideality = entry[1]
				
		# print("Proposed ideality for CH10 diode: %lf with err %lf" % (ideality, minErr))	
		# datalogger.setDiode("CH9", ideality = ideality)		
		# sys.exit()
			
			
		
			
		# PT-1000 & diode demo
		datalogger.setRTD("CH4")
		datalogger.setRTD("CH6")
		datalogger.setRTD("CH8")
		datalogger.setResitor("CH2", 2930)
		
		# initially for both
		# initially 1.05499935150146484375 for both
		datalogger.setDiode("CH10", ideality = 1.059000)
		datalogger.setDiode("CH9", ideality = 1.058000)
		
		channelsToRead = ["CH4","CH6","CH8","CH9", "CH10"]
		datalogger.selectChannels(channelsToRead)
		while 1:
			datalogger.initiateCorvesion("multiple")
			datalogger.waitConversion()
			result = []
			for ch in channelsToRead:
				data = datalogger.readChannelData(ch)
				result.append(datalogger.convertRawToTemperature(data))
			
			string = ""
			for r in result:
				string += ",%.10f" % (r)
			logString(string)
