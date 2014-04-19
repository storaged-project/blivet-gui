#!/usr/bin/python2

from blivet import *

#TODO
# do classy -- potrebuji nainitovat a nacist storage a pak s nim vzdycky pracovat

class BlivetUtils():
	def __init__(self):
		self.storage = Blivet()
		self.storage.reset()

	def GetDisks(self):
		roots = []

		for device in self.storage.devices:
			if len(device.parents) == 0 and device.isDisk:
				roots.append(device)
				
		return roots

	def GetGroupDevices(self):

		groups = []

		for device in self.storage.devices:
			if device._type == "lvmvg":
				groups.append(device)
				
		return groups

	def GetPartitions(self,disk):
		partitions = []
		
		partitions = self.storage.devicetree.getChildren(self.storage.devicetree.getDeviceByName(disk))
		
		#FIXME
		#detect free space on disk
		#sdb = b.devicetree.getDeviceByName("sdb")
		#blivet.partitioning.getFreeRegions([sdb]) -- returns list of free space (parted.geometry.Geometry)
		
		return partitions
