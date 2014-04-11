#!/usr/bin/python2

from blivet import *

#TODO
# do classy -- potrebuji nainitovat na nacist storage a pak s nim vzdycky pracovat


def GetDisks():
	myComputerStorage = Blivet() #jen si vytvorim #FIXME
	myComputerStorage.reset() #tim nactu informace o vsech discich a vubec storage zarizenich

	roots = []

	for device in myComputerStorage.devices:
		if len(device.parents) == 0 and device.isDisk:
			roots.append(device)
			
	return roots

def GetGroupDevices():
	myComputerStorage = Blivet() #jen si vytvorim #FIXME
	myComputerStorage.reset() #tim nactu informace o vsech discich a vubec storage zarizenich

	groups = []

	for device in myComputerStorage.devices:
		if device._type == "lvmvg":
			groups.append(device)
			
	return groups

def GetPartitions(disk):
	partitions = []
	
	myComputerStorage = Blivet() #jen si vytvorim
	myComputerStorage.reset() #tim nactu informace o vsech discich a vubec storage zarizenich
	
	partitions = myComputerStorage.devicetree.getChildren(myComputerStorage.devicetree.getDeviceByName(disk))
	
	return partitions
