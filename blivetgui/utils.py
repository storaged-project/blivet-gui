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

from __future__ import print_function

import blivet

from blivet.devices import PartitionDevice, LUKSDevice, LVMVolumeGroupDevice, LVMLogicalVolumeDevice, BTRFSVolumeDevice, BTRFSSubVolumeDevice, MDRaidArrayDevice, LVMSnapShotDevice

from  .blivetguiproxy.proxy_utils import ProxyDataContainer

from gi.overrides import BlockDev

import gettext

import socket, platform, re

import six

import traceback
import parted

import atexit

import pykickstart.parser
from pykickstart.version import makeVersion

from .logs import set_logging, set_python_meh, remove_logs

#------------------------------------------------------------------------------#

_ = lambda x: gettext.translation("blivet-gui", fallback=True).gettext(x) if x != "" else ""

#------------------------------------------------------------------------------#

PARTITION_TYPE = {"primary" : parted.PARTITION_NORMAL,
                  "logical" : parted.PARTITION_LOGICAL,
                  "extended" : parted.PARTITION_EXTENDED}

#------------------------------------------------------------------------------#

class RawFormatDevice(object):
    """ Special class to represent formatted disk without a disklabel
    """

    def __init__(self, disk, fmt):
        self.disk = disk
        self.format = fmt

        self.type = self.format.type
        self.size = self.disk.size

        self.isLogical = False
        self.isFreeSpace = False
        self.isDisk = False
        self.isleaf = True

        self.kids = 0
        self.parents = blivet.devices.lib.ParentList(items=[self.disk])

        if hasattr(self.format, "label") and self.format.label:
            self.name = self.format.label

        else:
            self.name = _("{0} disklabel").format(self.type)

#------------------------------------------------------------------------------#

class FreeSpaceDevice(object):
    """ Special class to represent free space on disk (device)
        (blivet doesn't have class/device to represent free space)
    """

    def __init__(self, free_size, start, end, parents, logical=False):
        """

        :param free_size: size of free space
        :type free_size: blivet.size.Size
        :param start: start block
        :type end: int
        :param end: end block
        :type end: int
        :param parents: list of parent devices
        :type parents: blivet.devices.lib.ParentList
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
        self.parents = blivet.devices.lib.ParentList(items=parents)

    @property
    def isEmptyDisk(self):
        return len(self.parents) == 1 and self.parents[0].type == "disk" and \
            self.parents[0].kids == 0 and self.parents[0].format.type and \
            self.parents[0].format.type not in ("iso9660",)

    @property
    def isUnitializedDisk(self):
        return len(self.parents) == 1 and self.parents[0].type == "disk" and \
            self.parents[0].kids == 0 and self.parents[0].format.type == None

    @property
    def isFreeRegion(self):
        return not (self.isEmptyDisk or self.isUnitializedDisk)

    def __str__(self):
        return "existing " + str(self.size) + " free space"

#------------------------------------------------------------------------------#

class BlivetUtils(object):
    """ Class with utils directly working with blivet itselves
    """

    def __init__(self, kickstart=False):

        if kickstart:
            self.ksparser = pykickstart.parser.KickstartParser(makeVersion())
            self.storage = blivet.Blivet(ksdata=self.ksparser.handler)
        else:
            self.storage = blivet.Blivet()

        self.blivet_logfile, self.program_logfile = self.set_logging()

        blivet.formats.fs.NTFS._formattable = True

        self.storage.reset()
        self._update_min_sizes_info()

    def set_logging(self):
        """ Set logging for blivet-gui-daemon process
        """

        blivet_logfile, _blivet_log = set_logging(component="blivet")
        program_logfile, _program_log = set_logging(component="program")

        atexit.register(remove_logs, log_files=[blivet_logfile, program_logfile])

        return blivet_logfile, program_logfile

    def set_meh(self, client_logfile, communication_logfile):
        """ Set python-meh for blivet-gui-daemon process
        """

        handler = set_python_meh(log_files=[self.blivet_logfile, self.program_logfile,
                                            client_logfile, communication_logfile])
        handler.install(self.storage)

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

    def get_free_pvs_info(self):
        """ Return list of PVs without VGs

            :returns: list of free PVs with name and size
            :rtype: tuple

        """

        pvs = self.storage.pvs

        free_pvs = []

        for pv in pvs:
            if pv.kids == 0:
                free_pvs.append((pv, FreeSpaceDevice(pv.size, None, None, pv.parents)))

        return free_pvs

    def get_vg_free(self, blivet_device):
        """ Return FreeSpaceDevice for selected LVM VG
        """

        assert blivet_device.type == "lvmvg"

        return FreeSpaceDevice(blivet_device.freeSpace, None, None, [blivet_device])

    def get_free_disks_regions(self):
        """ Returns list of non-empty disks with free space
        """

        free_disks = []

        for disk in self.storage.disks:

            if disk.format.type not in ("disklabel", None):
                continue

            elif not disk.format.type:
                free_disks.append(FreeSpaceDevice(disk.size, 0, disk.partedDevice.length, [disk]))
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

                free_size = blivet.size.Size(free.length * free.device.sectorSize)

                if free_size > blivet.size.Size("2 MiB"):
                    free_disks.append(FreeSpaceDevice(free_size, free.start, free.end, [disk]))

        return free_disks

    def get_removable_pvs_info(self, blivet_device):

        assert blivet_device.type == "lvmvg"

        pvs = []

        if len(blivet_device.parents) == 1:
            return pvs

        for parent in blivet_device.parents:
            if int((parent.size-parent.format.peStart) / blivet_device.peSize) <= blivet_device.freeExtents:
                pvs.append(parent)

        return pvs

    def _get_free_space(self, blivet_device, partitions):
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

        elif blivet_device.isDisk and blivet_device.format.type not in ("disklabel",):
            # LiveUSB or btrfs/mdraid partition table, no free space here
            pass

        elif blivet_device.isDisk:

            extended = None
            logicals = []

            for partition in partitions:
                if hasattr(partition, "isExtended") and partition.isExtended:
                    extended = partition

                if hasattr(partition, "isLogical") and partition.isLogical:
                    logicals.append(partition)

            free_space = blivet.partitioning.getFreeRegions([blivet_device])

            if len(free_space) == 0:
                # no free space
                return partitions

            for free in free_space:
                if free.length < 4096:
                    # too small to be usable
                    continue

                free_size = blivet.size.Size(free.length * free.device.sectorSize)

                # free space is inside extended partition
                if (extended and free.start >= extended.partedPartition.geometry.start
                    and free.end <= extended.partedPartition.geometry.end):

                    if logicals:
                        for logical in logicals:
                            if free.start < logical.partedPartition.geometry.start:
                                partitions.insert(partitions.index(logical),
                                                  FreeSpaceDevice(free_size, free.start, free.end,
                                                                  [blivet_device], True))
                                break

                        if free.end > logicals[-1].partedPartition.geometry.end:
                            partitions.append(FreeSpaceDevice(free_size, free.start, free.end,
                                                                  [blivet_device], True))

                    else:
                        partitions.insert(partitions.index(extended),
                                          FreeSpaceDevice(free_size, free.start, free.end,
                                                          [blivet_device], True))
                else:
                    added = False
                    for partition in partitions:
                        if partition.type in ("free space",):
                            continue

                        if free.start < partition.partedPartition.geometry.start:
                            partitions.insert(partitions.index(partition),
                                              FreeSpaceDevice(free_size, free.start, free.end,
                                                              [blivet_device], False))
                            added = True
                            break

                    if not added:
                        partitions.append(FreeSpaceDevice(free_size, free.start, free.end,
                                                          [blivet_device], False))

        elif blivet_device.type == "lvmvg":

            if blivet_device.freeSpace > blivet.size.Size(0):
                partitions.append(FreeSpaceDevice(blivet_device.freeSpace, None, None,
                    [blivet_device]))

        elif blivet_device.type in ("partition", "luks/dm-crypt", "mdarray"):
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

        if blivet_device.isDisk and blivet_device.format \
            and blivet_device.format.type not in ("disklabel", "btrfs", None):
            # special occasion -- raw device format
            return [RawFormatDevice(disk=blivet_device, fmt=blivet_device.format)]

        partitions = []
        partitions = self.storage.devicetree.getChildren(blivet_device)

        if blivet_device.isDisk and blivet_device.format.type in ("disklabel",):
            partitions.sort(key=lambda x: x.partedPartition.geometry.start)

        partitions = self._get_free_space(blivet_device, partitions)

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
            self.storage.devicetree.registerAction(action)

        except Exception as e: # pylint: disable=broad-except
            return ProxyDataContainer(success=False, actions=None, message=None, exception=e,
                              traceback=traceback.format_exc())

        return ProxyDataContainer(success=True, actions=[action], message=None, exception=None,
                          traceback=None)

    def delete_device(self, blivet_device):
        """ Delete device

            :param blivet_device: blivet device
            :type blivet_device: blivet.Device

        """

        actions = []

        if isinstance(blivet_device, RawFormatDevice):
            # raw device, not going to delete device but destroy disk format instead
            result = self.delete_disk_label(blivet_device.parents[0])

            return result

        try:
            if blivet_device.type in ("partition", "lvmlv") and blivet_device.format.type:
                ac_fmt = blivet.deviceaction.ActionDestroyFormat(blivet_device)
                self.storage.devicetree.registerAction(ac_fmt)
                actions.append(ac_fmt)

            ac_dev = blivet.deviceaction.ActionDestroyDevice(blivet_device)
            self.storage.devicetree.registerAction(ac_dev)
            actions.append(ac_dev)

        except Exception as e: # pylint: disable=broad-except
            return ProxyDataContainer(success=False, actions=None, message=None, exception=e,
                              traceback=traceback.format_exc())

        # for encrypted partitions/lvms delete the luks-formatted partition too
        if blivet_device.type in ("luks/dm-crypt",):
            for parent in blivet_device.parents:
                assert parent.type == "partition" and parent.format.type == "luks"

                # teardown parent before
                try:
                    parent.teardown()

                except blivet.errors.CryptoError:
                    msg = _("Failed to remove device {0}. Are you sure it is not in use?").format(parent.name)

                    # cancel destroy action for luks device
                    self.blivet_cancel_actions(actions)
                    return ProxyDataContainer(success=False, actions=None, message=msg, exception=None,
                                      traceback=traceback.format_exc())

                actions.extend(self.delete_device(parent))

        # for btrfs volumes delete parents partition after deleting volume
        if blivet_device.type in ("btrfs volume", "mdarray"):
            for parent in blivet_device.parents:
                if parent.type == "partition":
                    actions.extend(self.delete_device(parent))
                elif parent.type == "disk":
                    result = self.delete_disk_label(parent)

                    if not result.success:
                        return result
                    else:
                        actions.append(result.actions)

        return ProxyDataContainer(success=True, actions=actions,
                          message=None, exception=None, traceback=None)

    def _has_snapshots(self, blivet_device):

        for lvs in self.storage.devicetree.getChildren(blivet_device.vg):
            if isinstance(lvs, LVMSnapShotDevice) and lvs.origin == blivet_device:
                return True

        return False

    def _update_min_sizes_info(self):
        """ Update information of minimal size for resizable devices
        """

        for device in self.storage.devices:
            if device.type in ("partition", "lvmlv"):
                if device.format and device.format.type and hasattr(device.format, "updateSizeInfo"):
                    try:
                        device.format.updateSizeInfo()
                    except blivet.errors.FSError:
                        pass

    def device_resizable(self, blivet_device):
        """ Is given device resizable

            :param blivet_device: blivet device
            :type blivet_device: blivet.Device
            :returns: device resizable, minSize, maxSize, size
            :rtype: tuple

        """

        if blivet_device.format.type in (None, "swap") or not blivet_device.format.exists:
            return ProxyDataContainer(resizable=False, error=None, min_size=blivet.size.Size("1 MiB"),
                                      max_size=blivet_device.size)

        if blivet_device.type in ("lvmlv",) and self._has_snapshots(blivet_device):
            msg = _("Logical Volumes with snapshots couldn't be resized.")
            return ProxyDataContainer(resizable=False, error=msg, min_size=blivet.size.Size("1 MiB"),
                                      max_size=blivet_device.size)

        try:
            blivet_device.format.updateSizeInfo()

        except blivet.errors.FSError as e:
            if six.PY2:
                exc = unicode(e).encode("utf8")
            else:
                exc = str(e)

            return ProxyDataContainer(resizable=False, error=exc,
                              min_size=blivet.size.Size("1 MiB"),
                              max_size=blivet_device.size)

        if blivet_device.resizable and blivet_device.format.resizable:
            return ProxyDataContainer(resizable=True, error=None, min_size=blivet_device.minSize,
                              max_size=blivet_device.maxSize)

        else:
            return ProxyDataContainer(resizable=False, error=None, min_size=blivet.size.Size("1 MiB"),
                              max_size=blivet_device.size)

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
        actions = []

        if user_input.mountpoint:
            blivet_device.format.mountpoint = user_input.mountpoint

        if not user_input.resize and not user_input.fmt:
            return ProxyDataContainer(success=True, actions=None, message=None, exception=None,
                              traceback=None)

        if user_input.resize:
            actions.append(blivet.deviceaction.ActionResizeFormat(blivet_device, user_input.size))
            actions.append(blivet.deviceaction.ActionResizeDevice(blivet_device, user_input.size))

        if user_input.fmt:
            new_fmt = blivet.formats.getFormat(user_input.filesystem, mountpoint=user_input.mountpoint)
            actions.append(blivet.deviceaction.ActionCreateFormat(blivet_device, new_fmt))

        try:
            for ac in actions:
                self.storage.devicetree.registerAction(ac)
            blivet.partitioning.doPartitioning(self.storage)
            return ProxyDataContainer(success=True, actions=actions,
                              message=None, exception=None, traceback=None)

        except Exception as e: # pylint: disable=broad-except
            return ProxyDataContainer(success=False, actions=None, message=None, exception=e,
                              traceback=traceback.format_exc())

    def edit_lvmvg_device(self, user_input):
        """ Edit LVM Volume group
        """

        actions = []

        if user_input.action_type == "add":
            for parent in user_input.parents_list:
                result = self._add_lvmvg_parent(user_input.edit_device, parent)

                if result.success:
                    actions.extend(result.actions)

                else:
                    return result

        elif user_input.action_type == "remove":
            for parent in user_input.parents_list:
                result = self._remove_lvmvg_parent(user_input.edit_device, parent)

                if result.success:
                    actions.extend(result.actions)

                else:
                    return result

        return ProxyDataContainer(success=True, actions=actions,
                          message=None, exception=None, traceback=None)

    def _pick_device_name(self, name, parent_device=None, snapshot=False):
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
                name = self.storage.suggestDeviceName(parent=parent_device, swap=False)

            elif snapshot:
                name = self.storage.suggestDeviceName(parent=parent_device, swap=False,
                                                      prefix="snapshot")

            else:

                if hasattr(platform, "linux_distribution"):
                    prefix = re.sub(r"\W+", "", platform.linux_distribution()[0].lower())
                else:
                    prefix = ""

                name = self.storage.suggestContainerName(hostname=socket.gethostname(),
                                                         prefix=prefix)

        else:
            name = self.storage.safeDeviceName(name)

            # if name exists add -XX suffix
            if name in self.storage.names or (parent_device and
                                              parent_device.name + "-" + name in self.storage.names):
                for i in range(100):
                    if name + "-" + str(i) not in self.storage.names:
                        name = name + "-" + str(i)
                        break

            # if still exists let blivet pick it
            if name in self.storage.names:
                name = self._pick_device_name(name=None, parent_device=parent_device)

        return name

    def add_device(self, user_input):
        """ Create new device

            :param user_input: selected parameters from AddDialog
            :type user_input: class UserInput
            :returns: new device name
            :rtype: str

        """

        actions = []

        if user_input.device_type == "partition":

            if user_input.encrypt:
                dev = PartitionDevice(name="req%d" % self.storage.nextID,
                    size=user_input.size,
                    parents=[i[0] for i in user_input.parents])
                actions.append(blivet.deviceaction.ActionCreateDevice(dev))

                fmt = blivet.formats.getFormat(fmt_type="luks", passphrase=user_input.passphrase, device=dev.path)
                actions.append(blivet.deviceaction.ActionCreateFormat(dev, fmt))

                luks_dev = LUKSDevice("luks-%s" % dev.name, size=dev.size, parents=[dev])
                actions.append(blivet.deviceaction.ActionCreateDevice(luks_dev))

                luks_fmt = blivet.formats.getFormat(fmt_type=user_input.filesystem, device=dev.path, mountpoint=user_input.mountpoint)
                actions.append(blivet.deviceaction.ActionCreateFormat(luks_dev, luks_fmt))

            else:
                new_part = PartitionDevice(name="req%d" % self.storage.nextID,
                    size=user_input.size, parents=[i[0] for i in user_input.parents],
                    partType=PARTITION_TYPE[user_input.advanced["parttype"]])

                actions.append(blivet.deviceaction.ActionCreateDevice(new_part))

                if user_input.advanced["parttype"] != "extended":
                    new_fmt = blivet.formats.getFormat(fmt_type=user_input.filesystem,
                        label=user_input.label, mountpoint=user_input.mountpoint)

                    actions.append(blivet.deviceaction.ActionCreateFormat(new_part, new_fmt))

        elif user_input.device_type == "lvm" and not user_input.encrypt:

            device_name = self._pick_device_name(user_input.name)

            pvs = []

            # exact total size of newly created pvs (future parents)
            total_size = blivet.size.Size("0 MiB")

            for parent, size in user_input.parents:

                dev = PartitionDevice(name="req%d" % self.storage.nextID,
                    size=size, parents=parent)
                ac_part = blivet.deviceaction.ActionCreateDevice(dev)

                fmt = blivet.formats.getFormat(fmt_type="lvmpv")
                ac_fmt = blivet.deviceaction.ActionCreateFormat(dev, fmt)

                actions.extend([ac_part, ac_fmt])

                total_size += dev.size

                # we need to try to create pvs immediately, if something
                # fails, fail now
                try:
                    for ac in (ac_part, ac_fmt):
                        self.storage.devicetree.registerAction(ac)

                except blivet.errors.PartitioningError as e:
                    return ProxyDataContainer(success=False, actions=None, message=None, exception=e,
                                      traceback=traceback.format_exc())

                pvs.append(dev)

            new_vg = LVMVolumeGroupDevice(size=total_size, parents=pvs,
                name=device_name, peSize=user_input.advanced["pesize"])

            actions.append(blivet.deviceaction.ActionCreateDevice(new_vg))

        elif user_input.device_type == "lvm" and user_input.encrypt:

            device_name = self._pick_device_name(user_input.name)

            lukses = []

            # exact total size of newly created pvs (future parents)
            total_size = blivet.size.Size("0 MiB")

            for parent, size in user_input.parents:
                dev = PartitionDevice(name="req%d" % self.storage.nextID,
                    size=user_input.size,
                    parents=[parent])
                ac_part = blivet.deviceaction.ActionCreateDevice(dev)

                fmt = blivet.formats.getFormat(fmt_type="luks", passphrase=user_input.passphrase, device=dev.path)
                ac_fmt = blivet.deviceaction.ActionCreateFormat(dev, fmt)

                luks_dev = LUKSDevice("luks-%s" % dev.name,
                    fmt=blivet.formats.getFormat("lvmpv", device=dev.path),
                    size=dev.size, parents=[dev])
                ac_luks = blivet.deviceaction.ActionCreateDevice(luks_dev)

                actions.extend([ac_part, ac_fmt, ac_luks])

                total_size += luks_dev.size

                # we need to try to create pvs immediately, if something
                # fails, fail now
                try:
                    for ac in (ac_part, ac_fmt, ac_luks):
                        self.storage.devicetree.registerAction(ac)

                except blivet.errors.PartitioningError as e:
                    return ProxyDataContainer(success=False, actions=None, message=None, exception=e,
                                      traceback=traceback.format_exc())

                lukses.append(luks_dev)

            new_vg = LVMVolumeGroupDevice(size=total_size, parents=lukses,
                name=device_name, peSize=user_input.advanced["pesize"])

            actions.append(blivet.deviceaction.ActionCreateDevice(new_vg))

        elif user_input.device_type == "lvmlv":

            device_name = self._pick_device_name(user_input.name,
                user_input.parents[0][0])

            new_part = LVMLogicalVolumeDevice(name=device_name, size=user_input.size,
                parents=[i[0] for i in user_input.parents])

            actions.append(blivet.deviceaction.ActionCreateDevice(new_part))

            new_fmt = blivet.formats.getFormat(fmt_type=user_input.filesystem, mountpoint=user_input.mountpoint)

            actions.append(blivet.deviceaction.ActionCreateFormat(new_part, new_fmt))

        elif user_input.device_type == "lvmvg":

            device_name = self._pick_device_name(user_input.name)

            new_vg = LVMVolumeGroupDevice(size=user_input.size, name=device_name,
                parents=[i[0] for i in user_input.parents],
                peSize=user_input.advanced["pesize"])

            actions.append(blivet.deviceaction.ActionCreateDevice(new_vg))

        elif user_input.device_type == "lvmpv":

            if user_input.encrypt:

                dev = PartitionDevice(name="req%d" % self.storage.nextID,
                    size=user_input.size,
                    parents=[i[0] for i in user_input.parents])
                actions.append(blivet.deviceaction.ActionCreateDevice(dev))

                fmt = blivet.formats.getFormat(fmt_type="luks", passphrase=user_input.passphrase, device=dev.path)
                actions.append(blivet.deviceaction.ActionCreateFormat(dev, fmt))

                luks_dev = LUKSDevice("luks-%s" % dev.name,
                    fmt=blivet.formats.getFormat("lvmpv", device=dev.path),
                    size=dev.size, parents=[dev])
                actions.append(blivet.deviceaction.ActionCreateDevice(luks_dev))

            else:
                dev = PartitionDevice(name="req%d" % self.storage.nextID,
                    size=user_input.size, parents=[i[0] for i in user_input.parents])
                actions.append(blivet.deviceaction.ActionCreateDevice(dev))

                fmt = blivet.formats.getFormat(fmt_type="lvmpv")
                actions.append(blivet.deviceaction.ActionCreateFormat(dev, fmt))

        elif user_input.device_type == "btrfs volume":

            device_name = self._pick_device_name(user_input.name)

            # for btrfs we need to create parents first -- currently selected "parents" are
            # disks but "real parents" for subvolume are btrfs formatted partitions
            btrfs_parents = []

            # exact total size of newly created partitions (future parents)
            total_size = blivet.size.Size("0 MiB")

            for parent, size in user_input.parents:

                if user_input.btrfs_type == "disks":
                    assert parent.isDisk

                    fmt = blivet.formats.getFormat(fmt_type="btrfs")
                    ac_fmt = blivet.deviceaction.ActionCreateFormat(parent, fmt)

                    actions.append(ac_fmt)

                    try:
                        self.storage.devicetree.registerAction(ac_fmt)

                    except Exception as e: # pylint: disable=broad-except
                        return ProxyDataContainer(success=False, actions=None, message=None, exception=e,
                                          traceback=traceback.format_exc())

                    total_size += size
                    btrfs_parents.append(parent)

                else:

                    dev = PartitionDevice(name="req%d" % self.storage.nextID,
                        size=size, parents=[parent])
                    ac_part = blivet.deviceaction.ActionCreateDevice(dev)

                    fmt = blivet.formats.getFormat(fmt_type="btrfs")
                    ac_fmt = blivet.deviceaction.ActionCreateFormat(dev, fmt)

                    actions.extend([ac_part, ac_fmt])

                    total_size += dev.size

                    # we need to try to create partitions immediately, if something
                    # fails, fail now
                    try:
                        for ac in (ac_part, ac_fmt):
                            self.storage.devicetree.registerAction(ac)

                    except blivet.errors.PartitioningError as e:
                        return ProxyDataContainer(success=False, actions=None, message=None, exception=e,
                                          traceback=traceback.format_exc())

                    btrfs_parents.append(dev)

            new_btrfs = BTRFSVolumeDevice(device_name, size=total_size, parents=btrfs_parents)
            new_btrfs.format = blivet.formats.getFormat("btrfs", label=device_name, mountpoint=user_input.mountpoint)
            actions.append(blivet.deviceaction.ActionCreateDevice(new_btrfs))

        elif user_input.device_type == "btrfs subvolume":

            device_name = self._pick_device_name(user_input.name,
                                                 user_input.parents[0][0])

            new_btrfs = BTRFSSubVolumeDevice(device_name, parents=[i[0] for i in user_input.parents])
            new_btrfs.format = blivet.formats.getFormat("btrfs", mountpoint=user_input.mountpoint)
            actions.append(blivet.deviceaction.ActionCreateDevice(new_btrfs))

        elif user_input.device_type == "mdraid":
            device_name = self._pick_device_name(user_input.name)

            parts = []

            # exact total size of newly created pvs (future parents)
            total_size = blivet.size.Size("0 MiB")

            for parent, size in user_input.parents:

                dev = PartitionDevice(name="req%d" % self.storage.nextID,
                    size=size, parents=[parent])
                ac_part = blivet.deviceaction.ActionCreateDevice(dev)

                fmt = blivet.formats.getFormat(fmt_type="mdmember")
                ac_fmt = blivet.deviceaction.ActionCreateFormat(dev, fmt)

                actions.extend([ac_part, ac_fmt])

                total_size += dev.size

                # we need to try to create pvs immediately, if something
                # fails, fail now
                try:
                    for ac in (ac_part, ac_fmt):
                        self.storage.devicetree.registerAction(ac)

                except blivet.errors.PartitioningError as e:
                    return ProxyDataContainer(success=False, actions=None, message=None,
                                      exception=e, traceback=traceback.format_exc())

                parts.append(dev)

            new_md = MDRaidArrayDevice(size=total_size, parents=parts,
                name=device_name, level=user_input.raid_level,
                memberDevices=len(parts), totalDevices=len(parts))
            actions.append(blivet.deviceaction.ActionCreateDevice(new_md))

            fmt = blivet.formats.getFormat(fmt_type=user_input.filesystem)
            actions.append(blivet.deviceaction.ActionCreateFormat(new_md, fmt))

        elif user_input.device_type == "lvm snapshot":
            origin_lv = user_input.parents[0][0]
            snapshot_size = user_input.parents[0][1]

            device_name = self._pick_device_name(user_input.name, origin_lv.parents[0])

            new_snap = LVMSnapShotDevice(name=device_name, parents=[origin_lv.parents[0]],
                                         origin=origin_lv, size=snapshot_size)
            actions.append(blivet.deviceaction.ActionCreateDevice(new_snap))

        try:
            for ac in actions:
                if not ac._applied:
                    self.storage.devicetree.registerAction(ac)

            blivet.partitioning.doPartitioning(self.storage)

        except Exception as e: # pylint: disable=broad-except
            return ProxyDataContainer(success=False, actions=None, message=None,
                                                exception=e, traceback=traceback.format_exc())

        return ProxyDataContainer(success=True, actions=actions,
                                            message=None, exception=None, traceback=None)

    def _remove_lvmvg_parent(self, container, parent):
        """ Add parent fromexisting lvmg

            :param container: existing lvmvg
            :type container: class blivet.LVMVolumeGroupDevice
            :param parent: parent
            :type parent: class blivet.Device

        """

        try:
            ac_rm = blivet.deviceaction.ActionRemoveMember(container, parent)
            self.storage.devicetree.registerAction(ac_rm)

        except Exception as e: # pylint: disable=broad-except
            return ProxyDataContainer(success=False, actions=None, message=None, exception=e,
                              traceback=traceback.format_exc())

        return ProxyDataContainer(success=True, actions=[ac_rm],
                          message=None, exception=None, traceback=None)

    def _add_lvmvg_parent(self, container, parent):
        """ Add new parent to existing lvmg

            :param container: existing lvmvg
            :type container: class blivet.LVMVolumeGroupDevice
            :param parent: new parent -- existing device or free space
            :type parent: class blivet.Device or class blivetgui.utils.FreeSpaceDevice

        """

        assert container.type == "lvmvg"

        actions = []

        if parent.type == "free space":
            dev = PartitionDevice(name="req%d" % self.storage.nextID, size=parent.size,
                                  parents=[i for i in parent.parents])
            ac_part = blivet.deviceaction.ActionCreateDevice(dev)

            fmt = blivet.formats.getFormat(fmt_type="lvmpv")
            ac_fmt = blivet.deviceaction.ActionCreateFormat(dev, fmt)

            actions.extend([ac_part, ac_fmt])

            for ac in (ac_part, ac_fmt):
                self.storage.devicetree.registerAction(ac)

            blivet.partitioning.doPartitioning(self.storage)

            parent = dev

        try:
            ac_add = blivet.deviceaction.ActionAddMember(container, parent)
            self.storage.devicetree.registerAction(ac_add)

            actions.append(ac_add)

        except Exception as e: # pylint: disable=broad-except
            return ProxyDataContainer(success=False, actions=None, message=None, exception=e,
                              traceback=traceback.format_exc())

        return ProxyDataContainer(success=True, actions=actions,
                          message=None, exception=None, traceback=None)

    def unmount_device(self, blivet_device):
        """ Unmount selected device
        """

        if not blivet_device.format.mountable or not blivet_device.format.systemMountpoint:
            return False

        else:
            try:
                blivet_device.format.unmount()
                return True

            except blivet.errors.FSError:
                return False

    def get_actions(self):
        """ Return list of currently registered actions

            :returns: list of actions
            :rtype: list of class blivet.deviceaction.DeviceAction

        """

        actions = self.storage.devicetree.findActions()

        return actions

    def has_extended_partition(self, blivet_device):
        """ Detect if disk has an extended partition
        """

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

    def get_available_raid_levels(self, device_type):
        """ Return dict of supported raid levels for device types
        """

        if device_type == "btrfs volume":
            return blivet.devicefactory.get_supported_raid_levels(blivet.devicefactory.DEVICE_TYPE_BTRFS)

        if device_type == "mdraid":
            return blivet.devicefactory.get_supported_raid_levels(blivet.devicefactory.DEVICE_TYPE_MD)

    def get_mountpoints(self):
        """ Return list of current mountpoints
        """

        return list(self.storage.mountpoints.keys())

    def create_disk_label(self, blivet_device, label_type):
        """ Create disklabel

            :param blivet_device: blivet device
            :type blivet_device: blivet.Device
            :param label_type: type of label to create
            :type label_type: str

        """

        actions = []

        if blivet_device.format.type:
            actions.append(blivet.deviceaction.ActionDestroyFormat(blivet_device))

        new_label = blivet.formats.getFormat("disklabel", device=blivet_device.path,
                                             labelType=label_type)

        actions.append(blivet.deviceaction.ActionCreateFormat(blivet_device, new_label))

        for ac in actions:
            self.storage.devicetree.registerAction(ac)

        return ProxyDataContainer(success=True, actions=actions, message=None,
                          exception=None, traceback=None)

    def set_bootloader_device(self, disk_name):

        blivet_device = self.storage.devicetree.getDeviceByName(disk_name)

        assert blivet_device.isDisk

        self.ksparser.handler.bootloader.location = "mbr"
        self.ksparser.handler.bootloader.bootDrive = disk_name

        self.storage.ksdata = self.ksparser.handler

    def kickstart_mountpoints(self):
        """ delete existing mountpoints from dt and save them for future use
        """

        old_mountpoints = {}

        for mountpoint in self.storage.mountpoints.values():
            old_mountpoints[mountpoint.format.uuid] = mountpoint.format.mountpoint
            mountpoint.format.mountpoint = None
            mountpoint.format._mountpoint = None

        # set swaps to non-existent in order to set their status to False
        for swap in self.storage.swaps:
            swap.format.exists = False

        return ProxyDataContainer(**old_mountpoints)

    def kickstart_hide_disks(self, disk_names):
        """ Hide disks not used in kickstart mode
        """

        for name in disk_names:
            disk_device = self.storage.devicetree.getDeviceByName(name)
            self.storage.devicetree.hide(disk_device)

        self.storage.devicetree.populate()

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

        except BlockDev.CryptoError:
            return False

        else:
            self.storage.devicetree.populate()
            return True


    def blivet_cancel_actions(self, actions):
        """ Cancel scheduled actions
        """

        actions.reverse()

        for action in actions:
            self.storage.devicetree.cancelAction(action)

    def blivet_reset(self):
        """ Blivet.reset()
        """

        self.storage.reset()

    def blivet_do_it(self):
        """ Blivet.doIt()
        """

        try:
            self.storage.doIt()

        except Exception as e: # pylint: disable=broad-except
            return ProxyDataContainer(success=False, exception=e, traceback=traceback.format_exc())

        else:
            return ProxyDataContainer(success=True)

    def create_kickstart_file(self, fname):
        """ Create kickstart config file
        """

        self.storage.updateKSData()

        outfile = open(fname, 'w')
        outfile.write(self.storage.ksdata.__str__())
        outfile.close()
