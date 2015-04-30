 # -*- coding: utf-8 -*-
# device_information_dialog.py
# Dialog showing information about selected device
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

from __future__ import print_function

import gettext

import parted

from gi.repository import Gtk

#------------------------------------------------------------------------------#

_ = lambda x: gettext.translation("blivet-gui", fallback=True).gettext(x) if x != "" else ""

#------------------------------------------------------------------------------#

PARTITION_TYPE = {parted.PARTITION_NORMAL : _("primary"),
                  parted.PARTITION_LOGICAL : _("logical"),
                  parted.PARTITION_EXTENDED : _("extended")}

#------------------------------------------------------------------------------#

class DeviceInformationDialog(Gtk.Dialog):
    """ Dialog showing information about selected device
    """

    def __init__(self, parent_window, device):
        """

            :param parent_window: parent window
            :type parent_window: Gtk.Window
            :param device: a blviet device
            :type disk_device: blivet.Device

        """

        self.parent_window = parent_window
        self.device = device

        # Gtk.Dialog
        Gtk.Dialog.__init__(self, _("Information about {0}").format(self.device.name), None, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))

        self.set_transient_for(self.parent_window)
        self.set_border_width(10)

        # Gtk.Grid
        self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10, column_spacing=20)
        self.grid.set_margin_left(15)
        self.grid.set_margin_right(15)

        box = self.get_content_area()
        box.add(self.grid)

        # dictionary with 'human-readable' device names and methods providing detailed information
        self.type_dict = {"partition" : (_("Partition"), self._get_partition_info),
                          "lvmvg" : (_("LVM2 Volume Group"), self._get_lvmvg_info),
                          "lvmlv" : (_("LVM2 Logical Volume"), self._get_lvmlv_info),
                          "lvmsnapshot" : (_("LVM2 Snapshot"), self._get_lvmlv_info),
                          "lvmthinpool" : (_("LVM2 ThinPool"), self._get_lvmlv_info),
                          "luks/dm-crypt" : (_("LUKS/DM-Crypt Device"), None),
                          "btrfs volume" : (_("Btrfs Volume"), self._get_btrfs_info),
                          "btrfs subvolume" : (_("Btrfs Subvolume"), self._get_btrfs_info)}

        # Fill dialog with information
        self.device_info = self.add_device_info()
        self.format_info = self.add_format_info()
        self.parents_info = self.add_parents_info()

        # Show content
        self.show_all()

    def _get_partition_info(self):
        info = _(" • <i>Type:</i> {type}\n").format(type=PARTITION_TYPE[self.device.partType])

        if self.device.partedPartition:
            info += _(" • <i>Length:</i> {length}\n").format(length=self.device.partedPartition.geometry.length)
            info += _(" • <i>Start:</i> {start}\n").format(start=self.device.partedPartition.geometry.start)
            info += _(" • <i>End:</i> {end}\n").format(end=self.device.partedPartition.geometry.end)

        return info

    def _get_lvmlv_info(self):
        info = ""
        if self.device.type == "lvmsnapshot":
            info += _(" • <i>Origin:</i> {origin}\n").format(origin=self.device.origin.name)
            info += _(" • <i>Segment type:</i> {segtype}\n").format(segtype=self.device.segType)
            info += _(" • <i>Mirror copies:</i> {copies}\n").format(copies=self.device.copies)
        elif self.device.type == "lvmthinpool":
            info += _(" • <i>Segment type:</i> {segtype}\n").format(segtype=self.device.segType)
            info += _(" • <i>Mirror copies:</i> {copies}\n").format(copies=self.device.copies)
            info += _(" • <i>Free space:</i> {free}\n").format(free=str(self.device.freeSpace))
            info += _(" • <i>Space used:</i> {used}\n").format(used=str(self.device.usedSpace))
        else:
            info += _(" • <i>Segment type:</i> {segtype}\n").format(segtype=self.device.segType)
            info += _(" • <i>Mirror copies:</i> {copies}\n").format(copies=self.device.copies)

        return info

    def _get_lvmvg_info(self):
        info = _(" • <i>PE Size:</i> {pesize}\n").format(pesize=str(self.device.peSize))
        info += _(" • <i>PE Count:</i> {pecount}\n").format(pecount=self.device.peCount)
        info += _(" • <i>Free Space:</i> {free}\n").format(free=str(self.device.free))
        info += _(" • <i>PE Free:</i> {pefree}\n").format(pefree=self.device.peFree)
        info += _(" • <i>Reserved Space:</i> {res} ({resp} %)\n").format(res=self.device.reservedSpace,
            resp=self.device.reserved_percent)
        info += _(" • <i>Complete:</i> {complete}\n").format(complete=self.device.complete)

        return info

    def _get_btrfs_info(self):
        info = _(" • <i>Subvol ID:</i> {id}\n").format(id=self.device.format.subvolspec)
        info += _(" • <i>Data Level:</i> {level}\n").format(level=self.device.dataLevel)
        info += _(" • <i>Metadata Level:</i> {level}\n").format(level=self.device.metaDataLevel)

        return info

    def add_device_info(self):
        """ Display information about the device
        """

        # device name and type header
        device_type_label = Gtk.Label()
        self.grid.attach(child=device_type_label, left=0, top=0, width=2, height=1)

        info = "<b>{type} {name}</b>".format(type=self.type_dict[self.device.type][0],
            name=self.device.name)
        device_type_label.set_markup(info)

        # device info header
        info_type_label = Gtk.Label(label=_("<i>Basic information</i>"), use_markup=True)
        self.grid.attach(child=info_type_label, left=0, top=1, width=2, height=1)
        info_type_label.set_alignment(xalign=0, yalign=0)

        device_info_label = Gtk.Label()
        self.grid.attach(device_info_label, left=0, top=2, width=1, height=1)

        # 'basic' information about selected device
        existing = "existing" if self.device.exists else "non-existing"
        info = _(" • <i>Status:</i> {exist}\n").format(exist=existing)
        info += _(" • <i>Name:</i> {name}\n").format(name=self.device.name)
        info += _(" • <i>Path:</i> {path}\n").format(path=self.device.path)
        info += _(" • <i>Size:</i> {size}\n").format(size=str(self.device.size))

        device_info_label.set_markup(info)
        device_info_label.set_alignment(xalign=0, yalign=0)

        # 'advanced' information about selected device (specific for each device type)
        if self.device.type in self.type_dict.keys() and self.type_dict[self.device.type][1]:
            adv_info_label = Gtk.Label()
            self.grid.attach(adv_info_label, left=1, top=2, width=1, height=1)

            adv_info_fn = self.type_dict[self.device.type][1]
            adv_info_label.set_markup(adv_info_fn())
            adv_info_label.set_alignment(xalign=0, yalign=0)

    def add_format_info(self):
        """ Display information about format of the device
        """

        # device format header
        info_type_label = Gtk.Label(label=_("<i>Device format</i>"), use_markup=True)
        self.grid.attach(child=info_type_label, left=0, top=3, width=2, height=1)
        info_type_label.set_alignment(xalign=0, yalign=0)

        # information about device format
        fmt_info_label = Gtk.Label()
        self.grid.attach(fmt_info_label, left=0, top=4, width=2, height=1)

        if self.device.format and self.device.format.type:
            existing = "existing" if self.device.exists else "non-existing"
            info = _(" • <i>Status:</i> {exist}\n").format(exist=existing)
            info += _(" • <i>Type:</i> {type}\n").format(type=self.device.format.type)
            info += _(" • <i>UUID:</i> {uuid}\n").format(uuid=self.device.format.uuid)
            if hasattr(self.device.format, "label") and self.device.format.label:
                info += _(" • <i>Label:</i> {label}\n").format(label=self.device.format.label)
            if hasattr(self.device.format, "systemMountpoint") and self.device.format.systemMountpoint:
                info += _(" • <i>Mountpoint:</i> {mountpoint}\n").format(mountpoint=self.device.format.systemMountpoint)

        else:
            info = _(" • <i>Type:</i> None")

        fmt_info_label.set_markup(info)
        fmt_info_label.set_alignment(xalign=0, yalign=0)

    def add_parents_info(self):
        """ Display information about parents of the device
        """

        parents = self.device.parents

        # device parents header
        info_parents_label = Gtk.Label(label=_("<i>Parents</i>"), use_markup=True)
        self.grid.attach(child=info_parents_label, left=0, top=5, width=2, height=1)
        info_parents_label.set_alignment(xalign=0, yalign=0)

        # information about device parents
        parent_info_label = Gtk.Label()
        self.grid.attach(parent_info_label, left=0, top=6, width=2, height=1)

        info = ""
        for idx, parent in enumerate(parents):
            exists = _("existing") if parent.exists else _("non-existing")
            info += _(" • Parent device #{idx}: {exists} {size} {type} {name}\n").format(idx=idx,
                exists=exists, size=str(parent.size), name=parent.name, type=parent.type)

        parent_info_label.set_markup(info)
        parent_info_label.set_alignment(xalign=0, yalign=0)
