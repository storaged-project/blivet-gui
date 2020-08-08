# -*- coding: utf-8 -*-
# rectangle.py
# Gtk.Button modified for device visualization
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

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk

from ..i18n import _


class Rectangle(Gtk.RadioButton):
    """ Rectangle object """

    def __init__(self, rtype, group, width, height, device, label=True):
        self.width = width
        self.height = height

        self.device = device

        Gtk.RadioButton.__init__(self, group=group, width_request=width, height_request=height)

        self.set_mode(False)
        self.set_name("bg-" + rtype)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=False, spacing=6)
        self.add(hbox)

        self.device_icons = {"group": ("drive-multidisk-symbolic", _("Group device")),
                             "livecd": ("media-optical-symbolic", _("LiveUSB device")),
                             "encrypted": ("changes-prevent-symbolic", _("Encrypted device (locked)")),
                             "decrypted": ("changes-allow-symbolic", _("Encrypted device (unlocked)")),
                             "empty": ("radio-symbolic", _("Empty device")),
                             "snapshot": ("camera-photo-symbolic", _("Snapshot")),
                             "nodisklabel": ("drive-harddisk-symbolic", _("Missing partition table")),
                             "protected": ("action-unavailable-symbolic", _("Device or format is write protected")),
                             "cached": ("drive-harddisk-solidstate-symbolic", _("Cached device"))}

        if label:
            label_device = Gtk.Label(justify=Gtk.Justification.CENTER,
                                     label="<small>%s\n%s</small>" % (self.device.name, str(self.device.size)),
                                     use_markup=True, name="dark")

            hbox.pack_start(child=label_device, expand=True, fill=True, padding=0)

            icons = self._add_device_icons()
            hbox.pack_start(child=icons, expand=False, fill=False, padding=0)

    def _add_device_icons(self):
        device_properties = self._get_device_properties()

        icon_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=4)
        for prop in device_properties:
            icon = Gtk.Image.new_from_icon_name(self.device_icons[prop][0], Gtk.IconSize.MENU)
            icon.set_tooltip_text(self.device_icons[prop][1])
            icon.set_opacity(0.85)
            icon_box.pack_end(child=icon, expand=False, fill=False, padding=0)

        return icon_box

    def _get_device_properties(self):
        properties = []
        if self.device.type in ("lvmvg", "btrfs volume", "mdarray"):
            properties.append("group")
        if self.device.format and self.device.format.type in ("iso9660", "udf"):
            properties.append("livecd")
        if self.device.type == "partition" and self.device.format.type == "luks":
            if self.device.children:
                properties.append("decrypted")
            else:
                properties.append("encrypted")
        if self.device.type == "luks/dm-crypt" or any(parent.type == "luks/dm-crypt" for parent in self.device.parents):
            properties.append("decrypted")
        if self.device.type in ("lvmsnapshot", "btrfs snapshot", "lvmthinsnapshot"):
            properties.append("snapshot")
        if self.device.type == "free space" or (self.device.format and self.device.format.type == "lvmpv" and
                                                not self.device.children):
            properties.append("empty")
        if self.device.type == "free space" and self.device.is_uninitialized_disk:
            properties.append("nodisklabel")

        if self.device.format.exists and self.device.protected:
            properties.append("protected")

        if self.device.type in ("lvmlv", "lvmthinpool") and self.device.cached:
            properties.append("cached")

        return properties
