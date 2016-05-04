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

from blivet.devices import PartitionDevice, LUKSDevice, LVMVolumeGroupDevice, LVMLogicalVolumeDevice, BTRFSVolumeDevice, BTRFSSubVolumeDevice, MDRaidArrayDevice, LVMSnapShotDevice, LVMThinLogicalVolumeDevice, LVMThinPoolDevice
from blivet.formats import DeviceFormat

from  .communication.proxy_utils import ProxyDataContainer

import socket, platform, re
import traceback
import parted

import atexit

import pykickstart.parser
from pykickstart.version import makeVersion

from .logs import set_logging, set_python_meh, remove_logs
from .i18n import _

#------------------------------------------------------------------------------#

PARTITION_TYPE = {"primary" : parted.PARTITION_NORMAL,
                  "logical" : parted.PARTITION_LOGICAL,
                  "extended" : parted.PARTITION_EXTENDED}

#------------------------------------------------------------------------------#

class RawFormatDevice(object):
    """ Special class to represent formatted disk without a disklabel
    """

    def __init__(self, disk, fmt, dev_id):
        self.disk = disk
        self.format = fmt
        self.id = dev_id

        self.type = "raw format"
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

    @property
    def protected(self):
        return self.disk.protected

#------------------------------------------------------------------------------#

class FreeSpaceDevice(object):
    """ Special class to represent free space on disk (device)
        (blivet doesn't have class/device to represent free space)
    """

    def __init__(self, free_size, dev_id, start, end, parents, logical=False):
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
        self.id = dev_id

        self.start = start
        self.end = end

        self.isLogical = logical
        self.isExtended = False
        self.isPrimary = not logical
        self.isFreeSpace = True
        self.isDisk = False

        self.format = DeviceFormat(exists=True)
        self.type = "free space"
        self.kids = 0
        self.parents = blivet.devices.lib.ParentList(items=parents)

        self.disk = self._get_disk()

    def _get_disk(self):
        parents = self.parents

        while parents:
            if parents[0].isDisk:
                return parents[0]

            parents = parents[0].parents

        return None

    @property
    def protected(self):
        return self.parents[0].protected

    @property
    def isEmptyDisk(self):
        return len(self.parents) == 1 and self.parents[0].type == "disk" and \
            self.parents[0].kids == 0 and self.parents[0].format.type and \
            self.parents[0].format.type not in ("iso9660",)

    @property
    def isUninitializedDisk(self):
        return len(self.parents) == 1 and self.parents[0].type == "disk" and \
            self.parents[0].kids == 0 and self.parents[0].format.type == None

    @property
    def isFreeRegion(self):
        return not (self.isEmptyDisk or self.isUninitializedDisk)

    def __str__(self):
        return "existing " + str(self.size) + " free space"

#------------------------------------------------------------------------------#

class BlivetUtils(object):
    """ Class with utils directly working with blivet itselves
    """

    def __init__(self, kickstart=False, test_run=False):

        self.kickstart = kickstart

        if self.kickstart:
            self.ksparser = pykickstart.parser.KickstartParser(makeVersion())
            self.storage = blivet.Blivet(ksdata=self.ksparser.handler)
        else:
            self.storage = blivet.Blivet()

        if not test_run:
            self.blivet_logfile, self.program_logfile = self.set_logging()

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

        devices = {}
        devices["lvm"] = self.storage.vgs
        devices["raid"] = self.storage.mdarrays
        devices["btrfs"] = self.storage.btrfsVolumes

        return devices

    def get_free_pvs_info(self):
        """ Return list of PVs without VGs

            :returns: list of free PVs with name and size
            :rtype: tuple

        """

        pvs = self.storage.pvs

        free_pvs = []

        for pv in pvs:
            if pv.kids == 0:
                free_pvs.append((pv, FreeSpaceDevice(pv.size, self.storage.nextID, None, None, pv.parents)))

        return free_pvs

    def get_vg_free(self, blivet_device):
        """ Return FreeSpaceDevice for selected LVM VG
        """

        if blivet_device.type != "lvmvg":
            return None

        return FreeSpaceDevice(blivet_device.freeSpace, self.storage.nextID, None, None, [blivet_device])

    def get_free_disks_regions(self, include_uninitialized=False):
        """ Returns list of non-empty disks with free space
        """

        free_disks = []

        for disk in self.storage.disks:
            if not disk.format.type and include_uninitialized:
                free_disks.append(FreeSpaceDevice(disk.size, self.storage.nextID, 0, disk.currentSize, [disk]))
                continue

            elif disk.format.type not in ("disklabel",):
                continue

            free_space = blivet.partitioning.getFreeRegions([disk], align=True)

            for free in free_space:
                free_size = blivet.size.Size(free.length * free.device.sectorSize)

                if free_size > blivet.size.Size("2 MiB"):
                    free_disks.append(FreeSpaceDevice(free_size, self.storage.nextID, free.start, free.end, [disk]))

        return free_disks

    def get_removable_pvs_info(self, blivet_device):
        """ Get information about PVs that can be removed from the VG
        """

        pvs = []

        if len(blivet_device.parents) == 1:
            return pvs

        for parent in blivet_device.parents:
            if int((parent.size-parent.format.peStart) / blivet_device.peSize) <= blivet_device.freeExtents:
                pvs.append(parent)

        return pvs

    def get_group_device(self, blivet_device):
        """ Get 'group' device based on underlying device (lvmpv/btrfs/mdmember/luks partition)
        """

        # already a group device
        if blivet_device.type in ("btrfs volume", "lvmvg", "mdarray"):
            return blivet_device

        # encrypted group device -> get the luks device instead
        if blivet_device.format.type == "luks":
            blivet_device = self.get_luks_device(blivet_device)

        if not blivet_device.format or blivet_device.format.type not in ("lvmpv", "btrfs", "mdmember", "luks"):
            return None
        if blivet_device.kids != 1:
            return None

        group_device = self.storage.devicetree.getChildren(blivet_device)[0]
        return group_device

    def get_luks_device(self, blivet_device):
        """ Get luks device based on underlying partition
        """

        if not blivet_device.format or blivet_device.format.type != "luks" or not blivet_device.format.status:
            return None
        if blivet_device.kids != 1:
            return None

        luks_device = self.storage.devicetree.getChildren(blivet_device)[0]
        return luks_device

    def get_children(self, blivet_device):
        """ Get partitions (children) of selected device

            :param blivet_device: blivet device
            :type blivet_device: blivet.device.Device
            :returns: list of child devices
            :rtype: list of blivet.device.Device

        """

        if not blivet_device:
            return []

        childs = self.storage.devicetree.getChildren(blivet_device)

        if blivet_device.type == "lvmvg" and blivet_device.freeSpace > blivet.size.Size(0):
            childs.append(FreeSpaceDevice(blivet_device.freeSpace, self.storage.nextID, None, None, [blivet_device]))

        return childs

    def get_disk_children(self, blivet_device):
        if not blivet_device.isDisk:
            raise TypeError("device %s is not a disk" % blivet_device.name)

        if blivet_device.isDisk and blivet_device.format.type == None:
            # empty disk without disk label
            partitions = [FreeSpaceDevice(blivet_device.size, self.storage.nextID, 0, blivet_device.currentSize, [blivet_device], False)]
            return ProxyDataContainer(partitions=partitions, extended=None, logicals=None)

        if blivet_device.format and blivet_device.format.type not in ("disklabel", "btrfs", "luks", None):
            # special occasion -- raw device format
            partitions =  [RawFormatDevice(disk=blivet_device, fmt=blivet_device.format, dev_id=self.storage.nextID)]
            return ProxyDataContainer(partitions=partitions, extended=None, logicals=None)

        if blivet_device.format and blivet_device.format.type == "btrfs" and blivet_device.kids:
            # btrfs volume on raw device
            btrfs_volume = self.storage.devicetree.getChildren(blivet_device)[0]
            return ProxyDataContainer(partitions=[btrfs_volume], extended=None, logicals=None)

        if blivet_device.format and blivet_device.format.type == "luks":
            if blivet_device.kids:
                luks = self.storage.devicetree.getChildren(blivet_device)[0]
            else:
                luks = RawFormatDevice(disk=blivet_device, fmt=blivet_device.format, dev_id=self.storage.nextID)

            return ProxyDataContainer(partitions=[luks], extended=None, logicals=None)

        # extended partition
        extended = self._get_extended_partition(blivet_device)
        # logical partitions + 'logical' free space
        logicals = self._get_logical_partitions(blivet_device) + self._get_free_logical(blivet_device)
        # primary partitions + 'primary' free space
        primaries = self._get_primary_partitions(blivet_device) + self._get_free_primary(blivet_device)

        def _sort_partitions(part): # FIXME: move to separate 'utils' file
            if not part.type in ("free space", "partition"):
                raise ValueError
            if part.type == "free space":
                return part.start
            else:
                return part.partedPartition.geometry.start

        if extended:
            partitions = sorted(primaries + [extended], key=_sort_partitions)
        else:
            partitions = sorted(primaries, key=_sort_partitions)
        logicals = sorted(logicals, key=_sort_partitions)

        return ProxyDataContainer(partitions=partitions, extended=extended, logicals=logicals)

    def _get_extended_partition(self, blivet_device):
        if not blivet_device.isDisk or not blivet_device.format or blivet_device.format.type != "disklabel":
            return None

        extended = None
        partitions = self.storage.devicetree.getChildren(blivet_device)
        for part in partitions:
            if part.type == "partition" and part.isExtended:
                extended = part
                break # only one extended partition

        return extended

    def _get_logical_partitions(self, blivet_device):
        if not blivet_device.isDisk or not blivet_device.format or blivet_device.format.type != "disklabel":
            return []

        logicals = []
        partitions = self.storage.devicetree.getChildren(blivet_device)
        for part in partitions:
            if part.type == "partition" and part.isLogical:
                logicals.append(part)

        return logicals

    def _get_primary_partitions(self, blivet_device):
        if not blivet_device.isDisk or not blivet_device.format or blivet_device.format.type != "disklabel":
            return []

        primaries = []
        partitions = self.storage.devicetree.getChildren(blivet_device)
        for part in partitions:
            if part.type == "partition" and part.isPrimary:
                primaries.append(part)

        return primaries

    def _get_free_logical(self, blivet_device):
        if not blivet_device.isDisk or not blivet_device.format or blivet_device.format.type != "disklabel":
            return []

        extended = self._get_extended_partition(blivet_device)
        if not extended:
            return []

        free_logical = []

        free_regions = blivet.partitioning.getFreeRegions([blivet_device], align=True)
        for region in free_regions:
            region_size = blivet.size.Size(region.length * region.device.sectorSize)
            if region_size < blivet.size.Size("4 MiB"):
                continue

            if region.start >= extended.partedPartition.geometry.start and \
               region.end <= extended.partedPartition.geometry.end:
                free_logical.append(FreeSpaceDevice(region_size, self.storage.nextID, region.start, region.end, [blivet_device], True))

        return free_logical

    def _get_free_primary(self, blivet_device):
        if not blivet_device.isDisk or not blivet_device.format or blivet_device.format.type != "disklabel":
            return []

        free_primary = []
        free_regions = blivet.partitioning.getFreeRegions([blivet_device], align=True)

        extended = self._get_extended_partition(blivet_device)

        for region in free_regions:
            region_size = blivet.size.Size(region.length * region.device.sectorSize)
            if region_size < blivet.size.Size("4 MiB"):
                continue

            if extended and not (region.start >= extended.partedPartition.geometry.start and \
               region.end <= extended.partedPartition.geometry.end):
                free_primary.append(FreeSpaceDevice(region_size, self.storage.nextID, region.start, region.end, [blivet_device], False))
            elif not extended:
                free_primary.append(FreeSpaceDevice(region_size, self.storage.nextID, region.start, region.end, [blivet_device], False))

        return free_primary

    def get_roots(self, blivet_device):
        """ Get list of parents for selected device with its structure """

        roots = set([])

        if blivet_device.type == "lvmvg":
            for pv in blivet_device.pvs:
                roots.add(self._get_root_device(pv))
        elif blivet_device.type in ("mdarray", "btrfs volume"):
            for member in blivet_device.members:
                roots.add(self._get_root_device(member))
        elif blivet_device.type in ("luks/dm-crypt",):
            roots.add(self._get_root_device(blivet_device.slave))

        return roots

    def _get_root_device(self, blivet_device):
        if blivet_device.isDisk:
            return blivet_device

        elif blivet_device.type in ("mdarray",):
            return blivet_device

        elif blivet_device.type in ("lvmlv", "lvmthinlv"):
            return blivet_device.vg

        elif blivet_device.parents[0].type in ("mdarray", "mdmember"):
            return blivet_device.parents[0]

        elif blivet_device.type in ("luks/dm-crypt",):
            return self._get_root_device(blivet_device.slave)

        else:
            return blivet_device.disk

    def delete_disk_label(self, disk_device):
        """ Delete current disk label

            :param disk_device: blivet device
            :type disk_device: blivet.Device

        """

        try:
            if disk_device.format.exists:
                disk_device.format.teardown()
            action = blivet.deviceaction.ActionDestroyFormat(disk_device)
            self.storage.devicetree.registerAction(action)

        except Exception as e: # pylint: disable=broad-except
            return ProxyDataContainer(success=False, actions=None, message=None, exception=e,
                                      traceback=traceback.format_exc())

        return ProxyDataContainer(success=True, actions=[action], message=None, exception=None, traceback=None)

    def delete_device(self, blivet_device):
        """ Delete device

            :param blivet_device: blivet device
            :type blivet_device: blivet.Device

        """

        actions = []

        # in kickstart mode set formats to non-existing to be able to remove them
        if self.kickstart and blivet_device.format.type:
            blivet_device.format.exists = False

        if isinstance(blivet_device, RawFormatDevice):
            # raw device, not going to delete device but destroy disk format instead
            result = self.delete_disk_label(blivet_device.parents[0])
            return result

        if blivet_device.isDisk:
            result = self.delete_disk_label(blivet_device)
            return result

        try:
            if blivet_device.type in ("partition", "lvmlv", "lvmthinlv") and blivet_device.format.type:
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

                if parent.exists:
                # teardown existing parent before
                    try:
                        parent.teardown()

                    except blivet.errors.LUKSError:
                        msg = _("Failed to remove device {name}. Are you sure it's not in use?").format(name=parent.name)

                        # cancel destroy action for luks device
                        self.blivet_cancel_actions(actions)
                        return ProxyDataContainer(success=False, actions=None, message=msg, exception=None,
                                                  traceback=traceback.format_exc())

                result = self.delete_device(parent)
                if not result.success:
                    return result
                else:
                    actions.extend(result.actions)

        # for btrfs volumes delete parents partition after deleting volume
        if blivet_device.type in ("btrfs volume", "mdarray"):
            for parent in blivet_device.parents:
                if parent.type == "partition":
                    result = self.delete_device(parent)
                elif parent.type == "disk":
                    result = self.delete_disk_label(parent)

                if not result.success:
                    return result
                else:
                    actions.extend(result.actions)

        return ProxyDataContainer(success=True, actions=actions, message=None, exception=None, traceback=None)

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

        if (blivet_device.format.type in ("swap",) or not blivet_device.format.exists
           or not hasattr(blivet_device.format, "updateSizeInfo")):
            return ProxyDataContainer(resizable=False, error=None, min_size=blivet.size.Size("1 MiB"),
                                       max_size=blivet_device.size)

        elif not blivet_device.format.type:
            if blivet_device.type == "partition" and blivet_device.isExtended and blivet_device.maxSize > blivet_device.size:
                return ProxyDataContainer(resizable=True, error=None, min_size=blivet_device.size,
                                          max_size=blivet_device.maxSize)
            else:
                return ProxyDataContainer(resizable=False, error=None, min_size=blivet.size.Size("1 MiB"),
                                          max_size=blivet_device.size)


        if blivet_device.type in ("lvmlv",) and self._has_snapshots(blivet_device):
            msg = _("Logical Volumes with snapshots couldn't be resized.")
            return ProxyDataContainer(resizable=False, error=msg, min_size=blivet.size.Size("1 MiB"),
                                      max_size=blivet_device.size)

        try:
            blivet_device.format.updateSizeInfo()

        except blivet.errors.FSError as e:
            return ProxyDataContainer(resizable=False, error=str(e),
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
            return ProxyDataContainer(success=True, actions=None, message=None, exception=None, traceback=None)

        if user_input.resize:
            if blivet_device.type == "partition":
                aligned_size = blivet_device.alignTargetSize(user_input.size)
            else:
                aligned_size = user_input.size

            # do not resize format on extended partitions
            if not (blivet_device.type == "partition" and blivet_device.isExtended):
                actions.append(blivet.deviceaction.ActionResizeFormat(blivet_device, aligned_size))
            actions.append(blivet.deviceaction.ActionResizeDevice(blivet_device, aligned_size))

            # reverse resize actions when growing
            if user_input.size > blivet_device.size:
                actions.reverse()

        if user_input.fmt:
            new_fmt = blivet.formats.getFormat(user_input.filesystem, label=user_input.label, mountpoint=user_input.mountpoint)
            actions.append(blivet.deviceaction.ActionCreateFormat(blivet_device, new_fmt))

        try:
            for ac in actions:
                self.storage.devicetree.registerAction(ac)
            blivet.partitioning.doPartitioning(self.storage)
            return ProxyDataContainer(success=True, actions=actions, message=None, exception=None, traceback=None)

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

        return ProxyDataContainer(success=True, actions=actions, message=None, exception=None, traceback=None)

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
                name = self.storage.suggestDeviceName(parent=parent_device, swap=False, prefix="snapshot")
            else:
                if hasattr(platform, "linux_distribution"):
                    prefix = re.sub(r"\W+", "", platform.linux_distribution()[0].lower())
                else:
                    prefix = ""

                name = self.storage.suggestContainerName(hostname=socket.gethostname(), prefix=prefix)

        else:
            name = self.storage.safeDeviceName(name)

            # if name exists add -XX suffix
            if name in self.storage.names or (parent_device and parent_device.name + "-" + name in self.storage.names):
                for i in range(100):
                    if name + "-" + str(i) not in self.storage.names:
                        name = name + "-" + str(i)
                        break

            # if still exists let blivet pick it
            if name in self.storage.names:
                name = self._pick_device_name(name=None, parent_device=parent_device)

        return name

    def _create_partition(self, user_input):
        actions = []

        if hasattr(user_input, "advanced"):
            partition_type = user_input.advanced["parttype"] or "primary"
        else:
            partition_type = "primary"

        # create new partition
        new_part = PartitionDevice(name="req%d" % self.storage.nextID,
                                   size=user_input.size,
                                   parents=[i[0] for i in user_input.parents],
                                   partType=PARTITION_TYPE[partition_type])
        actions.append(blivet.deviceaction.ActionCreateDevice(new_part))

        # encrypted partition -- create a luks device and format it to desired format
        if user_input.encrypt:
            part_fmt = blivet.formats.getFormat(fmt_type="luks",
                                                passphrase=user_input.passphrase,
                                                device=new_part.path)
            actions.append(blivet.deviceaction.ActionCreateFormat(new_part, part_fmt))

            luks_dev = LUKSDevice("luks-%s" % new_part.name, size=new_part.size, parents=[new_part])
            actions.append(blivet.deviceaction.ActionCreateDevice(luks_dev))

            luks_fmt = blivet.formats.getFormat(fmt_type=user_input.filesystem,
                                                device=new_part.path,
                                                mountpoint=user_input.mountpoint)
            actions.append(blivet.deviceaction.ActionCreateFormat(luks_dev, luks_fmt))

        # non-encrypted partition -- just format the partition
        else:
            if partition_type != "extended":
                fmt_type = user_input.filesystem
                if fmt_type == "ntfs":
                    fmt_options = "-f"
                else:
                    fmt_options = ""

                new_fmt = blivet.formats.getFormat(fmt_type=fmt_type,
                                                   label=user_input.label,
                                                   mountpoint=user_input.mountpoint,
                                                   createOptions=fmt_options)
                actions.append(blivet.deviceaction.ActionCreateFormat(new_part, new_fmt))

        return actions

    def _create_lvmlv(self, user_input):
        actions = []

        if user_input.device_type == "lvmthinlv":
            create_class = LVMThinLogicalVolumeDevice
            # for thinlv, parent (for name suggestion) is not thinpool but the vg
            device_name = self._pick_device_name(user_input.name, user_input.parents[0][0].vg)
        elif user_input.device_type == "lvmlv":
            create_class = LVMLogicalVolumeDevice
            device_name = self._pick_device_name(user_input.name, user_input.parents[0][0])

        new_part = create_class(name=device_name,
                                size=user_input.size,
                                parents=[i[0] for i in user_input.parents])
        actions.append(blivet.deviceaction.ActionCreateDevice(new_part))

        fmt_type = user_input.filesystem
        if fmt_type == "ntfs":
            fmt_options = "-f"
        else:
            fmt_options = ""

        new_fmt = blivet.formats.getFormat(fmt_type=user_input.filesystem,
                                           mountpoint=user_input.mountpoint,
                                           createOptions=fmt_options)
        actions.append(blivet.deviceaction.ActionCreateFormat(new_part, new_fmt))

        return actions

    def _create_lvmpv(self, user_input):
        actions = []

        new_part = PartitionDevice(name="req%d" % self.storage.nextID,
                              size=user_input.size,
                              parents=[i[0] for i in user_input.parents])
        actions.append(blivet.deviceaction.ActionCreateDevice(new_part))

        # encrypted lvmpv
        if user_input.encrypt:
            part_fmt = blivet.formats.getFormat(fmt_type="luks",
                                                passphrase=user_input.passphrase,
                                                device=new_part.path)
            actions.append(blivet.deviceaction.ActionCreateFormat(new_part, part_fmt))

            luks_dev = LUKSDevice("luks-%s" % new_part.name, size=new_part.size, parents=[new_part])
            actions.append(blivet.deviceaction.ActionCreateDevice(luks_dev))

            luks_fmt = blivet.formats.getFormat(fmt_type="lvmpv")
            actions.append(blivet.deviceaction.ActionCreateFormat(luks_dev, luks_fmt))

        else:

            part_fmt = blivet.formats.getFormat(fmt_type="lvmpv")
            actions.append(blivet.deviceaction.ActionCreateFormat(new_part, part_fmt))

        return actions

    def _create_lvmvg(self, user_input):
        actions = []

        device_name = self._pick_device_name(user_input.name)

        new_vg = LVMVolumeGroupDevice(name=device_name,
                                      parents=[i[0] for i in user_input.parents],
                                      peSize=user_input.advanced["pesize"])
        actions.append(blivet.deviceaction.ActionCreateDevice(new_vg))

        return actions

    def _create_lvmthinpool(self, user_input):
        actions = []

        device_name = self._pick_device_name(user_input.name, user_input.parents[0][0])

        new_thin = LVMThinPoolDevice(name=device_name,
                                     size=user_input.size,
                                     parents=[i[0] for i in user_input.parents])

        actions.append(blivet.deviceaction.ActionCreateDevice(new_thin))

        return actions

    def _create_lvm(self, user_input):
        actions = []

        for parent, size in user_input.parents:
            # _create_lvmpv needs user_input but we actually don't have it for individual
            # pvs so we need to 'create' it
            pv_input = ProxyDataContainer(size=size,
                                          parents=[(parent, size)],
                                          encrypt=user_input.encrypt,
                                          passphrase=user_input.passphrase)
            pv_actions = self._create_lvmpv(pv_input)

            # we need to try to register create actions immediately, if something fails, fail now
            for ac in pv_actions:
                self.storage.devicetree.registerAction(ac)
            actions.extend(pv_actions)

        # we don't have a list of newly created pvs but we have the list of actions
        vg_parents = [(ac.device, ac.device.size) for ac in actions if ac.isFormat and ac._format.type == "lvmpv"]
        vg_input = ProxyDataContainer(name=user_input.name,
                                      parents=vg_parents,
                                      advanced=user_input.advanced)
        vg_actions = self._create_lvmvg(vg_input)
        actions.extend(vg_actions)

        return actions

    def _create_snapshot(self, user_input):
        actions = []

        if user_input.device_type == "lvm snapshot":

            origin_lv = user_input.parents[0][0]
            snapshot_size = user_input.parents[0][1]
            device_name = self._pick_device_name(user_input.name, origin_lv.parents[0])

            new_snap = LVMSnapShotDevice(name=device_name,
                                         parents=[origin_lv.parents[0]],
                                         origin=origin_lv,
                                         size=snapshot_size)
            actions.append(blivet.deviceaction.ActionCreateDevice(new_snap))

        return actions

    def _create_mdraid(self, user_input):
        actions = []

        device_name = self._pick_device_name(user_input.name)

        for parent, size in user_input.parents:
            # _create_partition needs user_input but we actually don't have it for individual
            # parent partitions so we need to 'create' it
            part_input = ProxyDataContainer(size=size,
                                            parents=[(parent, size)],
                                            filesystem="mdmember",
                                            encrypt=False,
                                            label=None, mountpoint=None)
            part_actions = self._create_partition(part_input)

            # we need to try to create partitions immediately, if something fails, fail now
            for ac in part_actions:
                self.storage.devicetree.registerAction(ac)
            actions.extend(part_actions)

        md_parents = [ac.device for ac in actions if ac.isFormat and ac._format.type == "mdmember"]
        new_md = MDRaidArrayDevice(parents=md_parents,
                                   name=device_name,
                                   level=user_input.raid_level,
                                   memberDevices=len(md_parents),
                                   totalDevices=len(md_parents))
        actions.append(blivet.deviceaction.ActionCreateDevice(new_md))

        fmt = blivet.formats.getFormat(fmt_type=user_input.filesystem)
        actions.append(blivet.deviceaction.ActionCreateFormat(new_md, fmt))

        return actions

    def _create_btrfs_disk(self, blivet_disk):
        """ Create a btrfs label on selected disk
        """

        actions = []

        if blivet_disk.format.type:
            result = self.delete_disk_label(blivet_disk)
            if not result.success:
                return result
            else:
                actions.extend(result.actions)

        fmt = blivet.formats.getFormat(fmt_type="btrfs")
        ac_fmt = blivet.deviceaction.ActionCreateFormat(blivet_disk, fmt)

        self.storage.devicetree.registerAction(ac_fmt)

        return actions

    def _create_btrfs_volume(self, user_input):
        actions = []
        device_name = self._pick_device_name(user_input.name)

        for parent, size in user_input.parents:

            if user_input.btrfs_type == "disks":
                disk_ac = self._create_btrfs_disk(parent)

                actions.extend(disk_ac)

            else:
                # _create_partition needs user_input but we actually don't have it for individual
                # parent partitions so we need to 'create' it
                part_input = ProxyDataContainer(size=size,
                                                parents=[(parent, size)],
                                                filesystem="btrfs",
                                                encrypt=False,
                                                label=None,
                                                mountpoint=None)
                part_actions = self._create_partition(part_input)

                # we need to try to create partitions immediately, if something
                # fails, fail now
                for ac in part_actions:
                    self.storage.devicetree.registerAction(ac)
                actions.extend(part_actions)

        if user_input.btrfs_type == "disks":
            btrfs_parents = [parent[0] for parent in user_input.parents]
        else:
            btrfs_parents = [ac.device for ac in actions if (ac.isFormat and ac.isCreate) and ac._format.type == "btrfs"]
        new_btrfs = BTRFSVolumeDevice(device_name, parents=btrfs_parents)
        new_btrfs.format = blivet.formats.getFormat("btrfs", label=device_name, mountpoint=user_input.mountpoint)
        actions.append(blivet.deviceaction.ActionCreateDevice(new_btrfs))

        return actions

    def _create_btrfs_subvolume(self, user_input):
        actions = []
        device_name = self._pick_device_name(user_input.name, user_input.parents[0][0])

        new_btrfs = BTRFSSubVolumeDevice(device_name, parents=[i[0] for i in user_input.parents])
        new_btrfs.format = blivet.formats.getFormat("btrfs", mountpoint=user_input.mountpoint)
        actions.append(blivet.deviceaction.ActionCreateDevice(new_btrfs))

        return actions

    add_dict = {"partition" : _create_partition,
                "lvm" : _create_lvm,
                "lvmlv" : _create_lvmlv,
                "lvmthinlv" : _create_lvmlv,
                "lvmthinpool" : _create_lvmthinpool,
                "lvmvg" : _create_lvmvg,
                "lvmpv" : _create_lvmpv,
                "btrfs volume" : _create_btrfs_volume,
                "btrfs subvolume" : _create_btrfs_subvolume,
                "mdraid" : _create_mdraid,
                "lvm snapshot" : _create_snapshot}

    def add_device(self, user_input):
        """ Create new device

            :param user_input: selected parameters from AddDialog
            :type user_input: class UserInput
            :returns: new device name
            :rtype: str

        """

        add_function = self.add_dict[user_input.device_type]

        try:
            actions = add_function(self, user_input)
        except Exception as e: # pylint: disable=broad-except
            return ProxyDataContainer(success=False, actions=None, message=None,
                                      exception=e, traceback=traceback.format_exc())
        try:
            for ac in actions:
                if not ac._applied:
                    self.storage.devicetree.registerAction(ac)

            blivet.partitioning.doPartitioning(self.storage)

        except Exception as e: # pylint: disable=broad-except
            return ProxyDataContainer(success=False, actions=None, message=None,
                                      exception=e, traceback=traceback.format_exc())

        return ProxyDataContainer(success=True, actions=actions, message=None,
                                  exception=None, traceback=None)

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

        return ProxyDataContainer(success=True, actions=[ac_rm], message=None, exception=None, traceback=None)

    def _add_lvmvg_parent(self, container, parent):
        """ Add new parent to existing lvmg

            :param container: existing lvmvg
            :type container: class blivet.LVMVolumeGroupDevice
            :param parent: new parent -- existing device or free space
            :type parent: class blivet.Device or class blivetgui.utils.FreeSpaceDevice

        """

        actions = []

        if parent.type == "free space":
            dev = PartitionDevice(name="req%d" % self.storage.nextID,
                                  size=parent.size,
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

        return ProxyDataContainer(success=True, actions=actions, message=None, exception=None, traceback=None)

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
        """

        return self.storage.devicetree.findActions()

    def get_available_disklabels(self, allow_btrfs=False):
        """ Return disklabels available on current platform

            :returns: list of disklabel types
            :rtype: list of str

        """

        dl_types = []
        dl_types.extend(blivet.platform.getPlatform().diskLabelTypes)

        if allow_btrfs:
            dl_types.append("btrfs")

        return dl_types

    def get_available_raid_levels(self, device_type):
        """ Return dict of supported raid levels for device types
        """

        if device_type == "btrfs volume":
            return blivet.devicefactory.get_supported_raid_levels(blivet.devicefactory.DEVICE_TYPE_BTRFS)

        if device_type == "mdraid":
            return blivet.devicefactory.get_supported_raid_levels(blivet.devicefactory.DEVICE_TYPE_MD)

    def get_available_filesystems(self):
        """ Return list of currently available (supported and with tools) formats
        """

        _fs_types = []

        for cls in blivet.formats.device_formats.values():
            obj = cls()

            supported_fs = (obj.type not in ("btrfs", "tmpfs") and
                            obj.supported and obj.formattable and
                            (isinstance(obj, blivet.formats.fs.FS) or
                             obj.type in ("swap",)))
            if supported_fs:
                _fs_types.append(obj.name)

        return sorted(_fs_types)

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

        return ProxyDataContainer(success=True, actions=actions, message=None, exception=None, traceback=None)

    def set_bootloader_device(self, disk_name):
        self.ksparser.handler.bootloader.location = "mbr"
        self.ksparser.handler.bootloader.bootDrive = disk_name

        self.storage.ksdata = self.ksparser.handler

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

        blivet_device.format._setPassphrase(passphrase)

        try:
            blivet_device.format.setup()

        except blivet.errors.LUKSError:
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

    def blivet_do_it(self, progress_report_hook):
        """ Blivet.doIt()
        """

        progress_clbk = lambda clbk_data: progress_report_hook(clbk_data.msg)

        callbacks_reg = blivet.callbacks.create_new_callbacks_register(report_progress=progress_clbk)

        try:
            self.storage.doIt(callbacks=callbacks_reg)

        except Exception as e: # pylint: disable=broad-except
            return (True, ProxyDataContainer(success=False, exception=e, traceback=traceback.format_exc()))

        else:
            return (True, ProxyDataContainer(success=True))

    def create_kickstart_file(self, fname):
        """ Create kickstart config file
        """

        self.storage.updateKSData()

        with open(fname, "w") as outfile:
            outfile.write(self.storage.ksdata.__str__())
