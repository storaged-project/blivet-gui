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

import blivet

from dialogs import message_dialogs

import gettext

import os, subprocess, copy, traceback, socket

import parted

import pykickstart.parser
from pykickstart.version import makeVersion

#------------------------------------------------------------------------------#

_ = lambda x: gettext.ldgettext("blivet-gui", x)

#------------------------------------------------------------------------------#

PARTITION_TYPE = {"primary" : parted.PARTITION_NORMAL, "logical" : parted.PARTITION_LOGICAL,
    "extended" : parted.PARTITION_EXTENDED}

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
    except IOError:
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
    except IOError:
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
    umount_proc = subprocess.Popen(["umount", mountpoint], stdout=FNULL,
        stderr=subprocess.STDOUT)

    ret = umount_proc.wait()

    if ret != 0:
        return False

    return True

class ISO9660Device():
    """ Special class to represent disk with iso9660 format
    """

    def __init__(self, size, fmt, disk):

        self.size = size

        self.isLogical = False
        self.isFreeSpace = False
        self.isDisk = False
        self.isleaf = True

        self.format = fmt
        self.type = "iso9660"

        self.kids = 0
        self.parents = [disk]

        if self.format.label:
            self.name = self.format.label

        else:
            self.name = _("ISO9660 Disklabel")

class FreeSpaceDevice():
    """ Special class to represent free space on disk (device)
        (blivet doesn't have class/device to represent free space)
    """

    def __init__(self, free_size, start, end, parents, logical=False):
        """

        :param free_size: size of free space
        :type free_size: blivet.Size
        :param start: start block
        :type end: int
        :param end: end block
        :type end: int
        :param parents: list of parent devices
        :type parents: list #FIXME blivet.devices.ParentList
        :param logical: is this free space inside extended partition
        :type logical: bool

        """

        self.name = _("free space")
        self.size = free_size

        self.start = start
        self.end = end

        self.isLogical = logical
        self.isFreeSpace = True

        self.format = None
        self.type = "free space"
        self.kids = 0
        self.parents = parents

    @property
    def isEmptyDisk(self):
        return len(self.parents) == 1 and self.parents[0].type == "disk" and \
            self.parents[0].kids == 0 and self.parents[0].format.type and \
            self.parents[0].format.type not in ["iso9660"]

    @property
    def isUnitializedDisk(self):
        return len(self.parents) == 1 and self.parents[0].type == "disk" and \
            self.parents[0].kids == 0 and self.parents[0].format.type == None

    @property
    def isFreeRegion(self):
        return not (self.isEmptyDisk or self.isUnitializedDisk)

    def __str__(self):
        return "existing " + str(self.size) + " free space"


class BlivetUtils():
    """ Class with utils directly working with blivet itselves
    """

    def __init__(self, main_window, kickstart=False):

        if kickstart:
            self.ksparser = pykickstart.parser.KickstartParser(makeVersion())
            self.storage = blivet.Blivet(ksdata=self.ksparser.handler)
        else:
            self.storage = blivet.Blivet()

        blivet.formats.fs.NTFS._formattable = True

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

    def get_btrfs_volumes(self):
        """ Return list of Btrfs Volumes

            :returns: list of btrfs volumes
            :rtype: list

        """

        return self.storage.btrfsVolumes

    def get_free_pvs_info(self):
        """ Return list of PVs without VGs

            :returns: list of free PVs with name and size
            :rtype: tuple

        """

        pvs = self.get_physical_devices()

        free_pvs = []

        for pv in pvs:
            if pv.kids == 0:
                free_pvs.append((pv, FreeSpaceDevice(pv.size, None, None,
                    pv.parents)))

        return free_pvs

    def get_free_disks_regions(self):
        """ Returns list of non-empty disks with free space
        """

        free_disks = []

        for disk in self.storage.disks:

            if disk.format.type in ["iso9660"]:
                continue

            elif not disk.format.type:
                free_disks.append(FreeSpaceDevice(disk.size, 0,
                    disk.partedDevice.length, [disk]))
                continue

            extended = None

            for partition in self.storage.devicetree.getChildren(disk):
                if partition.type == "partition" and partition.isExtended:
                    extended = (partition.partedPartition.geometry.start,
                        partition.partedPartition.geometry.end)

            free_space = blivet.partitioning.getFreeRegions([disk])
            for free in free_space:
                if extended and free.start >= extended[0] and free.end <= extended[1]:
                    #empty space inside extended partition -> not usable for btrfs
                    #volumes or lvmpv
                    continue

                free_size = blivet.Size(free.length * free.device.sectorSize)

                if free_size > blivet.Size("2 MiB"):
                    free_disks.append(FreeSpaceDevice(free_size, free.start, free.end,
                        [disk]))

        return free_disks

    def get_removable_pvs_info(self, blivet_device):

        #TODO

        assert blivet_device.type == "lvmvg"

        return []

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

            partitions.append(FreeSpaceDevice(blivet_device.size, 0,
                blivet_device.partedDevice.length, [blivet_device], False))

        elif blivet_device.isDisk and blivet_device.format.type in ["iso9660", "btrfs"]:
            # LiveUSB or btrfs partition table

            pass

        elif blivet_device.isDisk:

            extended = None

            for partition in partitions:
                if hasattr(partition, "isExtended") and partition.isExtended:
                    extended = partition
                    break

            free_space = blivet.partitioning.getFreeRegions([blivet_device])

            if len(free_space) == 0:
                # no free space

                return partitions

            for free in free_space:
                if free.length < 4096:
                    # too small to be usable
                    continue

                # free space in B
                free_size = blivet.Size(free.length * free.device.sectorSize)

                added = False

                for partition in partitions:

                    if (hasattr(partition, "partedPartition")
                        and free.start < partition.partedPartition.geometry.start):

                        if (extended and extended.partedPartition.geometry.start <= free.start
                            and extended.partedPartition.geometry.end >= free.end):

                            partitions.insert(partitions.index(partition),
                                FreeSpaceDevice(free_size, free.start, free.end,
                                    [blivet_device], True))

                        else:
                            partitions.insert(partitions.index(partition),
                                FreeSpaceDevice(free_size, free.start, free.end,
                                [blivet_device], False))

                        added = True
                        break

                    elif (hasattr(partition, "partedPartition")
                        and free.start > partition.partedPartition.geometry.start):

                        if (extended and extended.partedPartition.geometry.start <= free.start
                            and extended.partedPartition.geometry.end >= free.end):

                            partitions.insert(partitions.index(partition)+1,
                                FreeSpaceDevice(free_size, free.start, free.end,
                                [blivet_device], True))

                            added = True
                            break

                if not added:
                    # free space is at the end of device
                    if (extended and extended.partedPartition.geometry.start <= free.start
                        and extended.partedPartition.geometry.end >= free.end):

                        partitions.append(FreeSpaceDevice(free_size, free.start,
                        free.end, True))

                    else:
                        partitions.append(FreeSpaceDevice(free_size,free.start,
                            free.end, [blivet_device], False))

        elif blivet_device.type == "lvmvg":

            if blivet_device.freeSpace > 0:
                partitions.append(FreeSpaceDevice(blivet_device.freeSpace, None, None,
                    [blivet_device]))

        elif blivet_device.type in ["partition", "luks/dm-crypt", "mdarray"]:
            # empty (encrypted) physical volume

            if blivet_device.format.type == "lvmpv" and blivet_device.kids == 0:
                partitions.append(FreeSpaceDevice(blivet_device.size, None, None, [blivet_device]))

        return partitions

    def get_partitions(self, blivet_device):
        """ Get partitions (children) of selected device

            :param blivet_device: blivet device
            :type blivet_device: blivet.Device
            :returns: list of partitions
            :rtype: list

        """

        if blivet_device == None:
            return []

        if blivet_device.isDisk and blivet_device.format and blivet_device.format.type == "iso9660":
            # special occasion -- LiveUSB
            return [ISO9660Device(size=blivet_device.size, fmt=blivet_device.format,
                disk=blivet_device)]

        partitions = []
        partitions = self.storage.devicetree.getChildren(blivet_device)
        partitions = self.get_free_space(blivet_device, partitions)

        return partitions

    def delete_disk_label(self, disk_device):
        """ Delete current disk label

            :param disk_device: blivet device
            :type disk_device: blivet.Device

        """

        assert disk_device.isDisk and disk_device.format

        try:
            disk_device.format.teardown()
            action = blivet.deviceaction.ActionDestroyFormat(disk_device)
            # TODO: this looks just wrong
            action.apply()
            action.execute()

        except Exception as e:
            message_dialogs.ExceptionDialog(self.main_window, str(e),
                traceback.format_exc())

    def delete_device(self, blivet_device):
        """ Delete device

            :param blivet_device: blivet device
            :type blivet_device: blivet.Device

        """

        if blivet_device.type == "iso9660":
            # iso9660 disklabel, not going to delete device but destroy disk
            # format instead
            self.delete_disk_label(blivet_device.parents[0])

            return

        try:
            self.storage.destroyDevice(blivet_device)
        except Exception as e:

            message_dialogs.ExceptionDialog(self.main_window, str(e),
                traceback.format_exc())

        # for btrfs volumes delete parents partition after deleting volume
        if blivet_device.type in ["btrfs volume", "mdarray"]:
            for parent in blivet_device.parents:
                if parent.type == "partition":
                    self.delete_device(parent)
                elif parent.type == "disk":
                    self.delete_disk_label(parent)

    def device_resizable(self, blivet_device):
        """ Is given device resizable

            :param blivet_device: blivet device
            :type blivet_device: blivet.Device
            :returns: device resizable, minSize, maxSize, size
            :rtype: tuple

        """

        if blivet_device.resizable and blivet_device.format.resizable:

            blivet_device.format.updateSizeInfo()

            return (True, blivet_device.minSize, blivet_device.maxSize,
                blivet_device.size)

        else:

            return (False, blivet_device.size, blivet_device.size,
                blivet_device.size)


    def edit_partition_device(self, user_input):
        """ Edit device

            :param blivet_device: blivet.Device
            :type blivet_device: blivet.Device
            :param user_input: user selection
            :type user_input: class dialogs.edit_dialog.UserSelection
            :returns: success
            :rtype: bool

        """

        blivet_device = user_input.edit_device

        if user_input.mountpoint:
            blivet_device.format.mountpoint = user_input.mountpoint

        if not user_input.resize and not user_input.format:
            return False

        elif not user_input.resize and user_input.format:
            new_fmt = blivet.formats.getFormat(user_input.filesystem,
                device=blivet_device.path)
            self.storage.formatDevice(blivet_device, new_fmt)

        elif user_input.resize  and not user_input.format:
            self.storage.resizeDevice(blivet_device, user_input.size)

        else:
            self.storage.resizeDevice(blivet_device, user_input.size)
            new_fmt = blivet.formats.getFormat(user_input.filesystem,
                device=blivet_device.path)
            self.storage.formatDevice(blivet_device, new_fmt)

        if user_input.mountpoint:
            blivet_device.format.mountpoint = user_input.mountpoint

        try:
            blivet.partitioning.doPartitioning(self.storage)
            return True

        except Exception as e:

            message_dialogs.ExceptionDialog(self.main_window, str(e),
                traceback.format_exc())

            return False

    def edit_lvmvg_device(self, user_input):

        if user_input.action_type == "add":
            for parent in user_input.parents_list:
                self.add_lvmvg_parent(user_input.edit_device, parent)

        elif user_input.action_type == "remove":
            pass #TODO

        else:
            return False

        return True

    def _pick_device_name(self, name, parent_device=None):
        """ Pick name for device.
            If user choosed a name, check it and (if necessary) change it

            :param name: name selected by user
            :type name: str
            :param parent_device: parent device
            :type parent_device: blivet.Device
            :returns: new (valid) name
            :rtype: str

        """

        if not name:

            if parent_device:
                name = self.storage.suggestDeviceName(parent=parent_device,
                    swap=False)

            else:
                name = self.storage.suggestContainerName(
                    hostname=socket.gethostname())

        else:
            name = self.storage.safeDeviceName(name)

            # if name exists add -XX suffix
            if name in self.storage.names:
                for i in range(100):
                    if name + "-" + str(i) not in self.storage.names:
                        name = name + "-" + str(i)
                        break

            # if still exists let blivet pick it
            if name in self.storage.names:
                name = _pick_device_name(name=None, parent_device=parent_device)

        return name

    def add_device(self, user_input):
        """ Create new device

            :param user_input: selected parameters from AddDialog
            :type user_input: class UserInput
            :returns: new device name
            :rtype: str

        """

        device_id = None

        if user_input.device_type == "partition":

            if user_input.encrypt:
                dev = self.storage.newPartition(size=user_input.size,
                    parents=[i[0] for i in user_input.parents])

                self.storage.createDevice(dev)

                fmt = blivet.formats.getFormat(fmt_type="luks",
                    passphrase=user_input.passphrase, device=dev.path)

                self.storage.formatDevice(dev, fmt)

                luks_dev = blivet.devices.LUKSDevice("luks-%s" % dev.name,
                    fmt=blivet.formats.getFormat(user_input.filesystem,
                        device=dev.path), size=dev.size, parents=[dev])

                self.storage.createDevice(luks_dev)

                device_id = luks_dev.id

            else:

                # extreme situation -- we have 3 primary partitions and trying to add 4th
                # partition with same size as current free space on disk, blivet creates
                # extened partition and tries to create logical partition with same size
                # and fails -- in this situation we need to reserve 2 MiB for the extended
                # partition

                extended = False

                disk = user_input.parents[0][0]
                size_diff = self.storage.getFreeSpace(disks=[disk])[disk.name][0] - user_input.size

                if user_input.parents[0][0].kids == 3 and size_diff < blivet.Size("2 MiB"):
                    for child in self.storage.devicetree.getChildren(user_input.parents[0][0]):
                        if hasattr(child, "isExtended") and child.isExtended:
                            extended = True
                            break

                    if not extended:
                        user_input.size = user_input.size - blivet.Size("2 MiB")

                new_part = self.storage.newPartition(size=user_input.size,
                    parents=[i[0] for i in user_input.parents],
                    partType=PARTITION_TYPE[user_input.advanced["parttype"]])

                self.storage.createDevice(new_part)

                device_id = new_part.id

                if user_input.advanced["parttype"] == "extended":
                    pass

                else:
                    new_fmt = blivet.formats.getFormat(user_input.filesystem,
                        device=new_part.path, label=user_input.label,
                        mountpoint=user_input.mountpoint)

                    self.storage.formatDevice(new_part, new_fmt)

        elif user_input.device_type == "lvm" and not user_input.encrypt:

            device_name = self._pick_device_name(user_input.name)

            pvs = []

            # exact total size of newly created pvs (future parents)
            total_size = blivet.Size("0 MiB")

            for parent, size in user_input.parents:

                new_part = self.storage.newPartition(size=size,
                    parents=[parent])

                self.storage.createDevice(new_part)

                new_fmt = blivet.formats.getFormat("lvmpv", device=new_part.path)
                self.storage.formatDevice(new_part, new_fmt)

                total_size += new_part.size

                # we need to try to create pvs immediately, if something
                # fails, fail now
                try:
                    blivet.partitioning.doPartitioning(self.storage)

                except blivet.errors.PartitioningError as e:

                    message_dialogs.ExceptionDialog(self.main_window,
                        str(e), traceback.format_exc())

                    return None

                pvs.append(new_part)

            new_vg = self.storage.newVG(size=total_size, parents=pvs,
                name=device_name, peSize=user_input.advanced["pesize"])

            self.storage.createDevice(new_vg)

            device_id = new_vg.id

        elif user_input.device_type == "lvm" and user_input.encrypt:

            device_name = self._pick_device_name(user_input.name)

            lukses = []

            # exact total size of newly created pvs (future parents)
            total_size = blivet.Size("0 MiB")

            for parent, size in user_input.parents:

                dev = self.storage.newPartition(size=size,
                    parents=parent)

                self.storage.createDevice(dev)

                fmt = blivet.formats.getFormat(fmt_type="luks",
                    passphrase=user_input.passphrase, device=dev.path)

                self.storage.formatDevice(dev, fmt)

                luks_dev = blivet.devices.LUKSDevice("luks-%s" % dev.name,
                    fmt=blivet.formats.getFormat("lvmpv", device=dev.path),
                    size=dev.size, parents=[dev])

                self.storage.createDevice(luks_dev)

                total_size += luks_dev.size

                # we need to try to create pvs immediately, if something
                # fails, fail now
                try:
                    blivet.partitioning.doPartitioning(self.storage)

                except blivet.errors.PartitioningError as e:

                    message_dialogs.ExceptionDialog(self.main_window,
                        str(e), traceback.format_exc())

                    return None

                lukses.append(luks_dev)

            new_vg = self.storage.newVG(size=total_size, parents=lukses,
                name=device_name, peSize=user_input.advanced["pesize"])

            self.storage.createDevice(new_vg)

            device_id = new_vg.id

        elif user_input.device_type == "lvmlv":

            device_name = self._pick_device_name(user_input.name,
                user_input.parents[0][0])

            new_part = self.storage.newLV(size=user_input.size,
                parents=[i[0] for i in user_input.parents], name=device_name)

            device_id = new_part.id

            self.storage.createDevice(new_part)

            new_fmt = blivet.formats.getFormat(user_input.filesystem,
                device=new_part.path, label=user_input.label,
                mountpoint=user_input.mountpoint)

            self.storage.formatDevice(new_part, new_fmt)

        elif user_input.device_type == "lvmvg":

            device_name = self._pick_device_name(user_input.name)

            new_part = self.storage.newVG(size=user_input.size,
                parents=[i[0] for i in user_input.parents], name=device_name,
                peSize=user_input.advanced["pesize"])

            device_id = new_part.id

            self.storage.createDevice(new_part)

        elif user_input.device_type == "lvmpv":

            if user_input.encrypt:
                dev = self.storage.newPartition(size=user_input.size,
                    parents=[i[0] for i in user_input.parents])

                self.storage.createDevice(dev)

                fmt = blivet.formats.getFormat(fmt_type="luks",
                    passphrase=user_input.passphrase, device=dev.path)

                self.storage.formatDevice(dev, fmt)

                luks_dev = blivet.devices.LUKSDevice("luks-%s" % dev.name,
                    fmt=blivet.formats.getFormat("lvmpv", device=dev.path),
                    size=dev.size, parents=[dev])

                self.storage.createDevice(luks_dev)

                device_id = luks_dev.id

            else:
                new_part = self.storage.newPartition(size=user_input.size,
                    parents=[i[0] for i in user_input.parents])

                device_id = new_part.id

                self.storage.createDevice(new_part)

                new_fmt = blivet.formats.getFormat("lvmpv", device=new_part.path)
                self.storage.formatDevice(new_part, new_fmt)

        elif user_input.device_type == "btrfs volume":

            device_name = self._pick_device_name(user_input.name)

            # for btrfs we need to create parents first -- currently selected "parents" are
            # disks but "real parents" for subvolume are btrfs formatted partitions
            btrfs_parents = []

            # exact total size of newly created partitions (future parents)
            total_size = blivet.Size("0 MiB")

            for parent, size in user_input.parents:

                if user_input.btrfs_type == "disks":
                    assert parent.isDisk

                    if parent.format:
                        self.delete_disk_label(parent)

                    new_label = blivet.formats.getFormat("btrfs", device=parent.path)

                    try:
                        self.storage.formatDevice(parent, new_label)

                    except Exception as e:
                        message_dialogs.ExceptionDialog(self.main_window,
                            str(e), traceback.format_exc())

                        return None

                    total_size += size

                    btrfs_parents.append(parent)

                else:

                    new_part = self.storage.newPartition(size=size, parents=[parent])

                    self.storage.createDevice(new_part)

                    new_fmt = blivet.formats.getFormat("btrfs", device=new_part.path)
                    self.storage.formatDevice(new_part, new_fmt)

                    total_size += new_part.size

                    # we need to try to create partitions immediately, if something
                    # fails, fail now
                    try:
                        blivet.partitioning.doPartitioning(self.storage)

                    except blivet.errors.PartitioningError as e:

                        message_dialogs.ExceptionDialog(self.main_window,
                            str(e), traceback.format_exc())

                        return None

                    btrfs_parents.append(new_part)

            new_btrfs = self.storage.newBTRFS(size=total_size,
                parents=btrfs_parents, name=device_name)

            self.storage.createDevice(new_btrfs)

            device_id = new_btrfs.id

        elif user_input.device_type == "btrfs subvolume":

            device_name = self._pick_device_name(user_input.name,
                user_input.parents[0][0])

            new_btrfs = self.storage.newBTRFSSubVolume(parents=[i[0] for i in user_input.parents],
                name=device_name)

            self.storage.createDevice(new_btrfs)

            device_id = new_btrfs.id

        elif user_input.device_type == "mdraid":
            device_name = self._pick_device_name(user_input.name)

            parts = []

            # exact total size of newly created pvs (future parents)
            total_size = blivet.Size("0 MiB")

            for parent, size in user_input.parents:

                new_part = self.storage.newPartition(size=size,
                    parents=[parent])

                self.storage.createDevice(new_part)

                new_fmt = blivet.formats.getFormat("mdmember", device=new_part.path)
                self.storage.formatDevice(new_part, new_fmt)

                total_size += new_part.size

                # we need to try to create pvs immediately, if something
                # fails, fail now
                try:
                    blivet.partitioning.doPartitioning(self.storage)

                except blivet.errors.PartitioningError as e:

                    message_dialogs.ExceptionDialog(self.main_window,
                        str(e), traceback.format_exc())

                    return None

                parts.append(new_part)

            new_md = self.storage.newMDArray(size=total_size, parents=parts,
                name=device_name, level=user_input.raid_level,
                fmt_type=user_input.filesystem, memberDevices=len(parts),
                totalDevices=len(parts))

            self.storage.createDevice(new_md)

            device_id = new_md.id


        try:

            blivet.partitioning.doPartitioning(self.storage)

            return self.storage.devicetree.getDeviceByID(device_id)

        except Exception as e:

            message_dialogs.ExceptionDialog(self.main_window, str(e),
                traceback.format_exc())

            return None

    def add_lvmvg_parent(self, container, parent):
        """ Add new parent to existing lvmg

            :param container: existing lvmvg
            :type container: class blivet.LVMVolumeGroupDevice
            :param parent: new parent -- existing device or free space
            :type parent: class blivet.Device or class blivetgui.utils.FreeSpaceDevice

        """

        assert container.type == "lvmvg"

        if parent.type == "free space":
            new_part = self.storage.newPartition(size=parent.size,
                    parents=parent.parents)

            self.storage.createDevice(new_part)

            new_fmt = blivet.formats.getFormat("lvmpv", device=new_part.path)
            self.storage.formatDevice(new_part, new_fmt)

            blivet.partitioning.doPartitioning(self.storage)

            parent = new_part

        try:
            ac = blivet.deviceaction.ActionAddMember(container, parent)
            self.storage.devicetree.registerAction(ac)

        except Exception as e:

            message_dialogs.ExceptionDialog(self.main_window, str(e),
                traceback.format_exc())

    def get_device_type(self, blivet_device):
        """ Get device type

            :param blivet_device: blivet device
            :type device_name: blivet.Device
            :returns: type of device
            :rtype: str

        """

        assert blivet_device != None

        if blivet_device.type == "partition" and blivet_device.format.type == "lvmpv":
            return "lvmpv"

        return blivet_device.type

    def get_blivet_device(self, device_name):
        """ Get blivet device by name

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

        assert blivet_device.type == "lvmvg"

        return blivet_device.pvs

    def get_actions(self):
        """ Return list of currently registered actions

            :returns: list of actions
            :rtype: list of class blivet.deviceaction.DeviceAction

        """

        return self.storage.devicetree.findActions()

    def has_extended_partition(self, blivet_device):

        if not blivet_device.isDisk:
            return False

        extended = False

        for child in self.storage.devicetree.getChildren(blivet_device):
            if child.type == "partition" and child.isExtended:
                extended = True

        return extended

    def has_disklabel(self, blivet_device):
        """ Has this disk device disklabel

            :param blivet_device: blivet device
            :type blivet_device: blivet.Device
            :returns: true/false
            :rtype: bool

        """

        assert blivet_device.type == "disk"

        return blivet_device.format.type == "disklabel"

    def get_available_disklabels(self):
        """ Return disklabels available on current platform

            :returns: list of disklabel types
            :rtype: list of str

        """
        return blivet.platform.getPlatform().diskLabelTypes

    def get_available_raid_levels(self):
        """ Return dict of supported raid levels for device types
        """

        rl = {}
        rl["btrfs volume"] = blivet.devicefactory.get_supported_raid_levels(blivet.devicefactory.DEVICE_TYPE_BTRFS)
        rl["mdraid"] = blivet.devicefactory.get_supported_raid_levels(blivet.devicefactory.DEVICE_TYPE_MD)

        return rl

    def create_disk_label(self, blivet_device, label_type):
        """ Create disklabel

            :param blivet_device: blivet device
            :type blivet_device: blivet.Device
            :param label_type: type of label to create
            :type label_type: str

        """

        assert blivet_device.isDisk

        new_label = blivet.formats.getFormat("disklabel",
            device=blivet_device.path, labelType=label_type)

        self.storage.formatDevice(blivet_device, new_label)

    def set_bootloader_device(self, disk_name):

        blivet_device = self.storage.devicetree.getDeviceByName(disk_name)

        assert blivet_device.isDisk

        self.ksparser.handler.bootloader.location = "mbr"
        self.ksparser.handler.bootloader.bootDrive = disk_name

        self.storage.ksdata = self.ksparser.handler

    def kickstart_mountpoints(self):

        # delete existing mountpoints from devicetree and save them for future use
        old_mountpoints = {}

        for mountpoint in self.storage.mountpoints.values():
            old_mountpoints[mountpoint.format.uuid] = mountpoint.format.mountpoint
            mountpoint.format.mountpoint = None
            mountpoint.format._mountpoint = None

        # set swaps to non-existent in order to set their status to False
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

        except blivet.errors.CryptoError as e:

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

    def create_kickstart_file(self, fname):
        """ Create kickstart config file
        """

        self.storage.updateKSData()

        outfile = open(fname, 'w')
        outfile.write(self.storage.ksdata.__str__())
        outfile.close()
