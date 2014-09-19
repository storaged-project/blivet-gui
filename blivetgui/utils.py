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

from dialogs import message_dialogs

import gettext

import os, subprocess, copy

import pykickstart.parser
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

def swap_is_on(sysfs_path):
	""" Is selected swap in use?
	
		:param sysfs_path: sysfs path for swap
		:type sysfs_path: str
		
	"""
	
	try:
		swaps = open("/proc/swaps", "r")
	except IOError as e:
		return None
	
	for line in swaps:
		# /proc/swaps line fmt:
		# Filename-Type-Size-Used-Priority
		if line.split()[0].split("/")[-1] == sysfs_path.split("/")[-1]:
			return True
	
	return False

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
	
	def __init__(self, free_size, parents, logical=False):
		"""
		
		:param free_size: size of free space
		:type free_size: blivet.Size
		:param parents: list of parent devices
		:type parents: list #FIXME blivet.devices.ParentList
		:param logical: is this free space inside extended partition
		:type logical: bool
		
		"""
		
		self.name = _("free space")
		self.size = free_size
		
		self.isLogical = logical
		self.isFreeSpace = True
		
		self.format = None
		self.type = "free space"
		self.kids = 0
		self.parents = parents
		
class BlivetUtils():
	""" Class with utils directly working with blivet itselves
	"""
	
	def __init__(self, main_window, kickstart=False):
		
		if kickstart:
			self.ksparser = pykickstart.parser.KickstartParser(makeVersion())
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

	def get_free_disks_info(self):
		""" Returns list of disks with free space
		"""

		free_disks = []

		for disk in self.storage.disks:
			free_space = partitioning.getFreeRegions([disk])
			for free in free_space:
				free_size = Size(free.length * free.device.sectorSize)

				if free_size > Size("2 MiB"):
					free_disks.append((disk,free_size))

		return free_disks

	
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
		
		if blivet_device.isDisk and blivet_device.format.type == None:
			# empty disk without disk label
			
			partitions.append(FreeSpaceDevice(blivet_device.size, [blivet_device], False))
			
			return partitions

		elif blivet_device.isDisk and blivet_device.format.type == "iso9660":
			# LiveUSB

			return partitions
		
		elif blivet_device.isDisk:
			
			extended = None
			
			for partition in partitions:
				if hasattr(partition, "isExtended") and partition.isExtended:
					extended = partition
					break
			
			free_space = partitioning.getFreeRegions([blivet_device])
			
			if len(free_space) == 0:
				# no free space
				
				return partitions
			
			for free in free_space:
				if free.length < 4096:
					# too small to be usable
					continue
				
				free_size = Size(free.length * free.device.sectorSize) # free space in B
				
				added = False
				
				for partition in partitions:
					
					if hasattr(partition, "partedPartition") and free.start < partition.partedPartition.geometry.start:
						if extended and extended.partedPartition.geometry.start <= free.start and extended.partedPartition.geometry.end >= free.end:
							partitions.insert(partitions.index(partition),FreeSpaceDevice(free_size, [blivet_device], True))
						
						else:
							partitions.insert(partitions.index(partition),FreeSpaceDevice(free_size, [blivet_device], False))
						added = True
						break

					elif hasattr(partition, "partedPartition") and free.start > partition.partedPartition.geometry.start:
						if extended and extended.partedPartition.geometry.start <= free.start and extended.partedPartition.geometry.end >= free.end:
							partitions.insert(partitions.index(partition)+1,FreeSpaceDevice(free_size, [blivet_device], True))
							added = True
							break

				if not added:
					# free space is at the end of device
					if extended and extended.partedPartition.geometry.start <= free.start and extended.partedPartition.geometry.end >= free.end:
						partitions.append(FreeSpaceDevice(free_size, True))
						
					else:
						partitions.append(FreeSpaceDevice(free_size, [blivet_device], False))
			
			return partitions
			
		elif blivet_device._type == "lvmvg":
			
			if blivet_device.freeSpace > 0:
				partitions.append(FreeSpaceDevice(blivet_device.freeSpace, [blivet_device]))
			
			return partitions
		
		elif blivet_device._type == "partition":
			# empty physical volume
			
			if blivet_device.format.type == "lvmpv" and blivet_device.kids == 0:
				partitions.append(FreeSpaceDevice(blivet_device.size, [blivet_device]))
			
			return partitions
		
		elif blivet_device._type == "luks/dm-crypt" and blivet_device.format.type == "lvmpv" and blivet_device.kids == 0:
			# empty luks encrypted physical volume
			
			partitions.append(FreeSpaceDevice(blivet_device.size, [blivet_device]))
			
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
		
		try:	
			self.storage.destroyDevice(blivet_device)
		except Exception as e:

			title = _("Error:")
			msg = _("Unknown error appeared:\n\n{0}.").format(e)
			message_dialogs.ErrorDialog(self.main_window, title, msg)
	
	def device_resizable(self,blivet_device):
		""" Is given device resizable
		
			:param blivet_device: blivet device
			:type blivet_device: blivet.Device
			:returns: device resizable, minSize, maxSize, size
			:rtype: tuple
			
		"""
		
		if blivet_device.resizable and blivet_device.format.resizable:
			
			blivet_device.format.updateSizeInfo()
			
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
		target_size = Size(str(settings[1]) + "MiB")
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
			self.storage.resizeDevice(blivet_device, target_size)
		
		else:
			self.storage.resizeDevice(blivet_device, target_size)
			new_fmt = formats.getFormat(target_fs, device=blivet_device.path)
			self.storage.formatDevice(blivet_device, new_fmt)
		
		try:
			partitioning.doPartitioning(self.storage)
			return True
		
		except PartitioningError as e:
			title = _("Error:")
			msg = _("Unknown error appeared:\n\n{0}.").format(e)
			message_dialogs.ErrorDialog(self.main_window, title, msg)

			return False
		
		except _ped.PartitionException as e:
			title = _("Error:")
			msg = _("Unknown error appeared:\n\n{0}.").format(e)
			message_dialogs.ErrorDialog(self.main_window, title, msg)
			
			return False

	def _pick_device_name(self, name, parent_devices):
		""" Pick name for device. If user choosed a name, check it and (if necessary) change it

			:param name: name selected by user
			:type name: str
			:param parent_devices: list of parent devices
			:type parent_devices: list of blivet.Device
			:returns: new (valid) name
			:rtype: str

		"""

		if name == None:
				name = self.storage.suggestDeviceName(parent=parent_devices,swap=False)
			
		else:
			name = self.storage.safeDeviceName(name)

		if name in self.storage.names:
			for i in range(100):
				if name + "-" + str(i) not in self.storage.names:
					name = name + "-" + str(i)
					break

		if name in self.storage.names:
			name = self.storage.suggestDeviceName(parent=parent_devices,swap=False)

		return name

	
	def add_device(self, user_input):
		""" Create new device
		
			:param user_input: selected parameters from AddDialog
			:type user_input: class UserInput
			:returns: new device name
			:rtype: str
			
		"""
		
		device_id = None
		
		if user_input.device_type == _("Partition"):

			if user_input.encrypt:
				dev = self.storage.newPartition(size=user_input.size, parents=user_input.parents)
				self.storage.createDevice(dev)
				
				fmt = formats.getFormat(fmt_type="luks", passphrase=user_input.passphrase, device=dev.path)
				self.storage.formatDevice(dev, fmt)
				
				luks_dev = devices.LUKSDevice("luks-%s" % dev.name, fmt=getFormat(user_input.filesystem, device=dev.path), size=dev.size, parents=[dev])
				
				self.storage.createDevice(luks_dev)
				
				device_id = luks_dev.id

			else:

				# extreme situation -- we have 3 primary partitions and trying to add 4th
				# partition with same size as current free space on disk, blivet creates
				# extened partition and tries to create logical partition with same size 
				# and fails -- in this situation we need to reserve 2 MiB for the extended 
				# partition

				extended = False
				size_diff = self.storage.getFreeSpace(disks=[user_input.parents[0]])[user_input.parents[0].name][0] - user_input.size

				if user_input.parents[0].kids == 3 and size_diff < Size("2 MiB"):
					for child in self.storage.devicetree.getChildren(user_input.parents[0]):
						if hasattr(child, "isExtended") and child.isExtended:
							extended = True
							break

					if not extended:
						target_size = target_size - Size("2 MiB")

				new_part = self.storage.newPartition(size=user_input.size, parents=user_input.parents)
				self.storage.createDevice(new_part)
				
				device_id = new_part.id
				
				new_fmt = formats.getFormat(user_input.filesystem, device=new_part.path, label=user_input.label, mountpoint=user_input.mountpoint)
				self.storage.formatDevice(new_part, new_fmt)

		elif user_input.device_type == "LVM2 Storage":

			device_name = self._pick_device_name(user_input.name, user_input.parents)

			if user_input.encrypt:
				dev = self.storage.newPartition(size=user_input.size, parents=user_input.parents)
				self.storage.createDevice(dev)
				
				fmt = formats.getFormat(fmt_type="luks", passphrase=user_input.passphrase, device=dev.path)
				self.storage.formatDevice(dev, fmt)
				
				luks_dev = devices.LUKSDevice("luks-%s" % dev.name, fmt=getFormat("lvmpv", device=dev.path), size=dev.size, parents=[dev])
				
				self.storage.createDevice(luks_dev)

				new_vg = self.storage.newVG(size=luks_dev.size, parents=[luks_dev], name=device_name)
				self.storage.createDevice(new_vg)
			
				device_id = new_vg.id
				
			else:			
				new_part = self.storage.newPartition(size=user_input.size, parents=user_input.parents)				
				self.storage.createDevice(new_part)
				
				new_fmt = formats.getFormat("lvmpv", device=new_part.path)
				self.storage.formatDevice(new_part, new_fmt)

				new_vg = self.storage.newVG(size=new_part.size, parents=[new_part], name=device_name)
				self.storage.createDevice(new_vg)
			
				device_id = new_vg.id

		elif user_input.device_type == _("LVM2 Logical Volume"):
			
			device_name = self._pick_device_name(user_input.name, user_input.parents)

			new_part = self.storage.newLV(size=user_input.size, parents=user_input.parents, name=device_name)
			
			device_id = new_part.id
			
			self.storage.createDevice(new_part)
			
			new_fmt = formats.getFormat(user_input.filesystem, device=new_part.path, label=user_input.label, mountpoint=user_input.mountpoint)
			self.storage.formatDevice(new_part, new_fmt)
		
		elif user_input.device_type == _("LVM2 Volume Group"):
			
			device_name = self._pick_device_name(user_input.name, user_input.parents)
				
			new_part = self.storage.newVG(size=user_input.size, parents=user_input.parents, name=device_name)
			
			device_id = new_part.id
			
			self.storage.createDevice(new_part)
			
		elif user_input.device_type == _("LVM2 Physical Volume"):
			
			if user_input.encrypt:
				dev = self.storage.newPartition(size=user_input.size, parents=user_input.parents)
				self.storage.createDevice(dev)
				
				fmt = formats.getFormat(fmt_type="luks", passphrase=user_input.passphrase, device=dev.path)
				self.storage.formatDevice(dev, fmt)
				
				luks_dev = devices.LUKSDevice("luks-%s" % dev.name, fmt=getFormat("lvmpv", device=dev.path), size=dev.size, parents=[dev])
				
				self.storage.createDevice(luks_dev)
				
				device_id = luks_dev.id
				
			else:			
				new_part = self.storage.newPartition(size=user_input.size, parents=user_input.parents)
				
				device_id = new_part.id
				
				self.storage.createDevice(new_part)
				
				new_fmt = formats.getFormat("lvmpv", device=new_part.path)
				self.storage.formatDevice(new_part, new_fmt)

		elif user_input.device_type == _("Btrfs Volume"):

			device_name = self._pick_device_name(user_input.name, user_input.parents)

			# for btrfs we need to create parents first -- currently selected "parents" are
			# disks but "real parents" for subvolume are btrfs formatted partitions
			btrfs_parents = []

			# exact total size of newly created partitions (future parents)
			total_size = Size("0 MiB")

			for parent in user_input.parents:

				# FIXME: size of parent btrfs partitions -- now I know the size is total size / 
				# number of parents, because the same size of parents (partitions) is hardcoded
				# but this will change in future -- it is neccessary to redisign whole arguments
				# passing from dialog to lists_partitions to here (named tuple or class)

				new_part = self.storage.newPartition(size=user_input.size/len(user_input.parents), parents=[parent])				
				self.storage.createDevice(new_part)

				new_fmt = formats.getFormat("btrfs", device=new_part.path)
				self.storage.formatDevice(new_part, new_fmt)

				total_size += new_part.size

				# we need to try to create partitions immediately, if something fails, fail now
				try:
					partitioning.doPartitioning(self.storage)

				except errors.PartitioningError as e:
					title = _("Error:")
					msg = _("Unknown error appeared:\n\n{0}.").format(e)
					message_dialogs.ErrorDialog(self.main_window, title, msg)
			
					return None

				btrfs_parents.append(new_part)

			new_btrfs = self.storage.newBTRFS(size=total_size, parents=btrfs_parents, name=device_name)
			self.storage.createDevice(new_btrfs)

			device_id = new_btrfs.id

		elif user_input.device_type == _("Btrfs Subvolume"):

			device_name = self._pick_device_name(user_input.name, user_input.parents)

			new_btrfs = self.storage.newBTRFSSubVolume(parents=user_input.parents, name=device_name)
			self.storage.createDevice(new_btrfs)

			device_id = new_btrfs.id

			
		try:
			
			partitioning.doPartitioning(self.storage)
			
			return self.storage.devicetree.getDeviceByID(device_id)
		
		except Exception as e:
			title = _("Error:")
			msg = _("Unknown error appeared:\n\n{0}.").format(e)
			message_dialogs.ErrorDialog(self.main_window, title, msg)
			
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
		""" Get blivet device by name
		
			:param device_name: device name
			:type device_name: str
			:returns: blviet device
			:rtype: blivet.StorageDevice
			
		"""
		
		blivet_device = self.storage.devicetree.getDeviceByName(device_name)
		
		return blivet_device
	
	def get_blivet_device(self, device_uuid):
		""" Get blivet device by UUID
		
			:param device_uuid: device uuid
			:type device_name: str
			:returns: blviet device
			:rtype: blivet.StorageDevice
			
		"""
		
		blivet_device = self.storage.devicetree.getDeviceByUuid(device_uuid)
		
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
	
	def kickstart_mountpoints(self):
		
		#delete existing mountpoints from devicetree and save them for future use
		old_mountpoints = {}
		
		for mountpoint in self.storage.mountpoints.values():
			old_mountpoints[mountpoint.format.uuid] = mountpoint.format.mountpoint
			mountpoint.format.mountpoint = None
			mountpoint.format._mountpoint = None

		# FIXME set swaps to non-existent in order to set their status to False
		for swap in self.storage.swaps:
			swap.format.exists = False
		
		return old_mountpoints
	
	def kickstart_use_disks(self, disk_names):
		
		for name in disk_names:
			self.ksparser.handler.ignoredisk.onlyuse.append(name)
		
		self.storage.ksdata = self.ksparser.handler
		
		self.storage.reset()
		
		# ignore existing mountpoints
	
	def luks_decrypt(self, blivet_device, passphrase):
		""" Decrypt selected luks device
		
			:param blivet_device: device to decrypt
			:type blivet_device: LUKSDevice
			:param passphrase: passphrase
			:type passphrase: str
		
		"""
		
		assert blivet_device.format.type == "luks"
		
		blivet_device.format._setPassphrase(passphrase)
		
		try:
			blivet_device.format.setup()
		
		except CryptoError as e:
			
			return e
		
		self.storage.devicetree.populate()
		
		return
			
	
	@property
	def return_devicetree(self):
		
		return self.storage.devicetree
	
	def override_devicetree(self, devicetree):
		
		self.storage.devicetree = copy.deepcopy(devicetree)
	
	def blivet_reset(self):
		""" Blivet.reset()
		"""
		
		self.storage.reset()
	
	def blivet_reload(self):
		
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