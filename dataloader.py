from ltc2986 import *

def genHeaders(channels):
	retVal = []
	retVal.append("time")
	for i in range(0, len(channels)):
		ch = channels[i]
		if ch:
			retVal.append(channelNumbering[i])
			
	return retVal