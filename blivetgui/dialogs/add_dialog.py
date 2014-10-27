# -*- coding: utf-8 -*-
# add_dialog.py
# Gtk.Dialog for adding new device
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

import os

import gettext

from gi.repository import Gtk

from blivet import Size

from math import floor, ceil

import pdb

#------------------------------------------------------------------------------#

_ = lambda x: gettext.ldgettext("blivet-gui", x)

#------------------------------------------------------------------------------#

SUPPORTED_FS = ["ext2", "ext3", "ext4", "xfs", "reiserfs", "swap", "vfat"]
SUPPORTED_UNITS = ["B", "kB", "MB", "GB", "TB", "kiB", "MiB", "GiB", "TiB"]

#------------------------------------------------------------------------------#

class UserSelection(object):
    def __init__(self, device_type, size, filesystem, name, label, mountpoint,
        encrypt, passphrase, parents, btrfs_type, raid_level):

        self.device_type = device_type
        self.size = size
        self.filesystem = filesystem
        self.name = name
        self.label = label
        self.mountpoint = mountpoint
        self.encrypt = encrypt
        self.passphrase = passphrase
        self.parents = parents
        self.btrfs_type = btrfs_type
        self.raid_level = raid_level

class SizeChooserArea(object):

    def __init__(self, parent_device, free_device, max_size, min_size):
        """
            :param device_device: device the free space is on
            :type device_device: blivet.Device
            :param free_device: free space
            :type free_device: blivetgui.utils.FreeSpaceDevice
            :param max_size: maximum size that user can choose
            :type max_size: blivet.Size
            :param min_size: minimum size that user can choose (e.g. min size
                for this device/format type)
            :type min_size: blivet.Size

        """

        self.parent_device = parent_device
        self.free_device = free_device
        self.max_size = max_size
        self.min_size = min_size

        self.widgets = []

        self.selected_unit = None

        self.frame = Gtk.Frame()
        self.frame.set_label(self.parent_device.name)

        self.frame_grid = Gtk.Grid(column_homogeneous=False, row_spacing=10,
            column_spacing=5)

        self.frame.add(self.frame_grid)

        self.widgets.extend([self.frame, self.frame_grid])

        self.scale, self.spin_size = self.add_size_widgets()

    def add_size_widgets(self, unit="MiB"):

        scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL,
            adjustment=Gtk.Adjustment(0, self.min_size.convertTo(unit),
                self.max_size.convertTo(unit), 1, 10, 0))

        scale.set_margin_left(10)
        scale.set_margin_bottom(5)

        scale.set_hexpand(True)
        scale.set_valign(Gtk.Align.START)
        scale.set_digits(0)
        scale.set_value(self.max_size.convertTo(unit))
        scale.add_mark(self.min_size.convertTo(unit), Gtk.PositionType.BOTTOM,
            str(self.min_size))

        if self.max_size < self.free_device.size:
            scale.add_mark(self.max_size.convertTo(unit), Gtk.PositionType.BOTTOM,
                str(self.max_size) + " of " + str(self.free_device.size))

        else:
            scale.add_mark(self.max_size.convertTo(unit), Gtk.PositionType.BOTTOM,
                str(self.max_size))

        self.frame_grid .attach(scale, 0, 0, 4, 3)

        label_size = Gtk.Label(label=_("Volume size:"), xalign=1)
        self.frame_grid .attach(label_size, 4, 1, 1, 1)

        spin_size = Gtk.SpinButton(adjustment=Gtk.Adjustment(0,
            self.min_size.convertTo(unit), self.max_size.convertTo(unit), 1, 10, 0))

        spin_size.set_numeric(True)
        spin_size.set_value(self.max_size.convertTo(unit))

        self.frame_grid .attach(spin_size, 5, 1, 1, 1)

        unit_chooser = self.add_unit_chooser(unit)
        self.frame_grid .attach(unit_chooser, 6, 1, 1, 1)

        scale.connect("value-changed", self.scale_moved, spin_size)
        spin_size.connect("value-changed", self.spin_size_moved, scale)

        self.widgets.extend([scale, label_size, spin_size, unit_chooser])

        return scale, spin_size

    def add_unit_chooser(self, default_unit):

        unit_chooser = Gtk.ComboBoxText()
        unit_chooser.set_margin_right(10)

        for unit in SUPPORTED_UNITS:
            unit_chooser.append_text(unit)

        self.selected_unit = default_unit

        unit_chooser.set_active(SUPPORTED_UNITS.index(default_unit))
        unit_chooser.connect("changed", self.on_unit_combo_changed)

        return unit_chooser

    def adjust_size_scale(self, selected_size, unit="MiB"):

        self.scale.set_range(self.min_size.convertTo(unit), self.max_size.convertTo(unit))
        self.scale.clear_marks()

        increment, digits = self.get_size_precision(self.min_size.convertTo(unit),
            self.max_size.convertTo(unit), unit)
        self.scale.set_increments(increment, increment*10)
        self.scale.set_digits(digits)

        self.scale.add_mark(0, Gtk.PositionType.BOTTOM,
            format(self.min_size.convertTo(unit), "." + str(digits) + "f"))
        self.scale.add_mark(float(self.max_size.convertTo(unit)), Gtk.PositionType.BOTTOM,
            format(self.max_size.convertTo(unit), "." + str(digits) + "f"))

        self.spin_size.set_range(self.min_size.convertTo(unit), self.max_size.convertTo(unit))
        self.spin_size.set_increments(increment, increment*10)
        self.spin_size.set_digits(digits)

        self.scale.set_value(selected_size.convertTo(unit))

    def get_size_precision(self, down_limit, up_limit, unit):

        step = 1.0
        digits = 0

        while True:
            if down_limit >= 1.0:
                break

            down_limit *= 10
            step /= 10
            digits += 1

        # always offer at least 10 steps to adjust size
        if up_limit - down_limit < 10*step:
            step /= 10
            digits += 1

        return step, digits

    def on_unit_combo_changed(self, combo):

        new_unit = combo.get_active_text()
        old_unit = self.selected_unit
        self.selected_unit = new_unit

        selected_size = Size(str(self.scale.get_value()) + old_unit)

        self.adjust_size_scale(selected_size, new_unit)
        return

    def scale_moved(self, scale, spin_size):
        spin_size.set_value(scale.get_value())

    def spin_size_moved(self, spin_size, scale):
        scale.set_value(spin_size.get_value())

    def destroy(self):
        for widget in self.widgets:
            widget.hide()
            widget.destroy()

    def show(self):
        for widget in self.widgets:
            widget.show()

    def set_sensitive(self, sensitivity):
        for widget in self.widgets:
            widget.set_sensitive(sensitivity)

    def get_selection(self):

        size = Size(str(self.scale.get_value()) + self.selected_unit)

        if size > self.free_device.size:
            size = self.free_device.size

        return [self.parent_device, size]

class AddDialog(Gtk.Dialog):
    """ Dialog window allowing user to add new partition including selecting
         size, fs, label etc.
    """

    def __init__(self, parent_window, device_type, parent_device, free_device,
        free_space, free_pvs, free_disks_regions, supported_raids,
        kickstart=False, old_input=None):
        """

            :param device_type: type of parent device
            :type device_type: str
            :parama parent_device: parent device
            :type parent_device: blivet.Device
            :param free_device: free device
            :type free_device: FreeSpaceDevice
            :param free_space: free device size
            :type free_space: blivet.Size
            :param free_pvs: list PVs with no VG
            :type free_pvs: list
            :param free_disks_regions: list of free regions on non-empty disks
            :type free_disks_regions: list of blivetgui.utils.FreeSpaceDevice
            :param kickstart: kickstart mode
            :type kickstart: bool

          """

        self.free_device = free_device
        self.free_space = free_space
        self.device_type = device_type
        self.parent_device = parent_device
        self.free_pvs = free_pvs
        self.free_disks_regions = free_disks_regions
        self.parent_window = parent_window
        self.kickstart = kickstart
        self.old_input = old_input
        self.supported_raids = supported_raids

        Gtk.Dialog.__init__(self, _("Create new device"), None, 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_transient_for(self.parent_window)
        self.set_resizable(False) # auto shrink after removing widgets

        self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10,
            column_spacing=5)
        self.grid.set_border_width(10)

        self.box = self.get_content_area()
        self.box.add(self.grid)

        self.widgets_dict = {}

        # do we have free_type_chooser?
        self.free_type_chooser = None

        self.filesystems_combo = self.add_fs_chooser()
        self.label_entry, self.name_entry = self.add_name_chooser()
        self.encrypt_check, self.pass_entry = self.add_encrypt_chooser()
        self.parents_store = self.add_parent_list()

        self.raid_combo = self.add_raid_type_chooser()

        if kickstart:
            self.mountpoint_entry = self.add_mountpoint()

        self.devices_combo = self.add_device_chooser()
        self.devices_combo.connect("changed", self.on_devices_combo_changed)

        self.size_areas = []
        self.add_size_areas()

        if old_input:
            self.fill_dialog()

        self.show_all()
        self.devices_combo.set_active(0)

    def add_device_chooser(self):

        map_type_devices = {
            "disk" : [(_("Partition"), "partition"), (_("LVM2 Storage"), "lvm"),
            (_("LVM2 Physical Volume"), "lvmpv"), (_("Btrfs Volume"), "btrfs volume")],
            "lvmpv" : [(_("LVM2 Volume Group"), "lvmvg")],
            "lvmvg" : [(_("LVM2 Logical Volume"), "lvmlv")],
            "luks/dm-crypt" : [(_("LVM2 Volume Group"), "lvmvg")],
            "btrfs volume" : [(_("Btrfs Subvolume"), "btrfs subvolume")]
            }

        label_devices = Gtk.Label(label=_("Device type:"), xalign=1)
        label_devices.get_style_context().add_class("dim-label")
        self.grid.attach(label_devices, 0, 0, 1, 1)

        if self.device_type == "disk" and self.free_device.isLogical:
            self.devices = [(_("Partition"), "partition")]

        elif self.device_type == "disk" and not self.parent_device.format.type:
            self.devices = [(_("Btrfs Volume"), "btrfs volume")]

        else:
            self.devices = map_type_devices[self.device_type]

        devices_store = Gtk.ListStore(str, str)

        for device in self.devices:
            devices_store.append([device[0], device[1]])

        devices_combo = Gtk.ComboBox.new_with_model(devices_store)
        devices_combo.set_entry_text_column(0)

        if len(self.devices) == 1:
            devices_combo.set_sensitive(False)

        self.grid.attach(devices_combo, 1, 0, 2, 1)
        renderer_text = Gtk.CellRendererText()
        devices_combo.pack_start(renderer_text, True)
        devices_combo.add_attribute(renderer_text, "text", 0)

        return devices_combo

    def add_parent_list(self):

        parents_store = Gtk.ListStore(object, object, bool, bool, str, str, str)

        parents_view = Gtk.TreeView(model=parents_store)

        renderer_toggle = Gtk.CellRendererToggle()
        renderer_toggle.connect("toggled", self.on_cell_toggled)

        renderer_text = Gtk.CellRendererText()

        column_toggle = Gtk.TreeViewColumn(None, renderer_toggle, active=3)
        column_name = Gtk.TreeViewColumn(_("Device"), renderer_text, text=4)
        column_type = Gtk.TreeViewColumn(_("Type"), renderer_text, text=5)
        column_size = Gtk.TreeViewColumn(_("Size"), renderer_text, text=6)

        parents_view.append_column(column_toggle)
        parents_view.append_column(column_name)
        parents_view.append_column(column_type)
        parents_view.append_column(column_size)

        parents_view.set_headers_visible(True)

        label_list = Gtk.Label(label=_("Available devices:"), xalign=1)
        label_list.get_style_context().add_class("dim-label")

        self.grid.attach(label_list, 0, 1, 1, 1)
        self.grid.attach(parents_view, 1, 1, 4, 3)

        return parents_store

    def update_raid_type_chooser(self):

        device_type = self._get_selected_device_type()
        num_parents = self._get_number_selected_parents()

        if device_type not in self.supported_raids.keys() or num_parents == 1:
            for widget in self.widgets_dict["raid"]:
                widget.hide()

            return

        else:
            # save previously selected raid type
            selected = self.raid_combo.get_active_text()

            self.raid_combo.remove_all()

            for raid in self.supported_raids[device_type]:
                if num_parents >= raid.min_members:
                    self.raid_combo.append_text(raid.name)

            for widget in self.widgets_dict["raid"]:
                widget.show()

            if selected:
                if self.raid_combo.set_active_id(selected):
                    # set_active_id returns bool
                    return

            if device_type == "btrfs volume":
                self.raid_combo.set_active_id("single")

            else:
                self.raid_combo.set_active_id("linear")

        return

    def on_raid_type_changed(self, event):

        self.size_grid = self.add_size_areas()

    def add_raid_type_chooser(self):

        label_raid = Gtk.Label(label=_("RAID Level:"), xalign=1)
        label_raid.get_style_context().add_class("dim-label")
        self.grid.attach(label_raid, 0, 5, 1, 1)

        raid_combo = Gtk.ComboBoxText()
        raid_combo.set_entry_text_column(0)
        raid_combo.set_id_column(0)

        raid_combo.connect("changed", self.on_raid_type_changed)

        self.grid.attach(raid_combo, 1, 5, 1, 1)

        self.widgets_dict["raid"] = [label_raid, raid_combo]

        return raid_combo

    def on_free_space_type_toggled(self, button, name):
        if button.get_active():
            self.update_parent_list(parent_type=name)

            if name == "disks":
                self.set_widgets_unsensitive(["size"])

            else:
                self.set_widgets_sensitive(["size"])

    def add_free_type_chooser(self):

        label_empty_type = Gtk.Label(label=_("Volumes based on:"), xalign=1)
        label_empty_type.get_style_context().add_class("dim-label")
        self.grid.attach(label_empty_type, 0, 4, 1, 1)

        button1 = Gtk.RadioButton.new_with_label_from_widget(None, _("Disks"))
        button1.connect("toggled", self.on_free_space_type_toggled, "disks")
        self.grid.attach(button1, 1, 4, 1, 1)

        button2 = Gtk.RadioButton.new_with_label_from_widget(button1, _("Partitions"))
        button2.connect("toggled", self.on_free_space_type_toggled, "partitions")
        self.grid.attach(button2, 2, 4, 1, 1)

        label_empty_type.show()
        button1.show()
        button2.show()

        if self.free_device.isUnitializedDisk:
            button1.toggled()
            button1.set_sensitive(False)
            button2.set_sensitive(False)

        elif self.free_device.isFreeRegion:
            button2.set_active(True)
            button1.set_sensitive(False)
            button2.set_sensitive(False)

        else:
            # button1 is always pre-selected and re-selecting it using
            # button1.set_active(True) doesn't emit the toggled signal
            button1.toggled()

        self.free_type_chooser = (label_empty_type, button1, button2)

    def remove_free_type_chooser(self):

        for widget in self.free_type_chooser:
            widget.destroy()

        self.free_type_chooser = None

    def select_selected_free_region(self):
        """ In parent list select the free region user selected checkbox as checked
        """

        for row in self.parents_store:
            dev = row[0]
            free = row[1]

            if dev.name == self.parent_device.name and \
                (not self.free_device.start or self.free_device.start == free.start):
                row[2] = row[3] = True

        # TODO move selected iter at the top of the list

    def update_parent_list(self, parent_type=None):

        self.parents_store.clear()

        device_type = self._get_selected_device_type()

        if device_type == "lvmvg":
            for pv, free in self.free_pvs:
                self.parents_store.append([pv, free, False, False, pv.name,
                    "lvmpv", str(free.size)])

        elif device_type in ["btrfs volume", "lvm"]:

            for free in self.free_disks_regions:

                disk = free.parents[0]

                if free.isFreeRegion and (parent_type == "partitions" or device_type == "lvm"):
                    self.parents_store.append([disk, free, False, False, disk.name,
                        "disk region", str(free.size)])

                elif not free.isFreeRegion:
                    self.parents_store.append([disk, free, False, False, disk.name,
                        "disk", str(free.size)])

        else:
            self.parents_store.append([self.parent_device, self.free_device, False, False,
                self.parent_device.name, "disk", str(self.free_device.size)])

        self.select_selected_free_region()

    def on_cell_toggled(self, event, path):

        if self.parents_store[path][2]:
            pass

        else:
            self.parents_store[path][3] = not self.parents_store[path][3]

            self.size_grid = self.add_size_areas()
            self.update_raid_type_chooser()

    def raid_member_max_size(self):

        device_type = self._get_selected_device_type()
        num_parents = self._get_number_selected_parents()

        if device_type not in self.supported_raids.keys() or num_parents == 1:
            return (False, None)

        elif self.raid_combo.get_active_text() in ["linear", "single"]:
            return (False, None)

        else:
            max_size = None

            for row in self.parents_store:

                if row[3]:
                    if not max_size:
                        max_size = row[1].size

                    elif row[1].size < max_size:
                        max_size = row[1].size

            return (True, max_size)

    def add_size_areas(self):

        self.widgets_dict["size"] = []

        if self.size_areas:
            for area in self.size_areas:
                area.destroy()

            self.size_areas = []

        size_grid = Gtk.Grid(column_homogeneous=False, row_spacing=10,
            column_spacing=5)
        self.grid.attach(size_grid, 0, 6, 6, 1)
        size_grid.show()

        posititon = 0

        raid, max_size = self.raid_member_max_size()

        for row in self.parents_store:
            if row[3]:

                if not raid:
                    max_size = row[1].size

                area = SizeChooserArea(parent_device=row[0], free_device=row[1],
                    max_size=max_size, min_size=Size("1 MiB"))

                size_grid.attach(area.frame, 0, posititon, 1, 1)

                self.widgets_dict["size"].append(area)
                self.size_areas.append(area)

                posititon += 1

        for area in self.size_areas:
            area.show()

    def add_fs_chooser(self):
        label_fs = Gtk.Label(label=_("Filesystem:"), xalign=1)
        self.grid.attach(label_fs, 0, 8, 1, 1)

        filesystems_combo = Gtk.ComboBoxText()
        filesystems_combo.set_entry_text_column(0)

        for fs in SUPPORTED_FS:
            filesystems_combo.append_text(fs)

        self.grid.attach(filesystems_combo, 1, 8, 2, 1)

        self.widgets_dict["fs"] = [label_fs, filesystems_combo]

        return filesystems_combo

    def add_name_chooser(self):
        label_label = Gtk.Label(label=_("Label:"), xalign=1)
        self.grid.attach(label_label, 0, 9, 1, 1)

        label_entry = Gtk.Entry()
        self.grid.attach(label_entry, 1, 9, 2, 1)

        self.widgets_dict["label"] = [label_label, label_entry]

        name_label = Gtk.Label(label=_("Name:"), xalign=1)
        self.grid.attach(name_label, 3, 9, 1, 1)

        name_entry = Gtk.Entry()
        self.grid.attach(name_entry, 4, 9, 2, 1)

        self.widgets_dict["name"] = [name_label, name_entry]

        return label_entry, name_entry

    def add_encrypt_chooser(self):
        encrypt_label = Gtk.Label(label=_("Encrypt:"), xalign=1)
        self.grid.attach(encrypt_label, 0, 10, 1, 1)

        encrypt_check = Gtk.CheckButton()
        self.grid.attach(encrypt_check, 1, 10, 1, 1)

        self.widgets_dict["encrypt"] = [encrypt_label, encrypt_check]

        pass_label = Gtk.Label(label=_("Passphrase:"), xalign=1)
        self.grid.attach(pass_label, 3, 10, 1, 1)
        pass_label.set_sensitive(False)

        pass_entry = Gtk.Entry()
        pass_entry.set_visibility(False)
        pass_entry.set_property("caps-lock-warning", True)
        self.grid.attach(pass_entry, 4, 10, 2, 1)
        pass_entry.set_sensitive(False)

        encrypt_check.connect("toggled", lambda event: [pass_entry.set_sensitive(not pass_entry.get_sensitive()),
            pass_label.set_sensitive(not pass_label.get_sensitive())])

        return encrypt_check, pass_entry

    def add_mountpoint(self):
        mountpoint_label = Gtk.Label(label=_("Mountpoint:"), xalign=1)
        self.grid.attach(mountpoint_label, 0, 11, 1, 1)

        mountpoint_entry = Gtk.Entry()
        self.grid.attach(mountpoint_entry, 1, 11, 2, 1)

        self.widgets_dict["mountpoint"] = [mountpoint_label, mountpoint_entry]

        return mountpoint_entry

    def set_widgets_sensitive(self, widget_types):

        for widget_type in widget_types:
            if widget_type == "mountpoint" and not self.kickstart:
                continue

            for widget in self.widgets_dict[widget_type]:
                widget.set_sensitive(True)

    def set_widgets_unsensitive(self, widget_types):

        for widget_type in widget_types:
            if widget_type == "mountpoint" and not self.kickstart:
                continue

            for widget in self.widgets_dict[widget_type]:
                widget.set_sensitive(False)

    def on_devices_combo_changed(self, event):

        device_type = self._get_selected_device_type()
        self.update_parent_list()
        self.size_grid = self.add_size_areas()

        if self.free_type_chooser and device_type != "btrfs volume":
            self.remove_free_type_chooser()

        if device_type == "partition":
            self.set_widgets_sensitive(["label", "fs", "encrypt", "mountpoint", "size"])
            self.set_widgets_unsensitive(["name"])

            if self.free_device.isLogical:
                self.set_widgets_unsensitive(["encrypt"])

        elif device_type == "lvmpv":
            self.set_widgets_sensitive(["encrypt", "size"])
            self.set_widgets_unsensitive(["name", "label", "fs", "mountpoint"])

        elif device_type == "lvm":
            self.set_widgets_sensitive(["encrypt", "name", "size"])
            self.set_widgets_unsensitive(["label", "fs", "mountpoint"])

        elif device_type == "lvmvg":
            self.set_widgets_sensitive(["name"])
            self.set_widgets_unsensitive(["label", "fs", "mountpoint", "encrypt", "size"])

        elif device_type == "lvmlv":
            self.set_widgets_sensitive(["name", "fs", "mountpoint", "size"])
            self.set_widgets_unsensitive(["label", "encrypt"])

        elif device_type == "btrfs volume":
            self.set_widgets_sensitive(["name", "size"])
            self.set_widgets_unsensitive(["label", "fs", "mountpoint", "encrypt"])
            self.add_free_type_chooser()

        elif device_type == "btrfs subvolume":
            self.set_widgets_sensitive(["name"])
            self.set_widgets_unsensitive(["label", "fs", "mountpoint", "encrypt", "size"])

        self.update_raid_type_chooser()

    def fill_dialog(self):
        """ Fill in dialog with user's previous selection
        """

        # select parents

        # it = self.parents.get_iter_first()
        # FIXME: multiple parents can have same names (eg. more free space
        # devices on sigle disk for btrfs volumes)


        # set device type from Gtk.ComboBox
        i = 0
        for device in self.devices:
            if device[1] == self.old_input.device_type:
                self.devices_combo.set_active(i)
                break
            i += 1

        # set fs type from Gtk.ComboBox
        i = 0
        for fs in SUPPORTED_FS:
            if fs == self.old_input.filesystem:
                self.filesystems_combo.set_active(i)
                break
            i += 1

        if self.old_input.encrypt:
            self.encrypt_check.set_active(True)
            self.pass_entry.set_text(self.old_input.passphrase)

        # not neccessary if user actually filled these, we can set text to None
        self.label_entry.set_text(self.old_input.label)
        self.name_entry.set_text(self.old_input.name)

        if self.kickstart:
            self.mountpoint_entry.set_text(self.old_input.mountpoint)

        # we know user selected 'something', just set scale to it

        # self.unit_chooser.set_active(SUPPORTED_UNITS.index(self.old_input.unit))
        # self.scale.set_value(self.old_input.size.convertTo(self.old_input.unit))

        # self.parents = parents

    def _get_selected_device_type(self):
        tree_iter = self.devices_combo.get_active_iter()

        if tree_iter != None:
            model = self.devices_combo.get_model()
            device_type = model[tree_iter][1]

            return device_type

        else:
            return None

    def _get_number_selected_parents(self):

        num = 0

        for row in self.parents_store:
            if row[3]:
                num += 1

        return num

    def get_selection(self):

        device_type = self._get_selected_device_type()

        parents = []
        total_size = 0

        for size_area in self.size_areas:
            parents.append(size_area.get_selection())
            total_size += size_area.get_selection()[1]

        if self.free_type_chooser:
            if self.free_type_chooser[1].get_active():
                btrfs_type = "disks"
            elif self.free_type_chooser[2].get_active():
                btrfs_type = "partitions"

        else:
            btrfs_type = None

        if device_type in ["btrfs volume, lvm, lvmvg"]:
            raid_level = self.raid_combo.get_active_text()

        else:
            raid_level = None

        if self.kickstart:
            mountpoint = self.mountpoint_entry.get_text()

        else:
            mountpoint = None

        return UserSelection(device_type=device_type,
            size=total_size,
            filesystem=self.filesystems_combo.get_active_text(),
            name=self.name_entry.get_text(),
            label=self.label_entry.get_text(),
            mountpoint=mountpoint,
            encrypt=self.encrypt_check.get_active(),
            passphrase=self.pass_entry.get_text(),
            parents=parents,
            btrfs_type=btrfs_type,
            raid_level=raid_level)

class AddLabelDialog(Gtk.Dialog):
    """ Dialog window allowing user to add disklabel to disk
    """

    def __init__(self, parent_window, disk_device, disklabels):
        """

            :param parent_window: parent window
            :type parent_window: Gtk.Window
            :param disk_device: disk
            :type disk_device: blivet.DiskDevice
            :param disklabels: available disklabel types
            :type disklabels: list of str

        """

        self.disk_name = disk_device.name
        self.parent_window = parent_window
        self.disklabels = disklabels

        Gtk.Dialog.__init__(self, _("No partition table found on disk"), None,
            0, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_transient_for(self.parent_window)

        self.set_border_width(10)

        self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10,
            column_spacing=5)

        box = self.get_content_area()
        box.add(self.grid)

        self.add_labels()
        self.add_pt_chooser()

        self.show_all()

    def add_labels(self):

        self.info_label = Gtk.Label(label=_("A partition table is required " \
            "before partitions can be added.").format(self.disk_name))

        self.grid.attach(self.info_label, 0, 0, 4, 1) #left-top-width-height

    def add_pt_chooser(self):

        self.pts_store = Gtk.ListStore(str)

        for label in self.disklabels:
            self.pts_store.append([label])

        self.pts_store.append(["btrfs"])

        self.pts_combo = Gtk.ComboBox.new_with_model(self.pts_store)

        self.pts_combo.set_entry_text_column(0)
        self.pts_combo.set_active(0)

        if len(self.disklabels) > 1:
            self.pts_combo.set_sensitive(True)

        else:
            self.pts_combo.set_sensitive(False)

        self.label_list = Gtk.Label(label=_("Select new partition table type:"))

        self.grid.attach(self.label_list, 0, 1, 2, 1)
        self.grid.attach(self.pts_combo, 2, 1, 1, 1)

        self.pts_combo.connect("changed", self.on_pt_combo_changed)
        renderer_text = Gtk.CellRendererText()
        self.pts_combo.pack_start(renderer_text, True)
        self.pts_combo.add_attribute(renderer_text, "text", 0)


    def on_pt_combo_changed(self, event):

        tree_iter = self.pts_combo.get_active_iter()

        if tree_iter != None:
            model = self.pts_combo.get_model()
            device = model[tree_iter][0]

    def get_selection(self):
        tree_iter = self.pts_combo.get_active_iter()

        if tree_iter != None:
            model = self.pts_combo.get_model()
            label = model[tree_iter][0]

        return label
