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

from gi.repository import Gtk

from blivet import size
from blivet.devicelibs import crypto, lvm
from blivet.formats.fs import BTRFS

from ..dialogs import message_dialogs

from ..communication.proxy_utils import ProxyDataContainer

from . size_chooser import SizeArea
from .widgets import RaidChooser, EncryptionChooser
from .helpers import is_name_valid, is_label_valid, is_mountpoint_valid, supported_raids, get_monitor_size

from ..i18n import _
from ..config import config

# ---------------------------------------------------------------------------- #

SUPPORTED_PESIZE = ["2 MiB", "4 MiB", "8 MiB", "16 MiB", "32 MiB", "64 MiB"]
SUPPORTED_CHUNK = ["32 KiB", "64 KiB", "128 KiB", "256 KiB", "512 KiB", "1 MiB",
                   "2 MiB", "4 MiB", "8 MiB"]
POOL_RESERVED = 0.8

# ---------------------------------------------------------------------------- #


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

        elif self.device_type == "mdraid":
            self.chunk_combo = self.mdraid_options()

    def lvm_options(self):

        label_pesize = Gtk.Label(label=_("PE Size:"), xalign=1)
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
        self.grid.attach(label_pt_type, 0, 0, 1, 1)

        partition_store = Gtk.ListStore(str, str)

        types = []

        if self.parent_device.format.label_type == "msdos":
            if self.free_device.is_logical:
                types = [(_("Logical"), "logical")]
            elif self._has_extended:
                types = [(_("Primary"), "primary")]
            else:
                types = [(_("Primary"), "primary"), (_("Extended"), "extended")]
        else:
            types = [(_("Primary"), "primary")]

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

        if len(types) == 1:
            partition_combo.set_sensitive(False)

        self.widgets.extend([label_pt_type, partition_combo])

        return partition_combo

    def mdraid_options(self):
        label_chunk = Gtk.Label(label=_("Chunk Size:"), xalign=1)
        self.grid.attach(label_chunk, 0, 0, 1, 1)

        chunk_combo = Gtk.ComboBoxText().new_with_entry()
        chunk_combo.set_entry_text_column(0)
        chunk_combo.set_id_column(0)

        for chunk in SUPPORTED_CHUNK:
            chunk_combo.append_text(chunk)

        chunk_combo.set_active_id("512 KiB")

        self.grid.attach(chunk_combo, 1, 0, 2, 1)

        self.widgets.extend([label_chunk, chunk_combo])

        return chunk_combo

    @property
    def _has_extended(self):
        if self.parent_device.type == "disk":
            return self.parent_device.format.extended_partition is not None

        return False

    def on_pesize_changed(self, combo):
        pesize = combo.get_active_id()
        min_size = size.Size(pesize) * 2

        self.add_dialog.update_size_area_limits(min_size=min_size)

    def on_partition_type_changed(self, combo):

        part_type = combo.get_active_id()

        if part_type == "extended":
            self.add_dialog.hide_widgets(["fs", "encrypt", "label", "mountpoint"])

        else:
            self.add_dialog.show_widgets(["fs", "encrypt", "label", "mountpoint"])

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

    def validate_user_input(self):
        if self.device_type == "mdraid":
            try:
                chunk_size = size.Size(self.chunk_combo.get_active_text())
            except ValueError:
                msg = _("'{0}' is not a valid chunk size specification.").format(self.chunk_combo.get_active_text())
                message_dialogs.ErrorDialog(self.add_dialog, msg,
                                            not self.add_dialog.installer_mode)  # do not show decoration in installer mode
                return False
            if chunk_size % size.Size("4 KiB") != size.Size(0):
                msg = _("Chunk size must be multiple of 4 KiB.")
                message_dialogs.ErrorDialog(self.add_dialog, msg,
                                            not self.add_dialog.installer_mode)  # do not show decoration in installer mode
                return False

        return True

    def get_selection(self):

        if self.device_type in ("lvm", "lvmvg"):
            return {"pesize": size.Size(self.pesize_combo.get_active_text())}

        elif self.device_type == "partition":
            return {"parttype": self.partition_combo.get_active_id()}

        elif self.device_type == "mdraid":
            return {"chunk_size": size.Size(self.chunk_combo.get_active_text())}


class AddDialog(Gtk.Dialog):
    """ Dialog window allowing user to add new partition including selecting
         size, fs, label etc.
    """

    def __init__(self, parent_window, selected_parent, selected_free, available_free,
                 supported_filesystems, mountpoints=None, installer_mode=False):
        """

            :param str parent_type: type of (future) parent device
            :param parent_device: future parent device
            :type parent_device: :class:`blivet.Device` instances
            :param free_device: selected free space device
            :type free_device: :class:`blivetgui.utils.FreeSpaceDevice` instances
            :param list free_pvs: list PVs with no VG
            :param free_disks_regions: list of free regions on non-empty disks
            :type free_disks_regions: list of :class:`blivetgui.utils.FreeSpaceDevice` instances
            :param list mountpoints: list of mountpoints in current devicetree
            :param bool installer_mode: installer mode

          """

        self.parent_window = parent_window

        self.selected_parent = selected_parent
        self.selected_free = selected_free

        self.available_free = available_free

        self.installer_mode = installer_mode
        self.mountpoints = mountpoints

        self.supported_filesystems = supported_filesystems
        self.supported_raids = supported_raids()

        Gtk.Dialog.__init__(self)

        self.set_title(_("Create new device"))
        self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                         Gtk.STOCK_OK, Gtk.ResponseType.OK)
        self.set_transient_for(self.parent_window)

        if self.installer_mode:
            self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
            self.set_decorated(False)

        self.set_resizable(False)  # auto shrink after removing widgets

        mwidth, mheight = get_monitor_size(self.parent_window)
        self.max_height = int(mheight * 0.80)  # take at most 80 % of current monitor height
        self.max_width = int(mwidth * 0.80)  # take at most 80 % of current monitor width

        self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10, column_spacing=5)
        self.grid.set_border_width(10)

        self.scrolledwindow = Gtk.ScrolledWindow()
        self.scrolledwindow.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.NEVER)

        self.box = self.get_content_area()
        self.box.add(self.scrolledwindow)

        self.scrolledwindow.add(self.grid)

        self.widgets_dict = {}

        self.filesystems_store, self.filesystems_combo = self.add_fs_chooser()
        self.label_entry, self.name_entry = self.add_name_chooser()
        self.parents_store = self.add_parent_list()

        # encryption chooser
        self._encryption_chooser = EncryptionChooser()
        self._encryption_chooser.connect("encrypt-toggled", self.on_encrypt_check)
        self.grid.attach(self._encryption_chooser.grid, 0, 12, 3, 1)
        self.widgets_dict["encrypt"] = [self._encryption_chooser]

        # raid chooser
        self._raid_chooser = RaidChooser()
        self._raid_chooser.connect("changed", self.on_raid_type_changed)
        self.grid.attach(self._raid_chooser.box, 0, 5, 3, 1)
        self.widgets_dict["raid"] = [self._raid_chooser]

        if self.installer_mode:
            self.mountpoint_entry = self.add_mountpoint()

        self.devices_combo = self.add_device_chooser()
        self.devices_combo.connect("changed", self.on_devices_combo_changed)

        self.size_area = None
        self.add_size_area()

        self.advanced = None

        self.md_type_combo = self.add_md_type_chooser()

        # adjust size/scrolling of the dialog with every change of its size
        self._resize_handler = self.connect("configure-event", self.scrolled_adjust)

        self.show_all()

        self.devices_combo.set_active(0)

        ok_button = self.get_widget_for_response(Gtk.ResponseType.OK)
        ok_button.connect("clicked", self.on_ok_clicked)

    def scrolled_adjust(self, _widget, _event):
        """ Adjust current size of the dialog (and add scrollbars) if it's bigger
            than size limits
        """

        preferred_size = self.scrolledwindow.get_preferred_size()
        if preferred_size.natural_size:
            height = preferred_size.natural_size.height
            width = preferred_size.natural_size.width
        elif preferred_size.minimum_size:
            height = preferred_size.minimum_size.height
            width = preferred_size.minimum_size.width
        else:
            # this should never happened, but who knows what Gtk can really do
            width = None
            height = None

        with self.handler_block(self._resize_handler):
            if width is None or height is None:
                # something is really broken, just set everything to auto and
                # hope it will somehow work
                self.scrolledwindow.set_size_request(self.max_width, self.max_height)
                self.scrolledwindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            elif height >= self.max_height and width >= self.max_width:
                self.scrolledwindow.set_size_request(self.max_width, self.max_height)
                self.scrolledwindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            elif height >= self.max_height and width < self.max_width:
                self.scrolledwindow.set_size_request(-1, self.max_height)
                self.scrolledwindow.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            elif height < self.max_height and width >= self.max_width:
                self.scrolledwindow.set_size_request(self.max_width, -1)
                self.scrolledwindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
            else:
                self.scrolledwindow.set_size_request(-1, -1)
                self.scrolledwindow.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.NEVER)

    def _available_add_types(self):
        """ Get device types available to add to this device """

        types = []

        if self.selected_parent.is_disk and self.selected_parent.format.type == "disklabel":
            types.append((_("Partition"), "partition"))

            if self.selected_free.size > lvm.LVM_PE_SIZE * 2:
                types.extend([(_("LVM2 Volume Group"), "lvm")])

            if self.selected_free.size > BTRFS._min_size:
                types.append((_("Btrfs Volume"), "btrfs volume"))

            if len([f[0] for f in self.available_free if f[0] == "free"]) > 1:  # number of free disk regions
                types.append((_("Software RAID"), "mdraid"))

        elif self.selected_parent.type == "lvmvg":
            types.extend([(_("LVM2 Logical Volume"), "lvmlv"), (_("LVM2 ThinPool"), "lvmthinpool")])

        elif (self.selected_parent.format.type == "lvmpv" and not self.selected_parent.format.vg_name and
              self.selected_parent.size >= lvm.LVM_PE_SIZE * 2):
            types.append((_("LVM2 Volume Group"), "lvmvg"))

        elif self.selected_parent.type == "lvmlv":
            types.append((_("LVM2 Snaphost"), "lvm snapshot"))

        elif self.selected_parent.type == "lvmthinlv":
            types.append((_("LVM2 Thin Snaphost"), "lvm thinsnapshot"))

        elif self.selected_parent.type == "lvmthinpool":
            types.append((_("LVM2 Thin Logical Volume"), "lvmthinlv"))

        elif self.selected_parent.type in ("btrfs volume", "btrfs subvolume"):
            types.append((_("Btrfs Subvolume"), "btrfs subvolume"))

        return types

    def add_device_chooser(self):

        label_devices = Gtk.Label(label=_("Device type:"), xalign=1)
        self.grid.attach(label_devices, 0, 0, 1, 1)

        devices_store = Gtk.ListStore(str, str)

        devices = self._available_add_types()

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

        self.grid.attach(label_list, 0, 2, 1, 1)
        self.grid.attach(parents_view, 1, 2, 4, 3)

        return parents_store

    def update_raid_type_chooser(self, keep_selection=False):

        # save previously selected raid type
        selected = self._raid_chooser.selected_level

        # update the chooser
        num_parents = self._get_number_selected_parents()
        self._raid_chooser.update(self.selected_type, num_parents)

        if keep_selection and selected:
            try:
                self._raid_chooser = selected
            except ValueError:
                pass
            else:
                return

        # no previous selection -- just automatically select some 'sane' level
        self._raid_chooser.autoselect(self.selected_type)

    def on_raid_type_changed(self, _widget):
        self.add_size_area()

        if self.selected_type == "mdraid":
            self.add_advanced_options()
            self.show_widgets(["advanced"])

    def select_selected_free_region(self):
        """ In parent list select the free region user selected checkbox as checked
        """

        # for devices with only one parent just select the first (and only) one
        if len(self.parents_store) == 1:
            self.parents_store[0][2] = self.parents_store[0][3] = True
            return

        for row in self.parents_store:
            dev = row[0]
            free = row[1].size

            if dev.name == self.selected_parent.name and free == self.selected_free.size:
                row[2] = row[3] = True

        # TODO move selected iter at the top of the list

    def update_parent_list(self):

        self.parents_store.clear()

        if self.selected_type == "lvmvg":
            for ftype, fdevice in self.available_free:
                if ftype == "lvmpv" and fdevice.size >= lvm.LVM_PE_SIZE * 2:
                    self.parents_store.append([fdevice.parents[0], fdevice, False, False,
                                               fdevice.parents[0].name, ftype, str(fdevice.size)])

        elif self.selected_type in ("btrfs volume", "lvm", "mdraid"):
            for ftype, fdevice in self.available_free:
                if ftype == "free":
                    if self.selected_type == "btrfs volume" and fdevice.size < BTRFS._min_size:
                        # too small for new btrfs
                        continue

                    self.parents_store.append([fdevice.disk, fdevice, False, False,
                                               fdevice.disk.name, "disk region", str(fdevice.size)])

        elif self.selected_type in ("lvm snapshot",):
            # parent for a LVM snaphost is actually the VG, not the selected LV
            self.parents_store.append([self.selected_parent, self.selected_free, False, False,
                                       self.selected_parent.vg.name, "lvmvg", str(self.selected_free.size)])

        elif self.selected_type in ("lvm thinsnapshot",):
            # parent for an LVM thinsnaphost is actually the pool, not the selected thinLV
            self.parents_store.append([self.selected_parent, self.selected_free, False, False,
                                       self.selected_parent.pool.name, "lvmvg", str(self.selected_free.size)])

        else:
            self.parents_store.append([self.selected_parent, self.selected_free, False, False,
                                       self.selected_parent.name, self.selected_parent.type, str(self.selected_free.size)])

        self.select_selected_free_region()

    def on_cell_toggled(self, _event, path):

        if self.parents_store[path][2]:
            pass

        else:
            self.parents_store[path][3] = not self.parents_store[path][3]

            self.update_raid_type_chooser()
            self.add_size_area()

    def raid_member_max_size(self):

        device_type = self.selected_type
        num_parents = self._get_number_selected_parents()
        level = self._raid_chooser.selected_level

        if device_type not in self.supported_raids.keys() or num_parents == 1:
            return (False, None)

        elif level and level.name in ("linear", "single"):
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

    def update_size_area_limits(self, min_size=None, reserved_size=None):
        if min_size is not None:
            self.size_area.set_parents_min_size(min_size)
        if reserved_size is not None:
            self.size_area.set_parents_reserved_size(reserved_size)

    def _get_parent_min_size(self):
        """ Get minimal size for parent devices of newly created device.
            This value depends on type of created device.

            - partition: no limit
            - lv, thinpool (including thin): one extent
            - lvm: 2 * lvm.LVM_PE_SIZE
            - btrfs volume: 256 MiB
            - luks: crypto.LUKS_METADATA_SIZE

        """

        device_type = self.selected_type

        if device_type in ("lvmlv", "lvmthinpool"):
            min_size = self.selected_parent.pe_size
        elif device_type == "lvm":
            min_size = lvm.LVM_PE_SIZE * 2
        elif device_type in ("lvmthinlv", "lvm snapshot"):
            min_size = self.selected_parent.vg.pe_size
        elif device_type == "btrfs volume":
            min_size = BTRFS._min_size
        else:
            min_size = size.Size("1 MiB")

        return min_size

    def _get_parent_max_size(self, parent_device, free_size):
        """ Get maximal size for parent devices of newly created device.
            This value depends on type of created device.
        """

        device_type = self.selected_type

        if device_type in ("partition", "lvm", "btrfs volume", "mdraid"):
            # partition or a device we are going to create partition as a parent
            # --> we need to use disklabel limit
            disklabel_limit = size.Size(parent_device.format.parted_disk.maxPartitionLength * parent_device.format.sector_size)
            max_size = min(disklabel_limit, free_size)
        else:
            max_size = free_size

        return max_size

    def _get_parents(self):
        """ Get selected parents for newly created device """

        parents = []

        # for encrypted parents add space for luks metada
        if self._encryption_chooser.encrypt:
            reserved_size = crypto.LUKS_METADATA_SIZE
        else:
            reserved_size = size.Size(0)

        if self.selected_parent.type == "lvmvg":
            if self.selected_type == "lvmthinpool":
                free = self.selected_free.size * POOL_RESERVED
            else:
                free = self.selected_free.size

            parent = ProxyDataContainer(device=self.selected_parent,
                                        free_space=self.selected_free,
                                        min_size=self._get_parent_min_size(),
                                        max_size=self._get_parent_max_size(self.selected_parent, free),
                                        reserved_size=reserved_size)
            parents.append(parent)
        else:
            for row in self.parents_store:
                if row[3]:
                    parent = ProxyDataContainer(device=row[0],
                                                free_space=row[1],
                                                min_size=self._get_parent_min_size(),
                                                max_size=self._get_parent_max_size(row[0], row[1].size),
                                                reserved_size=reserved_size)
                    parents.append(parent)

        if not parents:  # FIXME
            parent = ProxyDataContainer(device=self.selected_parent,
                                        free_space=self.selected_free,
                                        min_size=self._get_parent_min_size(),
                                        max_size=self._get_parent_max_size(self.selected_parent, self.selected_free.size),
                                        reserved_size=reserved_size)
            parents.append(parent)

        return parents

    def _get_min_size_limit(self):
        limit = size.Size(0)

        if self.selected_fs:
            limit = self.selected_fs._min_size

        parent_limit = self._get_parent_min_size()
        limit = max(limit, parent_limit)

        return limit or size.Size("1 MiB")

    def _get_max_size_limit(self):
        limit = size.Size("16 EiB")

        if self.selected_fs:
            # some filesystems have 0 max size, so use 'our' upper limit for them
            limit = min(self.selected_fs._max_size, limit) or limit

        # XXX: free space for LVs is calculated based on free space on the PVs
        # but newly allocated LVs doesn't decrease this space, so we need some
        # way how to limit maximum size of the new LV
        if self.selected_type == "lvmlv":
            limit = min(self.selected_parent.free_space, limit)
        # same applies to thinpools, but we need to use another hack to limit
        # it's max size and leave some free space in the VG
        elif self.selected_type == "lvmthinpool":
            limit = min(self.selected_parent.free_space * POOL_RESERVED, limit)

        # limit from the parents maximum size
        parents_limit = sum(p.max_size for p in self._get_parents())
        limit = min(parents_limit, limit)

        return limit

    def add_size_area(self):
        device_type = self.selected_type

        # destroy existing size area
        if self.size_area is not None:
            self.size_area.destroy()

        if device_type in ("btrfs volume", "lvmlv", "mdraid"):
            raid_level = self._raid_chooser.selected_level
        else:
            raid_level = None

        min_size_limit = self._get_min_size_limit()
        max_size_limit = self._get_max_size_limit()
        parents = self._get_parents()

        size_area = SizeArea(device_type=device_type,
                             parents=parents,
                             min_limit=min_size_limit,
                             max_limit=max_size_limit,
                             raid_type=raid_level)

        self.grid.attach(size_area.frame, 0, 6, 6, 1)

        self.widgets_dict["size"] = [size_area]
        self.size_area = size_area

    def add_md_type_chooser(self):
        label_md_type = Gtk.Label(label=_("MDArray type:"), xalign=1)
        self.grid.attach(label_md_type, 0, 7, 1, 1)

        md_type_store = Gtk.ListStore(str, str)

        for md_type in ((_("Partition"), "partition"),):
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
        self.grid.attach(label_fs, 0, 8, 1, 1)

        filesystems_store = Gtk.ListStore(object, str, str)
        filesystems_combo = Gtk.ComboBox.new_with_model(filesystems_store)
        filesystems_combo.set_id_column(1)
        filesystems_combo.set_entry_text_column(2)

        self.grid.attach(filesystems_combo, 1, 8, 2, 1)

        renderer_text = Gtk.CellRendererText()
        filesystems_combo.pack_start(renderer_text, True)
        filesystems_combo.add_attribute(renderer_text, "text", 2)

        filesystems_combo.connect("changed", self.on_filesystems_combo_changed)
        self.widgets_dict["fs"] = [label_fs, filesystems_combo]

        return filesystems_store, filesystems_combo

    def _allow_format_size(self, fs):
        # FIXME: also check raid level -- resulting "free space" might be lower because of redundancy
        if self.selected_free.size < fs._min_size:
            return False
        if self.size_area and fs._max_size and self.size_area.min_size > fs._max_size:
            return False
        return True

    def update_fs_chooser(self):
        self.filesystems_store.clear()

        for fs in self.supported_filesystems:
            if self._allow_format_size(fs):
                self.filesystems_store.append((fs, fs.type, fs.name))
        self.filesystems_store.append((None, "unformatted", _("unformatted")))

        # XXX: what if there is no supported fs?
        if config.default_fstype in (fs.type for fs in self.supported_filesystems):
            self.filesystems_combo.set_active_id(config.default_fstype)
        else:
            self.filesystems_combo.set_active(0)

    def on_filesystems_combo_changed(self, _combo):

        if self.selected_fs is None:
            self.hide_widgets(["label", "mountpoint"])
        else:
            if not self.selected_fs.mountable:
                self.hide_widgets(["mountpoint"])
            else:
                self.show_widgets(["mountpoint"])

            if not self.selected_fs.labeling():
                self.hide_widgets(["label"])
            else:
                self.show_widgets(["label"])

        # update size
        min_size_limit = self._get_min_size_limit()
        max_size_limit = self._get_max_size_limit()

        self.size_area.set_size_limits(min_size_limit, max_size_limit)

    def add_name_chooser(self):
        label_label = Gtk.Label(label=_("Label:"), xalign=1)
        self.grid.attach(label_label, 0, 9, 1, 1)

        label_entry = Gtk.Entry()
        self.grid.attach(label_entry, 1, 9, 2, 1)

        self.widgets_dict["label"] = [label_label, label_entry]

        name_label = Gtk.Label(label=_("Name:"), xalign=1)
        self.grid.attach(name_label, 0, 10, 1, 1)

        name_entry = Gtk.Entry()
        self.grid.attach(name_entry, 1, 10, 2, 1)

        self.widgets_dict["name"] = [name_label, name_entry]

        return label_entry, name_entry

    def add_mountpoint(self):
        mountpoint_label = Gtk.Label(label=_("Mountpoint:"), xalign=1)
        self.grid.attach(mountpoint_label, 0, 11, 1, 1)

        mountpoint_entry = Gtk.Entry()
        self.grid.attach(mountpoint_entry, 1, 11, 2, 1)

        self.widgets_dict["mountpoint"] = [mountpoint_label, mountpoint_entry]

        return mountpoint_entry

    def add_advanced_options(self):

        device_type = self.selected_type

        if self.advanced:
            self.advanced.destroy()

        if device_type in ("lvm", "lvmvg", "partition", "mdraid"):
            level = self._raid_chooser.selected_level
            if device_type == "mdraid" and level and level.name == "raid1":
                self.advanced = None
                self.widgets_dict["advanced"] = []
            else:
                self.advanced = AdvancedOptions(self, device_type, self.selected_parent,
                                                self.selected_free)
                self.widgets_dict["advanced"] = [self.advanced]

                self.grid.attach(self.advanced.expander, 0, 15, 6, 1)

        else:
            self.advanced = None
            self.widgets_dict["advanced"] = []

    def show_widgets(self, widget_types):

        for widget_type in widget_types:
            if widget_type == "mountpoint" and not self.installer_mode:
                continue

            elif widget_type == "size":
                for widget in self.widgets_dict[widget_type]:
                    widget.set_sensitive(True)

            else:
                for widget in self.widgets_dict[widget_type]:
                    widget.show()

    def hide_widgets(self, widget_types):

        for widget_type in widget_types:
            if widget_type == "mountpoint" and not self.installer_mode:
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
        if self._encryption_chooser.encrypt:
            self.update_size_area_limits(min_size=self._get_min_size_limit(),
                                         reserved_size=crypto.LUKS_METADATA_SIZE)
        else:
            self.update_size_area_limits(min_size=self._get_min_size_limit(),
                                         reserved_size=size.Size(0))

    def on_devices_combo_changed(self, _event):

        device_type = self.selected_type

        self.update_parent_list()
        self.update_raid_type_chooser()
        self.update_fs_chooser()
        self.add_advanced_options()
        self.add_size_area()

        if device_type == "partition":
            self.show_widgets(["label", "fs", "encrypt", "mountpoint", "size", "advanced"])
            self.hide_widgets(["name", "mdraid"])

        elif device_type == "lvm":
            self.show_widgets(["encrypt", "name", "size", "advanced"])
            self.hide_widgets(["label", "fs", "mountpoint", "mdraid"])

        elif device_type == "lvmvg":
            self.show_widgets(["name", "advanced"])
            self.hide_widgets(["label", "fs", "mountpoint", "encrypt", "size", "mdraid"])

        elif device_type in ("lvmlv",):
            self.show_widgets(["name", "fs", "mountpoint", "size", "advanced", "label", "encrypt"])
            self.hide_widgets(["mdraid"])

        elif device_type in ("lvmthinlv",):
            self.show_widgets(["name", "fs", "mountpoint", "size", "label"])
            self.hide_widgets(["encrypt", "advanced", "mdraid"])

        elif device_type == "btrfs volume":
            self.show_widgets(["encrypt", "name", "size", "mountpoint"])
            self.hide_widgets(["label", "fs", "advanced", "mdraid"])

        elif device_type == "btrfs subvolume":
            self.show_widgets(["name", "mountpoint"])
            self.hide_widgets(["label", "fs", "encrypt", "size", "advanced", "mdraid"])

        elif device_type == "mdraid":
            self.show_widgets(["name", "size", "mountpoint", "fs", "advanced", "label", "encrypt"])
            self.hide_widgets(["mdraid"])

        elif device_type == "lvm snapshot":
            self.show_widgets(["name", "size"])
            self.hide_widgets(["label", "fs", "encrypt", "advanced", "mdraid", "mountpoint"])

        elif device_type == "lvm thinsnapshot":
            self.show_widgets(["name"])
            self.hide_widgets(["label", "fs", "encrypt", "advanced", "mdraid", "mountpoint", "size"])

        elif device_type == "lvmthinpool":
            self.show_widgets(["name", "size"])
            self.hide_widgets(["label", "fs", "encrypt", "advanced", "mdraid", "mountpoint"])

        # hide "advanced" encryption widgets if encrypt not checked
        self._encryption_chooser.set_advanced_visible(self._encryption_chooser.encrypt)

    @property
    def selected_fs(self):
        tree_iter = self.filesystems_combo.get_active_iter()

        if tree_iter:
            model = self.filesystems_combo.get_model()
            fs_obj = model[tree_iter][0]
            return fs_obj

    @property
    def selected_type(self):
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

        if user_input.mountpoint and not os.path.isabs(user_input.mountpoint):
            msg = _("\"{0}\" is not a valid mountpoint.").format(user_input.mountpoint)
            message_dialogs.ErrorDialog(self, msg,
                                        not self.installer_mode)  # do not show decoration in installer mode

            return False

        if user_input.device_type == "mdraid" and len(user_input.size_selection.parents) == 1:
            msg = _("Please select at least two parent devices.")
            message_dialogs.ErrorDialog(self, msg,
                                        not self.installer_mode)  # do not show decoration in installer mode

            return False

        if self.installer_mode and user_input.mountpoint:
            valid, msg = is_mountpoint_valid(self.mountpoints, user_input.mountpoint)
            if not valid:
                message_dialogs.ErrorDialog(self, msg,
                                            not self.installer_mode)  # do not show decoration in installer mode
                return False

        if user_input.name and not is_name_valid(user_input.device_type, user_input.name):
            msg = _("\"{0}\" is not a valid name.").format(user_input.name)
            message_dialogs.ErrorDialog(self, msg,
                                        not self.installer_mode)  # do not show decoration in installer mode
            return False

        if user_input.label and not is_label_valid(user_input.filesystem, user_input.label):
            msg = _("\"{0}\" is not a valid label.").format(user_input.label)
            message_dialogs.ErrorDialog(self, msg,
                                        not self.installer_mode)  # do not show decoration in installer mode
            return False

        valid, msg = self._encryption_chooser.validate_user_input()
        if not valid:
            message_dialogs.ErrorDialog(self, msg,
                                        not self.installer_mode)  # do not show decoration in installer mode
            return False

        return True

    def on_ok_clicked(self, _event):

        # validate advanced selection first
        if self.advanced and not self.advanced.validate_user_input():
            self.run()
            return

        if not self.validate_user_input():
            self.run()

    def get_selection(self):
        device_type = self.selected_type

        size_selection = self.size_area.get_selection()
        encryption_selection = self._encryption_chooser.get_selection()

        if device_type in ("btrfs volume", "mdraid", "lvmlv"):
            raid_level = self._raid_chooser.selected_level
            if raid_level:
                raid_level = raid_level.name
        else:
            raid_level = None

        if self.installer_mode:
            mountpoint = self.mountpoint_entry.get_text()
        else:
            mountpoint = None

        if self.advanced:
            advanced = self.advanced.get_selection()
        else:
            advanced = None

        if device_type in ("mdraid", "partition", "lvmlv", "lvmthinlv"):
            if self.selected_fs is not None:
                filesystem = self.selected_fs.type
            else:
                filesystem = None
        else:
            filesystem = None

        return ProxyDataContainer(device_type=device_type,
                                  size_selection=size_selection,
                                  filesystem=filesystem,
                                  name=self.name_entry.get_text(),
                                  label=self.label_entry.get_text(),
                                  mountpoint=mountpoint,
                                  encrypt=encryption_selection.encrypt,
                                  passphrase=encryption_selection.passphrase,
                                  encryption_type=encryption_selection.encryption_type,
                                  encryption_sector_size=encryption_selection.encryption_sector_size,
                                  raid_level=raid_level,
                                  advanced=advanced)
