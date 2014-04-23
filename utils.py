# utils.py
# Classes working directly with blivet instance
# 
# Copyright (C) 2014  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#
# Red Hat Author(s): Vojtech Trefny <vtrefny@redhat.com>
#

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
		""" Return list of all disk devices on current system
			:returns: list of all "disk" devices
			:rtype: list
        """
		roots = []

		for device in self.storage.devices:
			if len(device.parents) == 0 and device.isDisk:
				roots.append(device)
				
		return roots

	def GetGroupDevices(self):
		""" Return list of other devices with children (e.g. LVM volume group)
			:returns: list of "group" devices
			:rtype: list
        """

		groups = []

		for device in self.storage.devices:
			if device._type == "lvmvg":
				groups.append(device)
				
		return groups
	
	def get_free_space(self,device_name,partitions):
		""" Find free space on device
			:param device_name: name of device
			:type device_name: str
			:param paritions: partions (children) of device
			:type partition: list
			:returns: list of partitions + free space
			:rtype: list
        """
		
		if device_name == None:
			return []
		
		blivet_device = self.storage.devicetree.getDeviceByName(device_name)
		
		if blivet_device.isDisk:
			
			free_space = partitioning.getFreeRegions([blivet_device])
			partitions2 = copy.deepcopy(partitions)
			
			# Special occassion -- disk is empty
			if len(partitions) == 0:
				partitions2.append(FreeSpaceDevice(free_space[0]))
				return partitions2
			
			if len(free_space) != 0:
				for free in free_space:
					if free.length < 2048:
						continue
					for partition in partitions:
						if partition.name == _("unallocated"):
							break
						
						elif free.start < partition.partedPartition.geometry.start:
							partitions2.insert(partitions.index(partition),FreeSpaceDevice(free))
						
						elif free.end > partition.partedPartition.geometry.end:
							partitions2.append(FreeSpaceDevice(free))
			
			# Find free space inside extended partition
			for partition in partitions:
				try:
					if partition.isExtended:
						for logical in self.storage.devicetree.getChildren(partition):
							partitions2.append(logical)
						
						free_space = partitioning.getFreeRegions([blivet_device])
						
						# Special occassion -- extended partition with only free space on it
						if len(free_space) != 0 and len(partitions2) == 1:
							for free in free_space:
								if free.length < 2048:
									continue
								partitions2.append(FreeSpaceDevice(free))
						
				except AttributeError:
					pass
			
			return partitions2
		
		else:
			return []

	def GetPartitions(self,device_name):
		""" Get partitions (children) of selected device
			:param device_name: name of device
			:type device_name: str
			:returns: list of partitions
			:rtype: list
        """
		
		if device_name == None:
			return []
		
		blivet_device = self.storage.devicetree.getDeviceByName(device_name)
		
		partitions = []
		
		partitions = self.storage.devicetree.getChildren(blivet_device)
		
		partitions = self.get_free_space(device_name,partitions)
		
		return partitions
	
	def delete_device(self,device_name):
		""" Delete device
			:param device_name: name of device
			:type device_name: str
        """
		
		device = self.storage.devicetree.getDeviceByName(device_name)		
		self.storage.destroyDevice(device)
		
