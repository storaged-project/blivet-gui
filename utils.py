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

from dialogs import *

import gettext

import os, subprocess

APP_NAME = "blivet-gui"

gettext.bindtextdomain(APP_NAME, 'po')
gettext.textdomain(APP_NAME)
_ = gettext.gettext

def partition_mounted(partition_path):
	""" Is selected partition partition_mounted
		:param partition_path: /dev path for partition
		:param type: str
		:returns: mountpoint
		:rtype: str
	"""
	
	try:
		mounts = open("/proc/mounts", "r")
	except IOError as e:
		return None
	
	for line in mounts:
		# /proc/mounts line fmt:
		# device-mountpoint-mountopts
		if line.split()[0] == partition_path:
			return line.split()[1]
	
	return None

def os_umount_partition(mountpoint):
	""" Umount selected partition
		:param mountpoint: mountpoint (os.path)
		:type mountpoint: str
		:returns: success
		:rtype: bool
	"""
	
	if not os.path.ismount(mountpoint):
		return False
	
	FNULL = open(os.devnull, "w")
	umount_proc = subprocess.Popen(["umount", mountpoint],stdout=FNULL, stderr=subprocess.STDOUT)
	
	ret = umount_proc.wait()

	if ret != 0:
		return False
	
	return True
	

class FreeSpaceDevice():
	""" Special class to represent free space on disk (device)
		(blivet doesn't have class/device to represent free space)
	"""
	
	def __init__(self,free_size):
		"""
		:param free_size: size of free space in MB
		:type free_size: int
		"""
		self.name = _("free space")
		self.size = free_size

class BlivetUtils():
	""" Class with utils directly working with blivet itselves
	"""
	
	def __init__(self):
		self.storage = Blivet()
		self.storage.reset()

	def get_disks(self):
		""" Return list of all disk devices on current system
			:returns: list of all "disk" devices
			:rtype: list
        """
        
		return self.storage.disks

	def get_group_devices(self):
		""" Return list of LVM2 Volume Group devices
			:returns: list of LVM2 VG devices
			:rtype: list
        """

		return self.storage.vgs
	
	def get_physical_devices(self):
		""" Return list of LVM2 Physical Volumes
			:returns: list of LVM2 PV devices
		"""
		
		return self.storage.pvs
	
	def get_free_pvs_info(self):
		
		pvs = self.get_physical_devices()
		
		free_pvs = []
		
		for pv in pvs:
			if pv.kids == 0:
				free_pvs.append((pv.name, "lvmpv", int(pv.size)))
		
		return free_pvs
	
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
				free = free_space[0]
				partitions2.append(FreeSpaceDevice(int((free.length*free.device.sectorSize) / (free.device.sectorSize*2)**2)))
				return partitions2
			
			if len(free_space) != 0:
				for free in free_space:
					if free.length < 4096:
						continue
					for partition in partitions:
						if partition.name == _("unallocated"):
							break
						
						elif free.start < partition.partedPartition.geometry.start:
							partitions2.insert(partitions.index(partition),FreeSpaceDevice(int((free.length*free.device.sectorSize) / (free.device.sectorSize*2)**2)))
							break
						
						elif free.end > partition.partedPartition.geometry.end:
							partitions2.append(FreeSpaceDevice(int((free.length*free.device.sectorSize) / (free.device.sectorSize*2)**2)))
							break
			
			# Find free space inside extended partition
			for partition in partitions:
				try:
					if partition.isExtended:
						for logical in self.storage.devicetree.getChildren(partition):
							partitions2.append(logical)
							break
						
						free_space = partitioning.getFreeRegions([blivet_device])
						
						# Special occassion -- extended partition with only free space on it
						if len(free_space) != 0 and len(partitions2) == 1:
							for free in free_space:
								if free.length < 2048:
									continue
								partitions2.append(FreeSpaceDevice(int((free.length*free.device.sectorSize) / (free.device.sectorSize*2)**2)))
								break
						
				except AttributeError:
					pass
				
				return partitions2
			
		elif blivet_device._type == "lvmvg":
			if blivet_device.freeSpace > 2:
				partitions.append(FreeSpaceDevice(blivet_device.freeSpace))
			
			return partitions
		
		elif blivet_device._type == "partition":
			if blivet_device.format.type == "lvmpv" and blivet_device.kids == 0:
				partitions.append(FreeSpaceDevice(blivet_device.size))
			
			return partitions
		
		else:
			return partitions

	def get_partitions(self,device_name):
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
	
	def device_resizable(self,device_name):
		""" Is given device resizable
			:param device_name: anme of device
			:type device_name: str
			:returns: device resizable, minSize, maxSize, size
			:rtype: tuple
		"""
		
		blivet_device = self.storage.devicetree.getDeviceByName(device_name)
		
		if blivet_device.resizable:
			return (True, blivet_device.minSize, blivet_device.maxSize, blivet_device.size)
		
		else:
			return (False, blivet_device.size, blivet_device.size, blivet_device.size)
		
	
	def edit_partition_device(self, device_name, settings):
		""" Edit device
			:param device_name: name of device
			:type device_name: str
			:param settings: resize, target_size, target_fs
			:type settings: tuple
			:returns: success
			:rtype: bool
        """
        
		blivet_device = self.storage.devicetree.getDeviceByName(device_name)
		resize = settings[0]
		target_size = settings[1]
		target_fs = settings[2]
		
		#print resize, target_size, target_fs
        
		if resize == False and target_fs == None:
			return False
		
		elif resize == False and target_fs != None:
			new_fmt = formats.getFormat(target_fs, device=blivet_device.path)
			self.storage.formatDevice(blivet_device, new_fmt)
		
		elif resize == True and target_fs == None:
			self.storage.resizeDevice(blivet_device, int(target_size))
		
		else:
			self.storage.resizeDevice(blivet_device, int(target_size))
			new_fmt = formats.getFormat(target_fs, device=blivet_device.path)
			self.storage.formatDevice(blivet_device, new_fmt)
		
		try:
			partitioning.doPartitioning(self.storage)
			return True
		
		except PartitioningError as e:
			BlivetError(e)
			
			return False
	
	def add_device(self, parent_names, device_type, fs_type, target_size, name=None, label=None, flags=[]):
		""" Create new device
			:param parent_names: name of parent device
			:type parent_names: list of str
			:param device_type: type of device to create
			:type device_type: str
			:param fs_type: filesystem
			:type fs_type: str
			:param target_size: target size
			:type target_size: int
			:param label: device label (name)
			:type label: str
			:param flags: device flags
			:type flags: list of str
			:returns: new device name
			:rtype: str
		"""
		
		device_id = 0
		
		parent_devices = []
		
		for pname in parent_names:
			parent_devices.append(self.storage.devicetree.getDeviceByName(pname))		
		
		if device_type == _("Partition"):
			new_part = self.storage.newPartition(size=target_size, parents=parent_devices)
			self.storage.createDevice(new_part)
			
			device_id = new_part.id

			new_fmt = formats.getFormat(fs_type, device=new_part.path, label=label)
			self.storage.formatDevice(new_part, new_fmt)
			
		elif device_type == _("LVM2 Logical Volume"):
			
			if name == None:
				name = self.storage.suggestDeviceName(parent=parent_devices[0],swap=False)
			
			else:
				name = self.storage.safeDeviceName(name)
			
			new_part = self.storage.newLV(size=target_size, parents=parent_devices, name=name)
			
			device_id = new_part.id
			
			self.storage.createDevice(new_part)

			new_fmt = formats.getFormat(fs_type, device=new_part.path, label=label)
			self.storage.formatDevice(new_part, new_fmt)
		
		elif device_type == _("LVM2 Volume Group"):
			
			if name == None:
				name = self.storage.suggestDeviceName(parent=parent_devices,swap=False)
			
			else:
				name = self.storage.safeDeviceName(name)
			
			new_part = self.storage.newVG(size=target_size, parents=parent_devices, name=name)
			
			device_id = new_part.id
			
			self.storage.createDevice(new_part)
			
			
		elif device_type == _("LVM2 Physical Volume"):
			
			new_part = self.storage.newPartition(size=target_size, parents=parent_devices)
			
			device_id = new_part.id
			
			self.storage.createDevice(new_part)
			
			new_fmt = formats.getFormat("lvmpv", device=new_part.path)
			self.storage.formatDevice(new_part, new_fmt)
		
		try:
			partitioning.doPartitioning(self.storage)
			
			return self.storage.devicetree.getDeviceByID(device_id).name
		
		except PartitioningError as e:
			BlivetError(e)
			
			return None
	
	def get_device_type(self, device_name):
		""" Get device type
			:param device_name: device name
			:type device_name: str
			:returns: type of device
			:rtype: str
		"""
		
		blivet_device = self.storage.devicetree.getDeviceByName(device_name)
		
		assert blivet_device._type != None
		
		if blivet_device._type == "partition" and blivet_device.format.type == "lvmpv":
			return "lvmpv"
		
		return blivet_device._type
	
	def get_blivet_device(self, device_name):
		""" Get blivet device
			:param device_name: device name
			:type device_name: str
			:returns: blviet device
			:rtype: blivet.StorageDevice
		"""
		
		blivet_device = self.storage.devicetree.getDeviceByName(device_name)
		
		return blivet_device
	
	def get_parent_pvs(self, device_name):
		""" Return list of LVM VG PVs
			:param device_name: device name
			:type device_name: str
			:returns: list of devices
			:rtype: list of blivet.StorageDevice
		"""
		
		blivet_device = self.storage.devicetree.getDeviceByName(device_name)
		
		assert blivet_device._type == "lvmvg"
		
		return blivet_device.pvs
	
	def blivet_reset(self):
		self.storage.reset()
	
	def blivet_do_it(self):
		self.storage.doIt()