#!/usr/bin/python2

from blivet import *

import gettext

APP_NAME = "blivet-gui"

gettext.bindtextdomain(APP_NAME, 'po')
gettext.textdomain(APP_NAME)
_ = gettext.gettext

class FreeSpaceDevice():
	def __init__(self,freeSpace):
		self.name = _("unallocated")
		self.size = int((freeSpace.length*512) / (1024*1024)) ## FIXME: 512 = block size


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
		
		if disk == None:
			return []
		
		blivetDisk = self.storage.devicetree.getDeviceByName(disk)
		
		partitions = []
		
		partitions = self.storage.devicetree.getChildren(blivetDisk)
		
		partitions2 = copy.deepcopy(partitions)
		
		#FIXME: function
		#FIXME: jen jedna velka prazdna plocha se nezobrazi, viz nize
		if blivetDisk.isDisk: #looking for free space regions, disks only
			freeSpace = partitioning.getFreeRegions([blivetDisk])
			
			if len(freeSpace) != 0:
				for free in freeSpace:
					if free.length < 2048:
						continue
					for partition in partitions:
						if partition.name == _("unallocated"):
							break
						if free.start < partition.partedPartition.geometry.start:
								partitions2.insert(partitions.index(partition),FreeSpaceDevice(free))
						if free.end > partition.partedPartition.geometry.end:
								partitions2.append(FreeSpaceDevice(free))
		
		for partition in partitions:
			try:
				if partition.isExtended:
					for logical in self.storage.devicetree.getChildren(partition):
						partitions2.append(logical)
					
					freeSpace = partitioning.getFreeRegions([blivetDisk]) #FIXME prave proto funkce (mozna ne)
					
					# Special occassion -- extended partition with only free space on it
					if len(freeSpace) != 0 and len(partitions2) == 1:
						for free in freeSpace:
							if free.length < 2048:
								continue
							partitions2.append(FreeSpaceDevice(free))
						
			except AttributeError:
				pass
		
		return partitions2
	
	def delete_device(self,device_name):
		
		device = self.storage.devicetree.getDeviceByName(device_name)		
		self.storage.destroyDevice(device)
		
