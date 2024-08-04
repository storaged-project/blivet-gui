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
# ---------------------------------------------------------------------------- #

import parted

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Pango", "1.0")

from gi.repository import Gtk, Pango

from ..i18n import _

# ---------------------------------------------------------------------------- #

PARTITION_TYPE = {parted.PARTITION_NORMAL: _("primary"),  # pylint: disable=W9902
                  parted.PARTITION_LOGICAL: _("logical"),  # pylint: disable=W9902
                  parted.PARTITION_EXTENDED: _("extended")}  # pylint: disable=W9902

# ---------------------------------------------------------------------------- #


class DeviceInformationDialog(Gtk.Dialog):
    """ Dialog showing information about selected device
    """

    def __init__(self, parent_window, device, client, installer_mode=False):
        """

            :param parent_window: parent window
            :type parent_window: Gtk.Window
            :param device: a blviet device
            :type disk_device: blivet.Device

        """

        self.parent_window = parent_window
        self.device = device
        self.client = client
        self.installer_mode = installer_mode

        # Gtk.Dialog
        Gtk.Dialog.__init__(self)

        self.set_transient_for(self.parent_window)
        self.set_border_width(10)
        self.set_title(_("Information about {0}").format(self.device.name))
        self.add_buttons(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)

        # Gtk.Grid
        self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10, column_spacing=20)
        self.grid.set_margin_start(15)
        self.grid.set_margin_end(15)

        box = self.get_content_area()
        box.add(self.grid)

        # dictionary with 'human-readable' device names and methods providing detailed information
        self.type_dict = {"partition": (_("Partition"), self._get_partition_info),
                          "lvmvg": (_("LVM2 Volume Group"), self._get_lvmvg_info),
                          "lvmlv": (_("LVM2 Logical Volume"), self._get_lvmlv_info),
                          "lvmsnapshot": (_("LVM2 Snapshot"), self._get_lvmlv_info),
                          "lvmthinpool": (_("LVM2 ThinPool"), self._get_lvmlv_info),
                          "lvmthinlv": (_("LVM2 Thin Logical Volume"), self._get_lvmlv_info),
                          "luks/dm-crypt": (_("LUKS/DM-Crypt Device"), None),
                          "btrfs volume": (_("Btrfs Volume"), self._get_btrfs_info),
                          "btrfs subvolume": (_("Btrfs Subvolume"), self._get_btrfs_info),
                          "mdarray": (_("MD RAID Array"), self._get_mdarray_info),
                          "integrity/dm-crypt": (_("DM Integrity Device"), None)}

        # Fill dialog with information
        self.add_device_info()
        self.add_format_info()

        if self.device.parents:
            self.add_parents_info()

        # Show content
        self.show_all()

    def _get_partition_info(self):
        info = _(" • <i>Type:</i> {type}\n").format(type=PARTITION_TYPE[self.device.part_type])

        if self.device.parted_partition:
            info += _(" • <i>Length:</i> {length}\n").format(length=self.device.parted_partition.geometry.length)
            info += _(" • <i>Start:</i> {start}\n").format(start=self.device.parted_partition.geometry.start)
            info += _(" • <i>End:</i> {end}\n").format(end=self.device.parted_partition.geometry.end)

        return info

    def _get_lvmlv_info(self):
        info = ""
        if self.device.type == "lvmsnapshot":
            info += _(" • <i>Origin:</i> {origin}\n").format(origin=self.device.origin.name)
            info += _(" • <i>Segment type:</i> {segtype}\n").format(segtype=self.device.seg_type)
        elif self.device.type == "lvmthinpool":
            info += _(" • <i>Segment type:</i> {segtype}\n").format(segtype=self.device.seg_type)
            info += _(" • <i>Free space:</i> {free}\n").format(free=str(self.device.free_space))
            info += _(" • <i>Space used:</i> {used}\n").format(used=str(self.device.used_space))
        else:
            info += _(" • <i>Segment type:</i> {segtype}\n").format(segtype=self.device.seg_type)
            if self.device.cached:
                info += _(" • <i>Cached:</i> Yes (cache size: {cache_size})\n").format(cache_size=str(self.device.cache.size))
            else:
                info += _(" • <i>Cached:</i> No\n")

        return info

    def _get_lvmvg_info(self):
        info = _(" • <i>PE Size:</i> {pesize}\n").format(pesize=str(self.device.pe_size))
        info += _(" • <i>PE Count:</i> {pecount}\n").format(pecount=self.device.pe_count)
        info += _(" • <i>Free Space:</i> {free}\n").format(free=str(self.device.free))
        info += _(" • <i>PE Free:</i> {pefree}\n").format(pefree=self.device.pe_free)
        info += _(" • <i>Reserved Space:</i> {res}\n").format(res=self.device.reserved_space)
        info += _(" • <i>Complete:</i> {complete}\n").format(complete=self.device.complete)

        return info

    def _get_btrfs_info(self):
        info = _(" • <i>Subvol ID:</i> {id}\n").format(id=self.device.format.subvolspec)

        if self.device.type == "btrfs volume":
            info += _(" • <i>Data Level:</i> {level}\n").format(level=self.device.data_level)
            info += _(" • <i>Metadata Level:</i> {level}\n").format(level=self.device.metadata_level)

        return info

    def _get_mdarray_info(self):
        info = _(" • <i>Level:</i> {level}\n").format(level=str(self.device.level))
        info += _(" • <i>Devices:</i> {dcount}\n").format(dcount=self.device.total_devices)
        info += _(" • <i>Spares:</i> {spares}\n").format(spares=str(self.device.spares))
        info += _(" • <i>Degraded:</i> {degraded}\n").format(degraded=self.device.degraded)
        info += _(" • <i>Metadata Version:</i> {metadata}\n").format(metadata=self.device.metadata_version)
        info += _(" • <i>Complete:</i> {complete}\n").format(complete=self.device.complete)

        return info

    def add_device_info(self):
        """ Display information about the device
        """

        # device name and type header
        device_type_label = Gtk.Label()
        self.grid.attach(child=device_type_label, left=0, top=0, width=2, height=1)

        # unknown device type
        if self.device.type not in self.type_dict.keys():
            info = _("Unknown device {name}").format(name=self.device.name)

        else:
            info = "{type} {name}".format(type=self.type_dict[self.device.type][0],
                                          name=self.device.name)
        device_type_label.set_markup("<b>%s</b>" % info)

        # device info header
        info_type_label = Gtk.Label(label="<i>%s</i>" % _("Basic information"), use_markup=True)
        self.grid.attach(child=info_type_label, left=0, top=1, width=2, height=1)
        info_type_label.set_xalign(0)
        info_type_label.set_yalign(0)

        device_info_label = Gtk.Label()
        device_info_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        self.grid.attach(device_info_label, left=0, top=2, width=1, height=1)

        # 'basic' information about selected device
        existing = _("existing") if self.device.exists else _("non-existing")
        info = _(" • <i>Status:</i> {exist}\n").format(exist=existing)
        info += _(" • <i>Name:</i> {name}\n").format(name=self.device.name)
        info += _(" • <i>Path:</i> {path}\n").format(path=self.device.path)
        info += _(" • <i>Size:</i> {size}\n").format(size=str(self.device.size))

        device_info_label.set_markup(info)
        device_info_label.set_xalign(0)
        device_info_label.set_yalign(0)

        # 'advanced' information about selected device (specific for each device type)
        if self.device.type in self.type_dict.keys() and self.type_dict[self.device.type][1]:
            adv_info_label = Gtk.Label()
            self.grid.attach(adv_info_label, left=1, top=2, width=1, height=1)

            adv_info_fn = self.type_dict[self.device.type][1]
            adv_info_label.set_markup(adv_info_fn())
            adv_info_label.set_xalign(0)
            adv_info_label.set_yalign(0)

    def add_format_info(self):
        """ Display information about format of the device
        """

        # device format header
        info_type_label = Gtk.Label(label="<i>%s</i>" % _("Device format"), use_markup=True)
        self.grid.attach(child=info_type_label, left=0, top=3, width=2, height=1)
        info_type_label.set_xalign(0)
        info_type_label.set_yalign(0)

        # information about device format
        fmt_info_label = Gtk.Label()
        fmt_info_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        self.grid.attach(fmt_info_label, left=0, top=4, width=2, height=1)

        if self.device.format and self.device.format.type:
            existing = _("existing") if self.device.exists else _("non-existing")
            info = _(" • <i>Status:</i> {exist}\n").format(exist=existing)
            info += _(" • <i>Type:</i> {type}\n").format(type=self.device.format.type)
            info += _(" • <i>UUID:</i> {uuid}\n").format(uuid=self.device.format.uuid)
            if hasattr(self.device.format, "label") and self.device.format.label:
                info += _(" • <i>Label:</i> {label}\n").format(label=self.device.format.label)

            if self.device.format.mountable:
                if self.installer_mode:
                    mnt = self.device.format.mountpoint if (self.device.format and self.device.format.mountable) else None
                else:
                    is_mounted = bool(self.device.format.system_mountpoint) if (self.device.format and self.device.format.mountable) else False
                    if is_mounted:
                        mnts = self.client.remote_call("get_system_mountpoints", self.device)
                        mnt = "\n     ".join(mnts)
                    else:
                        mnt = None

                if mnt:
                    info += _(" • <i>Mountpoints:</i>\n     {mountpoints}").format(mountpoints=mnt)

        else:
            info = _(" • <i>Type:</i> None")

        fmt_info_label.set_markup(info)
        fmt_info_label.set_xalign(0)
        fmt_info_label.set_yalign(0)

    def add_parents_info(self):
        """ Display information about parents of the device
        """

        parents = self.device.parents

        # device parents header
        info_parents_label = Gtk.Label(label="<i>%s</i>" % _("Parents"), use_markup=True)
        self.grid.attach(child=info_parents_label, left=0, top=5, width=2, height=1)
        info_parents_label.set_xalign(0)
        info_parents_label.set_yalign(0)

        # information about device parents
        parent_info_label = Gtk.Label()
        parent_info_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        self.grid.attach(parent_info_label, left=0, top=6, width=2, height=1)

        info = ""
        for parent in parents:
            exists = _("existing") if parent.exists else _("non-existing")
            info += _(" • {exists} {size} {type} {name}\n").format(exists=exists,
                                                                   size=str(parent.size),
                                                                   name=parent.name,
                                                                   type=parent.type)

        parent_info_label.set_markup(info)
        parent_info_label.set_xalign(0)
        parent_info_label.set_yalign(0)
