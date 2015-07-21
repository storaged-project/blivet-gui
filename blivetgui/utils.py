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

from  .blivetguiproxy.proxy_utils import ProxyDataContainer

import gi
gi.require_version("BlockDev", "1.0")

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

    def __init__(self, kickstart=False, test_run=False):

        if kickstart:
            self.ksparser = pykickstart.parser.KickstartParser(makeVersion())
            self.storage = blivet.Blivet(ksdata=self.ksparser.handler)
        else:
            self.storage = blivet.Blivet()

        if not test_run:
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

    def get_free_disks_regions(self, include_uninitialized=False):
        """ Returns list of non-empty disks with free space
        """

        free_disks = []

        for disk in self.storage.disks:

            if disk.format.type not in ("disklabel",) and not include_uninitialized:
                continue

            elif not disk.format.type:
                free_disks.append(FreeSpaceDevice(disk.size, 0, disk.currentSize, [disk]))
                continue

            free_space = blivet.partitioning.getFreeRegions([disk])

            for free in free_space:
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
                blivet_device.currentSize, [blivet_device], False))

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
            if disk_device.format.exists:
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
                assert parent.type == "partition" and parent.format.type == "luks"

                if parent.exists:
                # teardown existing parent before
                    try:
                        parent.teardown()

                    except BlockDev.CryptoError:
                        msg = _("Failed to remove device {0}. Are you sure it is not in use?").format(parent.name)

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
                exc = unicode(e).encode("utf8") # pylint: disable=E0602
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
            if blivet_device.type == "partition":
                aligned_size = blivet_device.alignTargetSize(user_input.size)
            else:
                aligned_size = user_input.size
            actions.append(blivet.deviceaction.ActionResizeFormat(blivet_device, aligned_size))
            actions.append(blivet.deviceaction.ActionResizeDevice(blivet_device, aligned_size))

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
                new_fmt = blivet.formats.getFormat(fmt_type=user_input.filesystem,
                                                   label=user_input.label,
                                                   mountpoint=user_input.mountpoint)
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

        new_fmt = blivet.formats.getFormat(fmt_type=user_input.filesystem,
                                           mountpoint=user_input.mountpoint)
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
