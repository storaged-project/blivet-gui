#!/usr/bin/python2

from blivet import *

def printDeviceTree(blivetStorage, root):
	
	global depth
	for i in range(depth):
		print ' ',
	
	if root.kids != 0:
		depth += 1
	
	print root.name
	
	for child in blivetStorage.devicetree.getChildren(root):
		printDeviceTree(blivetStorage, child)


myComputerStorage = Blivet() #jen si vytvorim
myComputerStorage.reset() #tim nactu informace o vsech discich a vubec storage zarizenich

roots = []

for device in myComputerStorage.devices:
	if len(device.parents) == 0:
		roots.append(device)

#for root in roots:
	#depth = 0
	#printDeviceTree(myComputerStorage, root)

for root in roots:
	print root.name