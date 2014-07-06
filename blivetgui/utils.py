# -*- coding: utf-8 -*-
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
#------------------------------------------------------------------------------#

from blivet import *

from dialogs import *

import gettext

import os, subprocess, copy

from pykickstart.parser import *
from pykickstart.version import makeVersion

#------------------------------------------------------------------------------#

APP_NAME = "blivet-gui"

dirname, filename = os.path.split(os.path.abspath(__file__))

gettext.bindtextdomain('blivetgui', dirname + '/i18n')
gettext.textdomain('blivetgui')
_ = gettext.gettext

#------------------------------------------------------------------------------#

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
		
		self.format = None
		
class BlivetUtils():
	""" Class with utils directly working with blivet itselves
	"""
	
	def __init__(self, main_window, kickstart=False):
		
		if kickstart:
			self.ksparser = KickstartParser(makeVersion())
			self.storage = Blivet(ksdata=self.ksparser.handler)
		else:
			self.storage = Blivet()
			
		self.storage.reset()
		
		self.main_window = main_window
		
	def get_disks(self):
		""" Return list of all disk devices on current system
		
			:returns: list of all "disk" devices
			:rtype: list
			
		"""
		
		return self.storage.disks
	
	def get_disk_names(self):
		""" Return list of names of all disk devices on current system
		
			:returns: list of all "disk" devices names
			:rtype: list
			
		"""
		
		disk_names = []
		
		for disk in self.storage.disks:
			disk_names.append(disk.name)
		
		return disk_names
	
	def get_group_devices(self):
		""" Return list of LVM2 Volume Group devices
		
			:returns: list of LVM2 VG devices
			:rtype: list
			
		"""
		
		return self.storage.vgs
	
	def get_physical_devices(self):
		""" Return list of LVM2 Physical Volumes
		
			:returns: list of LVM2 PV devices
			:rtype: list
			
		"""
		
		return self.storage.pvs
	
	def get_free_pvs_info(self):
		""" Return list of PVs without VGs
		
			:returns: list of free PVs with name and size
			:rtype: tuple
			
		"""
		
		pvs = self.get_physical_devices()
		
		free_pvs = []
		
		for pv in pvs:
			if pv.kids == 0:
				free_pvs.append(pv)
		
		return free_pvs
	
	def get_free_space(self, blivet_device, partitions):
		""" Find free space on device
		
			:param blivet_device: blivet device
			:type blivet_device: blivet.Device
			:param paritions: partions (children) of device
			:type partition: list
			:returns: list of partitions + free space
			:rtype: list
			
		"""
		
		if blivet_device == None:
			return []
		
		if blivet_device.isDisk and blivet_device.kids == 0:
			# disk is empty
			
			partitions.append(FreeSpaceDevice(int(blivet_device.size)))
			
			return partitions
		
		elif blivet_device.isDisk and blivet_device.kids > 0:
			# disk with partitions
			
			free_space = partitioning.getFreeRegions([blivet_device])
			
			if len(free_space) == 0:
				# no free space
				
				return partitions
			
			for free in free_space:
				if free.length < 4096:
					# too small to be usable
					continue
				
				free_size = int((free.length*free.device.sectorSize) / (free.device.sectorSize*2)**2) # free space in MiB
				
				added = False
				
				for partition in partitions:
					
					if hasattr(partition, "partedPartition") and free.start < partition.partedPartition.geometry.start:
						partitions.insert(partitions.index(partition),FreeSpaceDevice(free_size))
						added = True
						break
					
				if not added:
					# free space is at the end of device
					partitions.append(FreeSpaceDevice(free_size))
			
			return partitions
			
		elif blivet_device._type == "lvmvg":
			
			if blivet_device.freeSpace > 0:
				partitions.append(FreeSpaceDevice(blivet_device.freeSpace))
			
			return partitions
		
		elif blivet_device._type == "partition":
			# empty physical volume
			
			if blivet_device.format.type == "lvmpv" and blivet_device.kids == 0:
				partitions.append(FreeSpaceDevice(blivet_device.size))
			
			return partitions
		
		else:
			return partitions
	
	def get_partitions(self,blivet_device):
		""" Get partitions (children) of selected device
		
			:param blivet_device: blivet device
			:type blivet_device: blivet.Device
			:returns: list of partitions
			:rtype: list
			
		"""
		
		if blivet_device == None:
			return []
		
		blivet_device = self.storage.devicetree.getDeviceByName(blivet_device.name)
		
		partitions = []		
		partitions = self.storage.devicetree.getChildren(blivet_device)
		partitions = self.get_free_space(blivet_device,partitions)
		
		return partitions
	
	def delete_device(self,blivet_device):
		""" Delete device
		
			:param blivet_device: blivet device
			:type blivet_device: blivet.Device
			
		"""
		
		self.storage.destroyDevice(blivet_device)
	
	def device_resizable(self,blivet_device):
		""" Is given device resizable
		
			:param blivet_device: blivet device
			:type blivet_device: blivet.Device
			:returns: device resizable, minSize, maxSize, size
			:rtype: tuple
			
		"""
		
		if blivet_device.resizable:
			
			return (True, blivet_device.minSize, blivet_device.maxSize, blivet_device.size)
		
		else:
			
			return (False, blivet_device.size, blivet_device.size, blivet_device.size)
		
	
	def edit_partition_device(self, blivet_device, settings):
		""" Edit device
		
			:param blivet_device: blivet.Device
			:type blivet_device: blivet.Device
			:param settings: resize, target_size, target_fs
			:type settings: tuple
			:returns: success
			:rtype: bool
			
		"""
		
		resize = settings[0]
		target_size = settings[1]
		target_fs = settings[2]
		mountpoint = settings[3]
		    
		if resize == False and target_fs == None:
			
			if mountpoint == None:
				return False
			
			else:
				blivet_device.format.mountpoint = mountpoint
		
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
			BlivetError(e, self.main_window)
		
		except _ped.PartitionException as e:
			BlivetError(e, self.main_window)
			
			return False
	
	def add_device(self, parent_devices, device_type, fs_type, target_size, name=None, label=None, mountpoint=None, flags=[]):
		""" Create new device
		
			:param parent_devices: parent devices
			:type parent_devices: list of blivet.Device
			:param device_type: type of device to create
			:type device_type: str
			:param fs_type: filesystem
			:type fs_type: str
			:param target_size: target size
			:type target_size: int
			:param name: device name
			:type name: str
			:param label: device label
			:type label: str
			:param mountpoint: mountpoint
			:type mountpoint: str
			:param flags: device flags
			:type flags: list of str
			:returns: new device name
			:rtype: str
			
		"""
		
		device_id = 0	
		
		if device_type == _("Partition"):
			new_part = self.storage.newPartition(size=target_size, parents=parent_devices)
			self.storage.createDevice(new_part)
			
			device_id = new_part.id
			
			new_fmt = formats.getFormat(fs_type, device=new_part.path, label=label, mountpoint=mountpoint)
			self.storage.formatDevice(new_part, new_fmt)
			
		elif device_type == _("LVM2 Logical Volume"):
			
			if name == None:
				name = self.storage.suggestDeviceName(parent=parent_devices[0],swap=False)
			
			else:
				name = self.storage.safeDeviceName(name)
			
			new_part = self.storage.newLV(size=target_size, parents=parent_devices, name=name)
			
			device_id = new_part.id
			
			self.storage.createDevice(new_part)
			
			new_fmt = formats.getFormat(fs_type, device=new_part.path, label=label, mountpoint=mountpoint)
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
			
			return self.storage.devicetree.getDeviceByID(device_id)
		
		except PartitioningError as e:
			BlivetError(e, self.main_window)
			
			return None
	
	def get_device_type(self, blivet_device):
		""" Get device type
		
			:param blivet_device: blivet device
			:type device_name: blivet.Device
			:returns: type of device
			:rtype: str
			
		"""
		
		assert blivet_device != None
		
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
	
	def get_parent_pvs(self, blivet_device):
		""" Return list of LVM VG PVs
		
			:param blivet_device: blivet device
			:type blivet_device: blivet.Device
			:returns: list of devices
			:rtype: list of blivet.StorageDevice
			
		"""
		
		assert blivet_device._type == "lvmvg"
		
		return blivet_device.pvs
	
	def has_disklabel(self, blivet_device):
		""" Has this disk device disklabel
		
			:param blivet_device: blivet device
			:type blivet_device: blivet.Device
			:returns: true/false
			:rtype: bool
			
		"""
		
		assert blivet_device._type == "disk"
		
		return blivet_device.format.type == "disklabel"
	
	def create_disk_label(self, blivet_device):
		""" Create disklabel
		
			:param blivet_device: blivet device
			:type blivet_device: blivet.Device
			
		"""
		
		self.storage.initializeDisk(blivet_device)
		
	def set_bootloader_device(self, disk_name):
		
		blivet_device = self.storage.devicetree.getDeviceByName(disk_name)
		
		assert blivet_device.isDisk
		
		self.ksparser.handler.bootloader.location = "mbr"
		self.ksparser.handler.bootloader.bootDrive = disk_name
		
		self.storage.ksdata = self.ksparser.handler
	
	def kickstart_use_disks(self, disk_names):
		
		for name in disk_names:
			self.ksparser.handler.ignoredisk.onlyuse.append(name)
		
		self.storage.ksdata = self.ksparser.handler
	
	@property
	def return_devicetree(self):
		
		return self.storage.devicetree
	
	def override_devicetree(self, devicetree):
		
		self.storage.devicetree = copy.deepcopy(devicetree)
	
	def blivet_reset(self):
		""" Blivet.reset()
		"""
		
		self.storage.reset()
	
	def blivet_do_it(self):
		""" Blivet.doIt()
		"""
		
		self.storage.doIt()
	
	def create_kickstart_file(self, filename):
		""" Create kickstart config file
		"""
		
		self.storage.updateKSData()
		outfile = open(filename, 'w')
		outfile.write(self.storage.ksdata.__str__())
		outfile.close()