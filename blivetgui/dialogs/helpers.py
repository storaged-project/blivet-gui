# -*- coding: utf-8 -*-
# helpers.py
# Helper functions for blivet-gui dialogs
#
# Copyright (C) 2015  Red Hat, Inc.
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

import os

from ..dialogs import message_dialogs
from ..i18n import _

from blivet.devices.btrfs import BTRFSDevice
from blivet.devices.lvm import  LVMVolumeGroupDevice, LVMLogicalVolumeDevice

from blivet.tasks.fslabeling import Ext2FSLabeling, FATFSLabeling, JFSLabeling, ReiserFSLabeling, XFSLabeling, NTFSLabeling

#------------------------------------------------------------------------------#

def is_name_valid(device_type, name):
    if device_type in ("lvmvg", "lvm"):
        return LVMVolumeGroupDevice.isNameValid(name)
    elif device_type == "lvmlv":
        return LVMLogicalVolumeDevice.isNameValid(name)
    elif device_type in ("btrfs volume", "btrfs subvolume"):
        return BTRFSDevice.isNameValid(name)
    else:
        return True

def is_label_valid(format_type, label):
    if format_type in ("ext2", "ext3", "ext4"):
        return Ext2FSLabeling.labelFormatOK(label)
    elif format_type == "vfat":
        return FATFSLabeling.labelFormatOK(label)
    elif format_type == "jfs":
        return JFSLabeling.labelFormatOK(label)
    elif format_type == "raiserfs":
        return ReiserFSLabeling.labelFormatOK(label)
    elif format_type == "xfs":
        return XFSLabeling.labelFormatOK(label)
    elif format_type == "ntfs":
        return NTFSLabeling.labelFormatOK(label)
    else:
        return True

def check_mountpoint(parent_window, used_mountpoints, mountpoint):
    """ Kickstart mode; check for duplicate mountpoints

        :param used_mountpoints: list of mountpoints currently in use
        :type used_mountpoints: list of str
        :param mountpoint: mountpoint selected by user
        :type mountpoint: str
        :returns: mountpoint validity
        :rtype: bool
    """

    # FIXME: do not open the dialog, just return true or false

    if not mountpoint:
        return True

    elif not os.path.isabs(mountpoint):
        msg = _("{0} is not a valid mountpoint.").format(mountpoint)
        message_dialogs.ErrorDialog(parent_window, msg)
        return False

    elif mountpoint not in used_mountpoints:
        return True

    else:
        msg = _("Selected mountpoint \"{0}\" is already set for another device").format(mountpoint)
        message_dialogs.ErrorDialog(parent_window, msg)
        return False
