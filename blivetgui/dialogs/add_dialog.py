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
# ---------------------------------------------------------------------------- #

import os

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

from gi.repository import Gtk, Gdk

from blivet import size

from decimal import Decimal

from ..dialogs import message_dialogs

from ..communication.proxy_utils import ProxyDataContainer

from . size_chooser import SizeChooser
from .helpers import is_name_valid, is_label_valid, is_mountpoint_valid

from ..i18n import _
from ..gui_utils import locate_ui_file

# ---------------------------------------------------------------------------- #

SUPPORTED_PESIZE = ["2 MiB", "4 MiB", "8 MiB", "16 MiB", "32 MiB", "64 MiB"]

# ---------------------------------------------------------------------------- #


class CacheArea(object):

    def __init__(self, add_dialog):

        self.add_dialog = add_dialog

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain("blivet-gui")
        self.builder.add_from_file(locate_ui_file("cache_area.ui"))

        self.grid = self.builder.get_object("grid_cache")

        self.liststore_pvs = self.update_pvs_list()
        self.checkbutton_cache = self.set_cache_button()
        self.combobox_type = self.builder.get_object("combobox_type")

        self.cache_widgets = [self.builder.get_object("treeview_pvs"),
                              self.builder.get_object("label_pvs"),
                              self.builder.get_object("label_type"),
                              self.combobox_type]
        self._all_widgets = self.builder.get_objects()

        self.size_area = self.add_size_area()

        for widget in self.cache_widgets:
            widget.hide()

    def set_cache_button(self):
        checkbutton_cache = self.builder.get_object("checkbutton_cache")
        checkbutton_cache.connect("toggled", self._on_cache_toggled)

        return checkbutton_cache

    def update_pvs_list(self):
        liststore_pvs = self.builder.get_object("liststore_pvs")

        renderer_toggle = self.builder.get_object("cellrenderertoggle1")
        renderer_toggle.connect("toggled", self._on_pv_toggled, liststore_pvs)

        for pv in self.add_dialog.parent_device.pvs:
            if pv.format.free < self._cache_min_size:
                continue  # not enough free space to be usable
            liststore_pvs.append([pv, False, pv.name, "lvmpv", str(pv.format.free), pv.disk.name])

        if len(liststore_pvs) > 0:  # just in some crazy case when there are no pvs
            liststore_pvs[0][1] = True  # pre-select first PV

        return liststore_pvs

    def add_size_area(self):
        area = SizeChooser(max_size=self._cache_max_size, min_size=self._cache_min_size)
        area.connect("size-changed", self._update_lv_max_size)
        area.selected_size = self.add_dialog.parent_device.pe_size  # set the minimal size for the cache

        self.grid.attach(area.grid, left=0, top=3, width=6, height=1)
        self.cache_widgets.append(area)

        return area

    def _update_lv_max_size(self, selected_size):
        self.add_dialog.update_size_areas_limits(max_size=self.add_dialog.parent_device.free_space - selected_size)

    @property
    def _cache_max_size(self):
        max_size = size.Size(0)
        selected_pvs = 0
        total_pvs = len(self.liststore_pvs)

        for line in self.liststore_pvs:
            if line[1]:
                selected_pvs += 1
                max_size += line[0].format.free

        if selected_pvs == total_pvs:
            # leave some space for the LV
            max_size -= self.add_dialog.parent_device.pe_size

        # max size of cache is limited by total vg free space available (minus min size of cached LV)
        return min(max_size, (self.add_dialog.parent_device.free_space - self.add_dialog.parent_device.pe_size))

    @property
    def _cache_min_size(self):
        # metada size - 8 MiB or 1 PE (if pe_size > 8 MiB)
        min_size = max(size.Size("8 MiB"), self.add_dialog.parent_device.pe_size)

        # at least 1 PE for the cache itself
        min_size += self.add_dialog.parent_device.pe_size

        # at least 8 MiB for pmspare (if it doesn't exist)
        if self.add_dialog.parent_device.pmspare_size < min_size:
            min_size += max(size.Size("8 MiB"), self.add_dialog.parent_device.pe_size)

        return min_size

    def _on_cache_toggled(self, button):
        if button.get_active():
            for widget in self.cache_widgets:
                widget.show()
            self.add_dialog.update_size_areas_limits(max_plus=-self._cache_min_size)
        else:
            for widget in self.cache_widgets:
                widget.hide()
            self.add_dialog.update_size_areas_limits(max_size=self.add_dialog.parent_device.free_space)

    def _on_pv_toggled(self, _button, path, store):
        store[path][1] = not store[path][1]

        if self._cache_max_size <= size.Size(0):
            # just to have same sane numbers when no PV is selected
            self.size_area.update_size_limits(min_size=self.add_dialog.parent_device.pe_size,
                                              max_size=self.add_dialog.parent_device.free_space)
            # set the max size for LV
            self.add_dialog.update_size_areas_limits(max_size=self.add_dialog.parent_device.free_space)
            self.size_area.set_sensitive(False)
        else:
            self.size_area.update_size_limits(max_size=self._cache_max_size)
            self.size_area.set_sensitive(True)

    def hide(self):
        for widget in self._all_widgets:
            if hasattr(widget, "hide"):
                widget.hide()

    def show(self):
        for widget in self._all_widgets:
            if hasattr(widget, "show"):
                widget.show()

    def set_sensitive(self, sensitive):
        for widget in self._all_widgets:
            if hasattr(widget, "set_sensitive"):
                widget.set_sensitive(sensitive)

    def get_selection(self):
        create_cache = self.checkbutton_cache.get_active()

        if not create_cache:
            return ProxyDataContainer(cache=False)

        cache_type = self.combobox_type.get_active_id()

        parents = []
        for line in self.liststore_pvs:
            if line[1]:
                parents.append(line[0])

        total_size = self.size_area.selected_size

        return ProxyDataContainer(cache=create_cache, type=cache_type, parents=parents, size=total_size)


class AdvancedOptions(object):

    def __init__(self, add_dialog, device_type, parent_device, free_device):

        self.add_dialog = add_dialog
        self.device_type = device_type
        self.parent_device = parent_device
        self.free_device = free_device

        self.expander = Gtk.Expander(label=_("Show advanced options"))
        self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10, column_spacing=5)
        self.grid.set_border_width(15)
        self.expander.add(self.grid)

        self.widgets = [self.expander, self.grid]

        if self.device_type in ("lvm", "lvmvg"):
            self.pesize_combo = self.lvm_options()

        elif self.device_type == "partition":
            self.partition_combo = self.partition_options()

        elif self.device_type == "lvmlv":
            self.cache_area = self.lvmlv_options()

    def lvm_options(self):

        label_pesize = Gtk.Label(label=_("PE Size:"), xalign=1)
        label_pesize.get_style_context().add_class("dim-label")
        self.grid.attach(label_pesize, 0, 0, 1, 1)

        pesize_combo = Gtk.ComboBoxText()
        pesize_combo.set_entry_text_column(0)
        pesize_combo.set_id_column(0)

        for pesize in SUPPORTED_PESIZE:
            if (2 * size.Size(pesize)) > self.free_device.size:
                # we need at least two free extents in the vg
                break
            pesize_combo.append_text(pesize)

        pesize_combo.connect("changed", self.on_pesize_changed)
        pesize_combo.set_active_id("4 MiB")

        self.grid.attach(pesize_combo, 1, 0, 2, 1)

        self.widgets.extend([label_pesize, pesize_combo])

        return pesize_combo

    def partition_options(self):

        label_pt_type = Gtk.Label(label=_("Partition type:"), xalign=1)
        label_pt_type.get_style_context().add_class("dim-label")
        self.grid.attach(label_pt_type, 0, 0, 1, 1)

        partition_store = Gtk.ListStore(str, str)

        types = []

        if self.free_device.is_logical:
            types = [(_("Logical"), "logical")]

        elif self._has_extended:
            types = [(_("Primary"), "primary")]

        elif self.parent_device.format.label_type in ("gpt",):
            types = [(_("Primary"), "primary")]

        else:
            types = [(_("Primary"), "primary"), (_("Extended"), "extended")]

        for part_type in types:
            partition_store.append(part_type)

        partition_combo = Gtk.ComboBox.new_with_model(partition_store)
        partition_combo.set_entry_text_column(0)

        self.grid.attach(partition_combo, 1, 0, 2, 1)
        renderer_text = Gtk.CellRendererText()
        partition_combo.pack_start(renderer_text, True)
        partition_combo.add_attribute(renderer_text, "text", 0)
        partition_combo.set_id_column(1)

        partition_combo.set_active(0)
        partition_combo.connect("changed", self.on_partition_type_changed)

        self.widgets.extend([label_pt_type, partition_combo])

        return partition_combo

    def lvmlv_options(self):
        cache_area = CacheArea(self.add_dialog)
        self.grid.attach(cache_area.grid, 0, 0, 1, 1)

        return cache_area

    @property
    def _has_extended(self):
        if self.parent_device.type == "disk":
            return self.parent_device.format.extended_partition is not None

        return False

    def on_pesize_changed(self, combo):
        pesize = combo.get_active_id()
        min_size = size.Size(pesize) * 2

        if self.add_dialog.encrypt_check.get_active():
            min_size += size.Size("2 MiB")

        self.add_dialog.update_size_areas_limits(min_size=min_size)

    def on_partition_type_changed(self, combo):

        part_type = combo.get_active_id()

        if part_type == "extended":
            self.add_dialog.hide_widgets(["fs", "encrypt", "label"])

        else:
            self.add_dialog.show_widgets(["fs", "encrypt", "label"])

    def destroy(self):
        for widget in self.widgets:
            widget.hide()
            widget.destroy()

    def show(self):
        for widget in self.widgets:
            widget.show()

    def hide(self):
        for widget in self.widgets:
            widget.hide()

    def set_sensitive(self, sensitivity):
        for widget in self.widgets:
            widget.set_sensitive(sensitivity)

    def get_selection(self):

        if self.device_type in ("lvm", "lvmvg"):
            return {"pesize": size.Size(self.pesize_combo.get_active_text())}

        elif self.device_type == "partition":
            return {"parttype": self.partition_combo.get_active_id()}

        elif self.device_type == "lvmlv":
            return self.cache_area.get_selection()


class AddDialog(Gtk.Dialog):
    """ Dialog window allowing user to add new partition including selecting
         size, fs, label etc.
    """

    def __init__(self, parent_window, parent_type, parent_device, free_device, free_pvs,
                 free_disks_regions, supported_raids, supported_fs, mountpoints, kickstart_mode=False):
        """

            :param str parent_type: type of (future) parent device
            :parama parent_device: future parent device
            :type parent_device: :class:`blivet.Device` instances
            :param free_device: selected free space device
            :type free_device: :class:`blivetgui.utils.FreeSpaceDevice` instances
            :param list free_pvs: list PVs with no VG
            :param free_disks_regions: list of free regions on non-empty disks
            :type free_disks_regions: list of :class:`blivetgui.utils.FreeSpaceDevice` instances
            :param list mountpoints: list of mountpoints in current devicetree
            :param bool kickstart_mode: kickstart mode

          """

        self.parent_window = parent_window

        self.parent_type = parent_type
        self.free_device = free_device
        self.parent_device = parent_device

        self.free_pvs = free_pvs
        self.free_disks_regions = free_disks_regions

        self.kickstart_mode = kickstart_mode

        self.supported_raids = supported_raids
        self.supported_fs = supported_fs
        self.mountpoints = mountpoints

        Gtk.Dialog.__init__(self, _("Create new device"), None, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_transient_for(self.parent_window)

        self.set_resizable(False)  # auto shrink after removing widgets

        self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10, column_spacing=5)
        self.grid.set_border_width(10)

        self.box = self.get_content_area()
        self.box.add(self.grid)

        self.widgets_dict = {}

        # do we have free_type_chooser?
        self.free_type_chooser = None

        self.filesystems_combo = self.add_fs_chooser()
        self.label_entry, self.name_entry = self.add_name_chooser()
        self.encrypt_check, self.pass_entry, self.pass2_entry = self.add_encrypt_chooser()
        self.parents_store = self.add_parent_list()

        self.raid_combo, self.raid_changed_signal = self.add_raid_type_chooser()

        if kickstart_mode:
            self.mountpoint_entry = self.add_mountpoint()

        self.devices_combo = self.add_device_chooser()
        self.devices_combo.connect("changed", self.on_devices_combo_changed)

        self.size_areas = []
        self.size_grid, self.size_scroll = self.add_size_areas()

        self.advanced = None

        self.md_type_combo = self.add_md_type_chooser()

        self.show_all()
        self.devices_combo.set_active(0)

        ok_button = self.get_widget_for_response(Gtk.ResponseType.OK)
        ok_button.connect("clicked", self.on_ok_clicked)

    def add_device_chooser(self):

        map_type_devices = {
            "disk": [(_("Partition"), "partition"), (_("LVM2 Storage"), "lvm"),
                     (_("LVM2 Physical Volume"), "lvmpv")],
            "lvmpv": [(_("LVM2 Volume Group"), "lvmvg")],
            "lvmvg": [(_("LVM2 Logical Volume"), "lvmlv"), (_("LVM2 ThinPool"), "lvmthinpool")],
            "luks/dm-crypt": [(_("LVM2 Volume Group"), "lvmvg")],
            "mdarray": [(_("LVM2 Volume Group"), "lvmvg")],
            "btrfs volume": [(_("Btrfs Subvolume"), "btrfs subvolume")],
            "lvmlv": [(_("LVM2 Snaphost"), "lvm snapshot")],
            "lvmthinpool": [(_("LVM2 Thin Logical Volume"), "lvmthinlv")]}

        label_devices = Gtk.Label(label=_("Device type:"), xalign=1)
        label_devices.get_style_context().add_class("dim-label")
        self.grid.attach(label_devices, 0, 0, 1, 1)

        if self.parent_type == "disk" and self.free_device.is_logical:
            devices = [(_("Partition"), "partition"), (_("LVM2 Storage"), "lvm"),
                       (_("LVM2 Physical Volume"), "lvmpv")]

        elif (self.parent_type == "disk" and not self.parent_device.format.type
              and self.free_device.size > size.Size("256 MiB")):
            devices = [(_("Btrfs Volume"), "btrfs volume")]

        else:
            devices = map_type_devices[self.parent_type]

            if self.parent_type == "disk" and len(self.free_disks_regions) > 1:
                devices.append((_("Software RAID"), "mdraid"))

            if self.parent_type == "disk" and self.free_device.size > size.Size("256 MiB"):
                devices.append((_("Btrfs Volume"), "btrfs volume"))

        devices_store = Gtk.ListStore(str, str)

        for device in devices:
            devices_store.append([device[0], device[1]])

        devices_combo = Gtk.ComboBox.new_with_model(devices_store)
        devices_combo.set_entry_text_column(0)
        devices_combo.set_id_column(1)

        if len(devices) == 1:
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

        self.grid.attach(label_list, 0, 2, 1, 1)
        self.grid.attach(parents_view, 1, 2, 4, 3)

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

            self.raid_combo.handler_block(self.raid_changed_signal)
            self.raid_combo.remove_all()

            for raid in self.supported_raids[device_type]:
                if raid.name == "container":
                    continue
                if num_parents >= raid.min_members:
                    self.raid_combo.append_text(raid.name)

            self.raid_combo.handler_unblock(self.raid_changed_signal)

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

    def on_raid_type_changed(self, _event):
        self.size_grid, self.size_scroll = self.add_size_areas()

    def add_raid_type_chooser(self):

        label_raid = Gtk.Label(label=_("RAID Level:"), xalign=1)
        label_raid.get_style_context().add_class("dim-label")
        self.grid.attach(label_raid, 0, 5, 1, 1)

        raid_combo = Gtk.ComboBoxText()
        raid_combo.set_entry_text_column(0)
        raid_combo.set_id_column(0)

        raid_changed_signal = raid_combo.connect("changed", self.on_raid_type_changed)

        self.grid.attach(raid_combo, 1, 5, 1, 1)

        self.widgets_dict["raid"] = [label_raid, raid_combo]

        return raid_combo, raid_changed_signal

    def on_free_space_type_toggled(self, button, name):
        if button.get_active():
            self.update_parent_list(parent_type=name)
            self.update_raid_type_chooser()

            self.size_grid, self.size_scroll = self.add_size_areas()

            if name == "disks":
                self.hide_widgets(["size"])

            else:
                self.show_widgets(["size"])

    def add_free_type_chooser(self):
        label_empty_type = Gtk.Label(label=_("Volumes based on:"), xalign=1)
        label_empty_type.get_style_context().add_class("dim-label")
        self.grid.attach(label_empty_type, 0, 1, 1, 1)

        button1 = Gtk.RadioButton.new_with_label_from_widget(None, _("Disks"))
        button1.connect("toggled", self.on_free_space_type_toggled, "disks")
        self.grid.attach(button1, 1, 1, 1, 1)

        button2 = Gtk.RadioButton.new_with_label_from_widget(button1, _("Partitions"))
        button2.connect("toggled", self.on_free_space_type_toggled, "partitions")
        self.grid.attach(button2, 2, 1, 1, 1)

        label_empty_type.show()
        button1.show()
        button2.show()

        if self.free_device.is_uninitialized_disk:
            button1.toggled()
            button1.set_sensitive(False)
            button2.set_sensitive(False)

        elif self.free_device.is_free_region:
            button2.set_active(True)
            button1.set_sensitive(False)
            button2.set_sensitive(False)

        else:
            button2.set_active(True)

        self.free_type_chooser = (label_empty_type, button1, button2)

    def _get_free_type(self):
        if self.free_type_chooser:
            button_disks = self.free_type_chooser[1]
            button_partitions = self.free_type_chooser[2]

        else:
            return None

        if button_disks.get_active():
            return "disks"

        elif button_partitions.get_active():
            return "partitions"

        else:
            return None

    def remove_free_type_chooser(self):
        for widget in self.free_type_chooser:
            widget.destroy()

        self.free_type_chooser = None

    def select_selected_free_region(self):
        """ In parent list select the free region user selected checkbox as checked
        """

        # for devices with only one parent just select the first (and only) one
        if len(self.parents_store) == 1:
            self.parents_store[0][2] = self.parents_store[0][3] = True
            return

        for row in self.parents_store:
            dev = row[0]
            free = row[1]

            if (dev.name == self.parent_device.name and
                (not hasattr(self.free_device, "start") or not self.free_device.start or
                 self.free_device.start == free.start)):
                row[2] = row[3] = True

        # TODO move selected iter at the top of the list

    def update_parent_list(self, parent_type=None):

        self.parents_store.clear()

        device_type = self._get_selected_device_type()

        if device_type == "lvmvg":
            for pv, free in self.free_pvs:
                self.parents_store.append([pv, free, False, False, pv.name,
                                           "lvmpv", str(free.size)])

        elif device_type in ("btrfs volume", "lvm", "mdraid"):

            for free in self.free_disks_regions:

                if device_type == "btrfs volume" and free.size < size.Size("256 MiB"):
                    continue

                disk = free.parents[0]

                if free.is_free_region and (parent_type == "partitions" or device_type in ("lvm", "mdraid")):
                    self.parents_store.append([disk, free, False, False, disk.name,
                                               "disk region", str(free.size)])

                elif not free.is_free_region:
                    self.parents_store.append([disk, free, False, False, disk.name,
                                               "disk", str(free.size)])

        elif device_type in ("lvm snapshot",):
            self.parents_store.append([self.parent_device, self.free_device, False, False,
                                       self.free_device.parents[0].name, "lvmvg", str(self.free_device.size)])

        elif device_type in ("lvmlv"):
            self.parents_store.append([self.parent_device, self.free_device, False, False,
                                       self.parent_device.name, "lvmvg", str(self.free_device.size)])

        else:
            self.parents_store.append([self.parent_device, self.free_device, False, False,
                                       self.parent_device.name, "disk", str(self.free_device.size)])

        self.select_selected_free_region()

    def on_cell_toggled(self, _event, path):

        if self.parents_store[path][2]:
            pass

        else:
            self.parents_store[path][3] = not self.parents_store[path][3]

            self.size_grid, self.size_scroll = self.add_size_areas()
            self.update_raid_type_chooser()

    def raid_member_max_size(self):

        device_type = self._get_selected_device_type()
        num_parents = self._get_number_selected_parents()

        if device_type not in self.supported_raids.keys() or num_parents == 1:
            return (False, None)

        elif self.raid_combo.get_active_text() in ("linear", "single"):
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

    def update_size_areas_selections(self, selected_size):
        """ Update all size areas to selected size
            (used for raids where all parents has same size)
        """

        device_type = self._get_selected_device_type()
        num_parents = self._get_number_selected_parents()

        if device_type not in self.supported_raids.keys() or num_parents == 1:
            return

        elif self.raid_combo.get_active_text() in ("linear", "single"):
            return

        else:
            for area, _parent in self.size_areas:
                area.selected_size = selected_size

    def update_size_areas_limits(self, min_size=None, max_size=None, min_plus=None, max_plus=None, min_multi=None, max_multi=None):
        for area, _parent in self.size_areas:
            if min_plus and not min_size:
                min_size = area.min_size + min_plus
            if min_multi and not min_size:
                min_size = area.min_size * min_multi

            if max_plus and not max_size:
                max_size = area.max_size + max_plus
            if max_multi and not max_size:
                max_size = area.max_size * max_multi

            if min_size is not None:
                area.min_size = min_size
            if max_size is not None:
                area.max_size = max_size

    def _destroy_size_areas(self):
        """ Remove existing size areas
        """

        self.widgets_dict["size"] = []

        if self.size_areas:
            for area, _parent in self.size_areas:
                area.destroy()

            self.size_scroll.destroy()
            self.size_grid.destroy()

            self.size_areas = []

    def add_size_areas(self):
        device_type = self._get_selected_device_type()

        # remove all existing size areas
        self._destroy_size_areas()

        size_scroll = Gtk.ScrolledWindow()
        size_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.NEVER)
        self.grid.attach(size_scroll, 0, 6, 6, 1)
        size_scroll.show()

        size_grid = Gtk.Grid(column_homogeneous=False, row_spacing=10, column_spacing=5)

        size_scroll.add(size_grid)
        size_grid.show()

        posititon = 0

        raid, max_size = self.raid_member_max_size()

        if device_type in ("lvmpv", "lvm"):
            min_size = size.Size("8 MiB")
        elif device_type in ("lvmlv", "lvmthinpool"):
            min_size = max(self.parent_device.pe_size, size.Size("1 MiB"))
        elif device_type in ("lvmthinlv", "lvm snapshot"):
            min_size = max(self.parent_device.vg.pe_size, size.Size("1 MiB"))
        elif device_type == "btrfs volume":
            min_size = size.Size("256 MiB")
        else:
            min_size = size.Size("1 MiB")

        for row in self.parents_store:
            if row[3]:
                if not raid:
                    max_size = row[1].size

                area = SizeChooser(max_size=max_size, min_size=min_size)
                area.connect("size-changed", self.update_size_areas_selections)

                size_grid.attach(area.grid, 0, posititon, 1, 1)

                self.widgets_dict["size"].append(area)
                self.size_areas.append((area, row[0]))

                posititon += 1

        for area, _parent in self.size_areas:
            area.show()

            if device_type in ("lvmvg", "btrfs subvolume") or self._get_free_type() == "disks":
                area.set_sensitive(False)

        # TODO: this needs better rewrite, maybe own method
        size_area_height = size_grid.size_request().height
        size_area_width = size_grid.size_request().width
        screen_height = Gdk.Screen.get_default().get_height()
        screen_width = Gdk.Screen.get_default().get_width()
        dialog_height = self.size_request().height

        size_diff = int((screen_height * 0.7) - dialog_height)

        if size_diff < 0:
            # dialog is largen than 70 % of screen
            areas_to_display = len(self.size_areas) - (abs(size_diff) / (size_area_height / len(self.size_areas)))

            if areas_to_display < 1:
                # always display at least one size area

                size_scroll.set_size_request(size_area_width, int(size_area_height / len(self.size_areas)))
                size_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

            else:
                if size_area_height > screen_width * 0.7:
                    size_scroll.set_size_request(screen_width * 0.7,
                                                 int(size_area_height / len(self.size_areas)) * areas_to_display)
                    size_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

                else:
                    size_scroll.set_size_request(size_area_width,
                                                 int(size_area_height / len(self.size_areas)) * areas_to_display)
                    size_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        else:
            if size_area_width > screen_width * 0.7:
                size_scroll.set_size_request(screen_width * 0.7, size_area_height)
                size_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)

            else:
                size_grid.set_size_request(size_area_width, size_area_height + 20)
                size_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.NEVER)

        return size_grid, size_scroll

    def add_md_type_chooser(self):
        label_md_type = Gtk.Label(label=_("MDArray type:"), xalign=1)
        label_md_type.get_style_context().add_class("dim-label")
        self.grid.attach(label_md_type, 0, 7, 1, 1)

        md_type_store = Gtk.ListStore(str, str)

        for md_type in ((_("Partition"), "partition"), (_("LVM Physical Volume"), "lvmpv")):
            md_type_store.append(md_type)

        md_type_combo = Gtk.ComboBox.new_with_model(md_type_store)
        md_type_combo.set_entry_text_column(0)

        self.grid.attach(md_type_combo, 1, 7, 2, 1)
        renderer_text = Gtk.CellRendererText()
        md_type_combo.pack_start(renderer_text, True)
        md_type_combo.add_attribute(renderer_text, "text", 0)
        md_type_combo.set_id_column(1)

        md_type_combo.set_active_id("partition")
        md_type_combo.connect("changed", self.on_md_type_changed)

        self.widgets_dict["mdraid"] = [label_md_type, md_type_combo]

        return md_type_combo

    def on_md_type_changed(self, _event):
        if self.md_type_combo.get_active_id() == "partition":
            self.show_widgets(["fs"])

        else:
            self.hide_widgets(["fs"])

    def add_fs_chooser(self):
        label_fs = Gtk.Label(label=_("Filesystem:"), xalign=1)
        label_fs.get_style_context().add_class("dim-label")
        self.grid.attach(label_fs, 0, 8, 1, 1)

        filesystems_combo = Gtk.ComboBoxText()
        filesystems_combo.set_entry_text_column(0)
        filesystems_combo.set_id_column(0)

        for fs in self.supported_fs:
            filesystems_combo.append_text(fs)

        self.grid.attach(filesystems_combo, 1, 8, 2, 1)

        if "ext4" in self.supported_fs:
            filesystems_combo.set_active(self.supported_fs.index("ext4"))
        else:
            filesystems_combo.set_active(0)

        filesystems_combo.connect("changed", self.on_filesystems_combo_changed)

        self.widgets_dict["fs"] = [label_fs, filesystems_combo]

        return filesystems_combo

    def on_filesystems_combo_changed(self, combo):
        selection = combo.get_active_text()

        if selection in ("swap",):
            self.hide_widgets(["label", "mountpoint"])

        else:
            device_type = self._get_selected_device_type()

            if device_type == "partition":
                self.show_widgets(["label", "mountpoint"])
            else:
                self.show_widgets(["mountpoint"])

    def add_name_chooser(self):
        label_label = Gtk.Label(label=_("Label:"), xalign=1)
        label_label.get_style_context().add_class("dim-label")
        self.grid.attach(label_label, 0, 9, 1, 1)

        label_entry = Gtk.Entry()
        self.grid.attach(label_entry, 1, 9, 2, 1)

        self.widgets_dict["label"] = [label_label, label_entry]

        name_label = Gtk.Label(label=_("Name:"), xalign=1)
        name_label.get_style_context().add_class("dim-label")
        self.grid.attach(name_label, 0, 9, 1, 1)

        name_entry = Gtk.Entry()
        self.grid.attach(name_entry, 1, 9, 2, 1)

        self.widgets_dict["name"] = [name_label, name_entry]

        return label_entry, name_entry

    def add_mountpoint(self):
        mountpoint_label = Gtk.Label(label=_("Mountpoint:"), xalign=1)
        mountpoint_label.get_style_context().add_class("dim-label")
        self.grid.attach(mountpoint_label, 0, 10, 1, 1)

        mountpoint_entry = Gtk.Entry()
        self.grid.attach(mountpoint_entry, 1, 10, 2, 1)

        self.widgets_dict["mountpoint"] = [mountpoint_label, mountpoint_entry]

        return mountpoint_entry

    def add_encrypt_chooser(self):
        encrypt_label = Gtk.Label(label=_("Encrypt:"), xalign=1)
        encrypt_label.get_style_context().add_class("dim-label")
        self.grid.attach(encrypt_label, 0, 11, 1, 1)

        encrypt_check = Gtk.CheckButton()
        self.grid.attach(encrypt_check, 1, 11, 1, 1)

        self.widgets_dict["encrypt"] = [encrypt_label, encrypt_check]

        pass_label = Gtk.Label(label=_("Passphrase:"), xalign=1)
        pass_label.get_style_context().add_class("dim-label")
        self.grid.attach(pass_label, 0, 12, 1, 1)

        pass_entry = Gtk.Entry()
        pass_entry.set_visibility(False)
        pass_entry.set_property("caps-lock-warning", True)
        self.grid.attach(pass_entry, 1, 12, 2, 1)

        pass2_label = Gtk.Label(label=_("Repeat Passphrase:"), xalign=1)
        pass2_label.get_style_context().add_class("dim-label")
        self.grid.attach(pass2_label, 0, 13, 1, 1)

        pass2_entry = Gtk.Entry()
        pass2_entry.set_visibility(False)
        pass2_entry.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "dialog-error-symbolic.symbolic")
        pass2_entry.set_icon_activatable(Gtk.EntryIconPosition.SECONDARY, False)
        pass2_entry.set_icon_tooltip_markup(Gtk.EntryIconPosition.SECONDARY, _("Passphrases don't match."))
        pass2_entry.connect("changed", self.on_passphrase_changed, pass_entry)
        self.grid.attach(pass2_entry, 1, 13, 2, 1)

        self.widgets_dict["passphrase"] = [pass_label, pass_entry, pass2_label, pass2_entry]

        encrypt_check.connect("toggled", self.on_encrypt_check)

        return encrypt_check, pass_entry, pass2_entry

    def add_advanced_options(self):

        device_type = self._get_selected_device_type()

        if self.advanced:
            self.advanced.destroy()

        if device_type in ("lvm", "lvmvg", "partition", "lvmlv"):
            self.advanced = AdvancedOptions(self, device_type, self.parent_device, self.free_device)
            self.widgets_dict["advanced"] = [self.advanced]

            self.grid.attach(self.advanced.expander, 0, 14, 6, 1)

        else:
            self.advanced = None
            self.widgets_dict["advanced"] = []

    def show_widgets(self, widget_types):

        for widget_type in widget_types:
            if widget_type == "mountpoint" and not self.kickstart_mode:
                continue

            elif widget_type == "size":
                for widget in self.widgets_dict[widget_type]:
                    widget.set_sensitive(True)

            else:
                for widget in self.widgets_dict[widget_type]:
                    widget.show()

    def hide_widgets(self, widget_types):

        for widget_type in widget_types:
            if widget_type == "mountpoint" and not self.kickstart_mode:
                continue

            elif widget_type == "size":
                for widget in self.widgets_dict[widget_type]:
                    widget.set_sensitive(False)

            else:
                for widget in self.widgets_dict[widget_type]:
                    widget.hide()

                    if isinstance(widget, Gtk.Entry):
                        widget.set_text("")

    def on_encrypt_check(self, _toggle):
        if self.encrypt_check.get_active():
            self.show_widgets(["passphrase"])
            self.update_size_areas_limits(min_plus=size.Size("2 MiB"))
        else:
            self.hide_widgets(["passphrase"])
            self.update_size_areas_limits(min_plus=size.Size("-2 MiB"))

    def on_passphrase_changed(self, confirm_entry, passphrase_entry):
        if passphrase_entry.get_text() == confirm_entry.get_text():
            confirm_entry.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "emblem-ok-symbolic.symbolic")
            confirm_entry.set_icon_tooltip_markup(Gtk.EntryIconPosition.SECONDARY, _("Passphrases match."))
        else:
            confirm_entry.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "dialog-error-symbolic.symbolic")
            confirm_entry.set_icon_tooltip_markup(Gtk.EntryIconPosition.SECONDARY, _("Passphrases don't match."))

    def on_devices_combo_changed(self, _event):

        device_type = self._get_selected_device_type()

        self.update_parent_list()
        self.add_advanced_options()
        self.encrypt_check.set_active(False)
        self.size_grid, self.size_scroll = self.add_size_areas()

        if self.free_type_chooser and device_type != "btrfs volume":
            self.remove_free_type_chooser()

        if device_type == "partition":
            self.show_widgets(["label", "fs", "encrypt", "mountpoint", "size", "advanced"])
            self.hide_widgets(["name", "passphrase", "mdraid"])

        elif device_type == "lvmpv":
            self.show_widgets(["encrypt", "size"])
            self.hide_widgets(["name", "label", "fs", "mountpoint", "passphrase", "advanced", "mdraid"])

        elif device_type == "lvm":
            self.show_widgets(["encrypt", "name", "size", "advanced"])
            self.hide_widgets(["label", "fs", "mountpoint", "passphrase", "mdraid"])

        elif device_type == "lvmvg":
            self.show_widgets(["name", "advanced"])
            self.hide_widgets(["label", "fs", "mountpoint", "encrypt", "size", "passphrase", "mdraid"])

        elif device_type in ("lvmlv"):
            self.show_widgets(["name", "fs", "mountpoint", "size", "advanced"])
            self.hide_widgets(["label", "encrypt", "passphrase", "mdraid"])

            if self.parent_device.free_space < self.advanced.cache_area._cache_min_size:
                self.advanced.cache_area.set_sensitive(False)

        elif device_type in ("lvmthinlv"):
            self.show_widgets(["name", "fs", "mountpoint", "size"])
            self.hide_widgets(["label", "encrypt", "passphrase", "advanced", "mdraid"])

        elif device_type == "btrfs volume":
            self.show_widgets(["name", "size", "mountpoint"])
            self.hide_widgets(["label", "fs", "encrypt", "passphrase", "advanced", "mdraid"])
            self.add_free_type_chooser()

        elif device_type == "btrfs subvolume":
            self.show_widgets(["name", "mountpoint"])
            self.hide_widgets(["label", "fs", "encrypt", "size", "passphrase", "advanced", "mdraid"])

        elif device_type == "mdraid":
            self.show_widgets(["name", "size", "mountpoint", "fs", "mdraid"])
            self.hide_widgets(["label", "encrypt", "passphrase", "advanced"])

        elif device_type == "lvm snapshot":
            self.show_widgets(["name", "size"])
            self.hide_widgets(["label", "fs", "encrypt", "passphrase", "advanced", "mdraid", "mountpoint"])

        elif device_type == "lvmthinpool":
            self.show_widgets(["name", "size"])
            self.hide_widgets(["label", "fs", "encrypt", "passphrase", "advanced", "mdraid", "mountpoint"])
            self.update_size_areas_limits(max_multi=Decimal(0.8))

        self.update_raid_type_chooser()

    def _get_selected_device_type(self):
        tree_iter = self.devices_combo.get_active_iter()

        if tree_iter:
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

    def validate_user_input(self):
        """ Validate data input
        """

        user_input = self.get_selection()

        if not user_input.filesystem and user_input.device_type == "partition" \
           and user_input.advanced["parttype"] != "extended":
            msg = _("Filesystem type must be specified when creating new partition.")
            message_dialogs.ErrorDialog(self, msg)

            return False

        if not user_input.filesystem and user_input.device_type == "lvmlv":
            msg = _("Filesystem type must be specified when creating new logical volume.")
            message_dialogs.ErrorDialog(self, msg)

            return False

        if user_input.encrypt and not user_input.passphrase:
            msg = _("Passphrase not specified.")
            message_dialogs.ErrorDialog(self, msg)

            return False

        if user_input.mountpoint and not os.path.isabs(user_input.mountpoint):
            msg = _("\"{0}\" is not a valid mountpoint.").format(user_input.mountpoint)
            message_dialogs.ErrorDialog(self, msg)

            return False

        if user_input.device_type == "mdraid" and len(user_input.parents) == 1:
            msg = _("Please select at least two parent devices.")
            message_dialogs.ErrorDialog(self, msg)

            return False

        if self.kickstart_mode and user_input.mountpoint:
            valid, msg = is_mountpoint_valid(self.mountpoints, user_input.mountpoint)
            if not valid:
                message_dialogs.ErrorDialog(self, msg)
                return False

        if user_input.name and not is_name_valid(user_input.device_type, user_input.name):
            msg = _("\"{0}\" is not a valid name.").format(user_input.name)
            message_dialogs.ErrorDialog(self, msg)
            return False

        if user_input.label and not is_label_valid(user_input.filesystem, user_input.label):
            msg = _("\"{0}\" is not a valid label.").format(user_input.label)
            message_dialogs.ErrorDialog(self, msg)
            return False

        if self.pass_entry.get_text() != self.pass2_entry.get_text():
            msg = _("Provided passphrases do not match.")
            message_dialogs.ErrorDialog(self, msg)
            return False

        return True

    def on_ok_clicked(self, _event):
        if not self.validate_user_input():
            self.run()

    def get_selection(self):
        device_type = self._get_selected_device_type()

        parents = []
        total_size = 0

        for size_area, parent in self.size_areas:
            parents.append([parent, size_area.get_selection()])
            total_size += size_area.get_selection()

        if self.free_type_chooser:
            if self.free_type_chooser[1].get_active():
                btrfs_type = "disks"
            elif self.free_type_chooser[2].get_active():
                btrfs_type = "partitions"
        else:
            btrfs_type = None

        if device_type in ("btrfs volume", "lvmlv", "mdraid"):
            raid_level = self.raid_combo.get_active_text()
        else:
            raid_level = None

        if self.kickstart_mode:
            mountpoint = self.mountpoint_entry.get_text()
        else:
            mountpoint = None

        if self.advanced:
            advanced = self.advanced.get_selection()
        else:
            advanced = None

        if device_type == "mdraid" and self.md_type_combo.get_active_id() == "lvmpv":
            filesystem = "lvmpv"
        elif device_type in ("mdraid", "partition", "lvmlv", "lvmthinlv"):
            filesystem = self.filesystems_combo.get_active_text()
        else:
            filesystem = None

        return ProxyDataContainer(device_type=device_type,
                                  size=total_size,
                                  filesystem=filesystem,
                                  name=self.name_entry.get_text(),
                                  label=self.label_entry.get_text(),
                                  mountpoint=mountpoint,
                                  encrypt=self.encrypt_check.get_active(),
                                  passphrase=self.pass_entry.get_text(),
                                  parents=parents,
                                  btrfs_type=btrfs_type,
                                  raid_level=raid_level,
                                  advanced=advanced)
