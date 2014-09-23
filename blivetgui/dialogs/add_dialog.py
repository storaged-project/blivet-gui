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

import os

import gettext

from gi.repository import Gtk

from blivet import Size

from math import floor

#------------------------------------------------------------------------------#

APP_NAME = "blivet-gui"

dirname, filename = os.path.split(os.path.abspath(__file__))

#t = gettext.translation('messages', dirname + '/i18n')
#_ = t.gettext

gettext.bindtextdomain('blivetgui', dirname + '/i18n')
gettext.textdomain('blivetgui')
_ = gettext.gettext

#------------------------------------------------------------------------------#

class UserSelection(object):
    def __init__(self, device_type, size, filesystem, name, label, mountpoint,
        encrypt, passphrase, parents):
        self.device_type = device_type
        self.size = size
        self.filesystem = filesystem
        self.name = name
        self.label = label
        self.mountpoint = mountpoint
        self.encrypt = encrypt
        self.passphrase = passphrase
        self.parents = parents

class AddDialog(Gtk.Dialog):
    """ Dialog window allowing user to add new partition including selecting
         size, fs, label etc.
    """

    #FIXME add mountpoint validation -- os.path.isabs(path)
    def __init__(self, parent_window, device_type, parent_device, free_device,
        free_space, free_pvs, free_disks, kickstart=False):
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
            :param kickstart: kickstart mode
            :type kickstart: bool

          """

        self.free_device = free_device
        self.free_space = free_space
        self.device_type = device_type
        self.parent_device = parent_device
        self.free_pvs = free_pvs
        self.free_disks = free_disks
        self.parent_window = parent_window
        self.kickstart = kickstart

        Gtk.Dialog.__init__(self, _("Create new device"), None, 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_transient_for(self.parent_window)

        self.set_border_width(10)
        self.set_default_size(600, 300)

        self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10,
            column_spacing=5)

        box = self.get_content_area()
        box.add(self.grid)

        self.add_device_chooser()
        self.add_size_scale(self.free_space)
        self.add_fs_chooser()
        self.add_name_chooser()
        self.add_encrypt_chooser()
        self.add_parent_list()

        if kickstart and self.device_type in ["disk", "lvmvg"]:
            self.add_mountpoint()

        self.show_all()

    def add_device_chooser(self):

        map_type_devices = {
            "disk" : [_("Partition"), _("LVM2 Storage"),
            _("LVM2 Physical Volume"), _("Btrfs Volume")],
            "lvmpv" : [_("LVM2 Volume Group")],
            "lvmvg" : [_("LVM2 Logical Volume")],
            "luks/dm-crypt" : [_("LVM2 Volume Group")],
            "btrfs volume" : [_("Btrfs Subvolume")]
            }

        self.label_devices = Gtk.Label()
        self.label_devices.set_text(_("Device type:"))
        self.grid.attach(self.label_devices, 0, 0, 1, 1)

        if self.device_type == "disk" and self.free_device.isLogical:
            devices = [_("Partition")]

        else:
            devices = map_type_devices[self.device_type]

        devices_store = Gtk.ListStore(str)

        for device in devices:
            devices_store.append([device])

        self.devices_combo = Gtk.ComboBox.new_with_model(devices_store)

        self.devices_combo.set_entry_text_column(0)
        self.devices_combo.set_active(0)

        if len(devices) == 1:
            self.devices_combo.set_sensitive(False)

        self.grid.attach(self.devices_combo, 1, 0, 2, 1)

        self.devices_combo.connect("changed", self.on_devices_combo_changed)
        renderer_text = Gtk.CellRendererText()
        self.devices_combo.pack_start(renderer_text, True)
        self.devices_combo.add_attribute(renderer_text, "text", 0)

    def add_parent_list(self):

        self.parents_store = Gtk.ListStore(object, bool, str, str, str)

        self.parents = Gtk.TreeView(model=self.parents_store)

        renderer_toggle = Gtk.CellRendererToggle()
        renderer_toggle.connect("toggled", self.on_cell_toggled)

        renderer_text = Gtk.CellRendererText()

        column_toggle = Gtk.TreeViewColumn(None, renderer_toggle, active=1)
        column_name = Gtk.TreeViewColumn(_("Device"), renderer_text, text=2)
        column_type = Gtk.TreeViewColumn(_("Type"), renderer_text, text=3)
        column_size = Gtk.TreeViewColumn(_("Size"), renderer_text, text=4)

        self.parents.append_column(column_toggle)
        self.parents.append_column(column_name)
        self.parents.append_column(column_type)
        self.parents.append_column(column_size)

        self.parents.set_headers_visible(True)

        self.label_list = Gtk.Label()
        self.label_list.set_text(_("Available devices:"))

        self.grid.attach(self.label_list, 0, 1, 1, 1)
        self.grid.attach(self.parents, 1, 1, 4, 4)

        self.update_parent_list()

    def update_parent_list(self):

        self.parents_store.clear()

        tree_iter = self.devices_combo.get_active_iter()

        if tree_iter != None:
            model = self.devices_combo.get_model()
            device = model[tree_iter][0]

            if device == "LVM2 Volume Group":

                for pv in self.free_pvs:
                    if pv.name == self.parent_device.name:
                        self.parents_store.append([self.parent_device, True,
                            self.parent_device.name, self.device_type,
                            str(self.free_space)])
                    else:
                        self.parents_store.append([pv, False, pv.name, "lvmpv",
                            str(pv.size)])

                self.parents.set_sensitive(True)

            elif device == "Btrfs Volume":

                # add selected device
                self.parents_store.append([self.parent_device, True,
                    self.parent_device.name, self.device_type,
                    str(self.free_space)])

                self.parents.set_sensitive(True)

                for disk, free in self.free_disks:

                    # skip selected device -- already added
                    if disk.name == self.parent_device.name:
                        pass

                    else:
                        self.parents_store.append([disk, False, disk.name,
                            "disk", str(free)])

            else:
                self.parents_store.append([self.parent_device, True,
                    self.parent_device.name, self.device_type,
                    str(self.free_space)])

                self.parents.set_sensitive(False)

    def on_cell_toggled(self, event, path):

        if self.parents_store[path][2] == self.parent_device.name:
            pass

        else:
            self.parents_store[path][1] = not self.parents_store[path][1]

            self.remove_size_scale() # remove scale -- it has wrong size

            tree_iter = self.devices_combo.get_active_iter()

            if tree_iter != None:
                model = self.devices_combo.get_model()
                device = model[tree_iter][0]

            # re-add deleted size scale and show it
            self.add_size_scale(self.compute_size_scale(device))
            self.show_size_scale()

    def compute_size_scale(self, device_type):
        """ Computes size (upper limit) for our Gtk.Scale and Gtk.SpinButtons
            --> if user chooses more than one parent device, we need to allow
                him to choose size for new device to be size of both devices
                (or twice size of smaller smaller device for raids)

                #FIXME: size based on raid type, btrfs see: https://btrfs.wiki.kernel.org/index.php/Using_Btrfs_with_Multiple_Devices

            :param device_type: type of created device (raid, lvmvg, btrfs)
            :type device_type: str
            :returns: size upper limit for newly created device
            :rtype: blivet.Size

        """

        size = Size("0 MiB")
        num_selected = 0

        for row in self.parents_store:
            if row[1] == True:

                num_selected += 1

                if device_type == "LVM2 Volume Group":
                    size += Size(row[4])

                elif device_type == "Btrfs Volume":
                    if size == 0:
                        size = Size(row[4])

                    elif Size(row[4]) < size:
                        size = Size(row[4])

        if device_type == "LVM2 Volume Group":
            return size

        elif device_type == "Btrfs Volume":
            return size*num_selected

    def add_size_scale(self, up_limit):

        # see edit dialog for explanation # FIXME (up_limit)
        self.up_limit = int(floor(up_limit.convertTo("KiB")/1024))

        self.scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL,
            adjustment=Gtk.Adjustment(0, 1, self.up_limit, 1, 10, 0))

        self.scale.set_hexpand(True)
        self.scale.set_valign(Gtk.Align.START)
        self.scale.set_digits(0)
        self.scale.set_value(self.up_limit)
        self.scale.add_mark(0, Gtk.PositionType.BOTTOM, str(1))
        self.scale.add_mark(self.up_limit, Gtk.PositionType.BOTTOM,
            str(self.up_limit))

        self.scale.connect("value-changed", self.scale_moved)

        self.grid.attach(self.scale, 0, 6, 6, 1) #left-top-width-height

        self.label_size = Gtk.Label()
        self.label_size.set_text(_("Volume size:"))
        self.grid.attach(self.label_size, 0, 7, 1, 1) #left-top-width-height

        self.spin_size = Gtk.SpinButton(adjustment=Gtk.Adjustment(0, 1,
            self.up_limit, 1, 10, 0))

        self.spin_size.set_numeric(True)
        self.spin_size.set_value(self.up_limit)
        self.spin_size.connect("value-changed", self.spin_size_moved)

        self.grid.attach(self.spin_size, 1, 7, 1, 1) #left-top-width-height

        self.label_mb = Gtk.Label()
        self.label_mb.set_text(_("MiB"))
        self.grid.attach(self.label_mb, 2, 7, 1, 1) #left-top-width-height

        self.label_free = Gtk.Label()
        self.label_free.set_text(_("Free space after:"))
        self.grid.attach(self.label_free, 3, 7, 1, 1) #left-top-width-height

        self.spin_free = Gtk.SpinButton(adjustment=Gtk.Adjustment(0, 0,
            self.up_limit, 1, 10, 0))

        self.spin_free.set_numeric(True)
        self.spin_free.connect("value-changed", self.spin_free_moved)

        self.grid.attach(self.spin_free, 4, 7, 1, 1) #left-top-width-height

        self.label_mb2 = Gtk.Label()
        self.label_mb2.set_text(_("MiB"))
        self.grid.attach(self.label_mb2, 5, 7, 1, 1) #left-top-width-height

        if self._get_selected_device_type in ["LVM2 Volume Group",
            "Btrfs Subvolume"]:

            self.label_size.set_sensitive(False)
            self.label_free.set_sensitive(False)
            self.scale.set_sensitive(False)
            self.spin_size.set_sensitive(False)
            self.spin_free.set_sensitive(False)

        else:
            self.label_size.set_sensitive(True)
            self.label_free.set_sensitive(True)
            self.scale.set_sensitive(True)
            self.spin_size.set_sensitive(True)
            self.spin_free.set_sensitive(True)

    def remove_size_scale(self):
        self.scale.destroy()
        self.label_size.destroy()
        self.spin_size.destroy()
        self.label_mb.destroy()
        self.label_free.destroy()
        self.spin_free.destroy()
        self.label_mb2.destroy()

    def show_size_scale(self):
        self.scale.show()
        self.label_size.show()
        self.spin_size.show()
        self.label_mb.show()
        self.label_free.show()
        self.spin_free.show()
        self.label_mb2.show()

    def add_fs_chooser(self):
        self.label_fs = Gtk.Label()
        self.label_fs.set_text(_("Filesystem:"))
        self.grid.attach(self.label_fs, 0, 8, 1, 1)

        filesystems = ["ext2", "ext3", "ext4", "xfs", "reiserfs", "swap",
            "vfat"]

        self.filesystems_combo = Gtk.ComboBoxText()
        self.filesystems_combo.set_entry_text_column(0)

        for fs in filesystems:
            self.filesystems_combo.append_text(fs)

        self.grid.attach(self.filesystems_combo, 1, 8, 2, 1)

        if self._get_selected_device_type in ["Partition", "LVM2 Logical Volume"]:
            self.filesystems_combo.set_sensitive(True)
            self.label_fs.set_sensitive(True)

        else:
            self.filesystems_combo.set_sensitive(False)
            self.label_fs.set_sensitive(False)

    def add_name_chooser(self):
        self.label_label = Gtk.Label()
        self.label_label.set_text(_("Label:"))
        self.grid.attach(self.label_label, 0, 9, 1, 1)

        self.label_entry = Gtk.Entry()
        self.grid.attach(self.label_entry, 1, 9, 2, 1)

        if self.device_type not in ["lvmvg", "disk"]:
            self.label_label.set_sensitive(False)
            self.label_entry.set_sensitive(False)

        self.name_label = Gtk.Label()
        self.name_label.set_text(_("Name:"))
        self.grid.attach(self.name_label, 3, 9, 1, 1)

        self.name_entry = Gtk.Entry()
        self.grid.attach(self.name_entry, 4, 9, 2, 1)

        if self._get_selected_device_type in ["Partition", "LVM2 Physical Volume"]:
            self.name_label.set_sensitive(False)
            self.name_entry.set_sensitive(False)

        else:
            self.name_label.set_sensitive(True)
            self.label_entry.set_sensitive(True)

        if self._get_selected_device_type not in ["Partition"]:
            self.label_label.set_sensitive(False)
            self.label_entry.set_sensitive(False)

        else:
            self.label_label.set_sensitive(True)
            self.name_entry.set_sensitive(True)

    def add_encrypt_chooser(self):
        self.encrypt_label = Gtk.Label()
        self.encrypt_label.set_text(_("Encrypt:"))
        self.grid.attach(self.encrypt_label, 0, 10, 1, 1)

        self.encrypt_check = Gtk.CheckButton()
        self.grid.attach(self.encrypt_check, 1, 10, 1, 1)
        self.encrypt_check.connect("toggled", self.on_encrypt_changed)

        if self.parent_device.type != "disk" or self.free_device.isLogical:
            self.encrypt_label.set_sensitive(False)
            self.encrypt_check.set_sensitive(False)

        else:
            self.encrypt_label.set_sensitive(True)
            self.encrypt_check.set_sensitive(True)

        self.passphrase_label = Gtk.Label()
        self.passphrase_label.set_text(_("Passphrase:"))
        self.grid.attach(self.passphrase_label, 3, 10, 1, 1)
        self.passphrase_label.set_sensitive(False)

        self.passphrase_entry = Gtk.Entry()
        self.passphrase_entry.set_visibility(False)
        self.passphrase_entry.set_property("caps-lock-warning", True)
        self.grid.attach(self.passphrase_entry, 4, 10, 2, 1)
        self.passphrase_entry.set_sensitive(False)

    def add_mountpoint(self):
        self.mountpoint_label = Gtk.Label()
        self.mountpoint_label.set_text(_("Mountpoint:"))
        self.grid.attach(self.mountpoint_label, 0, 11, 1, 1)

        self.mountpoint_entry = Gtk.Entry()
        self.grid.attach(self.mountpoint_entry, 1, 11, 2, 1)

        if self.device_type in ["Partition"]:
            self.label_label.set_sensitive(False)
            self.label_entry.set_sensitive(False)

    def on_encrypt_changed(self, event):
        self.passphrase_entry.set_sensitive(not self.passphrase_entry.get_sensitive())
        self.passphrase_label.set_sensitive(not self.passphrase_label.get_sensitive())

    def on_devices_combo_changed(self, event):
        device_type = self._get_selected_device_type

        if device_type == _("Partition"):
            self.label_label.set_sensitive(True)
            self.label_entry.set_sensitive(True)

            self.name_label.set_sensitive(False)
            self.name_entry.set_sensitive(False)

            self.filesystems_combo.set_sensitive(True)
            self.label_fs.set_sensitive(True)

            self.encrypt_label.set_sensitive(True)
            self.encrypt_check.set_sensitive(True)

            if self.kickstart:
                self.mountpoint_label.set_sensitive(True)
                self.mountpoint_entry.set_sensitive(True)

        elif device_type == _("LVM2 Physical Volume"):
            self.label_label.set_sensitive(False)
            self.label_entry.set_sensitive(False)

            self.name_label.set_sensitive(False)
            self.name_entry.set_sensitive(False)

            self.filesystems_combo.set_sensitive(False)
            self.label_fs.set_sensitive(False)

            self.encrypt_label.set_sensitive(True)
            self.encrypt_check.set_sensitive(True)

            if self.kickstart:
                self.mountpoint_label.set_sensitive(False)
                self.mountpoint_entry.set_sensitive(False)

        elif device_type == _("LVM2 Storage"):
            self.label_label.set_sensitive(False)
            self.label_entry.set_sensitive(False)

            self.name_label.set_sensitive(True)
            self.name_entry.set_sensitive(True)

            self.filesystems_combo.set_sensitive(False)
            self.label_fs.set_sensitive(False)

            self.encrypt_label.set_sensitive(True)
            self.encrypt_check.set_sensitive(True)

            if self.kickstart:
                self.mountpoint_label.set_sensitive(False)
                self.mountpoint_entry.set_sensitive(False)

        elif device_type == _("Btrfs Volume"):
            self.label_label.set_sensitive(False)
            self.label_entry.set_sensitive(False)

            self.name_label.set_sensitive(True)
            self.name_entry.set_sensitive(True)

            self.filesystems_combo.set_sensitive(False)
            self.label_fs.set_sensitive(False)

            self.encrypt_label.set_sensitive(False)
            self.encrypt_check.set_sensitive(False)

            if self.kickstart:
                self.mountpoint_label.set_sensitive(False) #FIXME!
                self.mountpoint_entry.set_sensitive(False)

        self.update_parent_list()

    def scale_moved(self, event):
        self.spin_size.set_value(self.scale.get_value())
        self.spin_free.set_value(self.up_limit - self.scale.get_value())

    def spin_size_moved(self, event):
        self.scale.set_value(self.spin_size.get_value())
        self.spin_free.set_value(self.up_limit - self.scale.get_value())

    def spin_free_moved(self, event):
        self.scale.set_value(self.up_limit - self.spin_free.get_value())
        self.spin_size.set_value(self.up_limit - self.spin_free.get_value())

    @property
    def _get_selected_device_type(self):
        tree_iter = self.devices_combo.get_active_iter()

        if tree_iter != None:
            model = self.devices_combo.get_model()
            device_type = model[tree_iter][0]

            return device_type

        else:
            return None

    def get_selection(self):

        device_type = self._get_selected_device_type

        parents = []

        for row in self.parents_store:
            if row[1]:
                parents.append(row[0])

        if self.kickstart:
            mountpoint = self.mountpoint_entry.get_text()

        else:
            mountpoint = None

        return UserSelection(device_type=device_type,
            size=Size(str(self.spin_size.get_value()) + "MiB"),
            filesystem=self.filesystems_combo.get_active_text(),
            name=self.name_entry.get_text(),
            label=self.label_entry.get_text(),
            mountpoint=mountpoint,
            encrypt=self.encrypt_check.get_active(),
            passphrase=self.passphrase_entry.get_text(),
            parents=parents)

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

        self.set_default_size(550, 200)
        self.set_border_width(10)

        self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10,
            column_spacing=5)

        box = self.get_content_area()
        box.add(self.grid)

        self.add_labels()
        self.add_pt_chooser()

        self.show_all()

    def add_labels(self):

        self.info_label = Gtk.Label()
        self.info_label.set_markup(_("A partition table is required before " \
            "partitions can be added.\n\n<b>Warning: This will delete all " \
            "data on {0}!</b>").format(self.disk_name))

        self.grid.attach(self.info_label, 0, 0, 4, 1) #left-top-width-height

    def add_pt_chooser(self):

        self.pts_store = Gtk.ListStore(str)

        for label in self.disklabels:
            self.pts_store.append([label])

        self.pts_combo = Gtk.ComboBox.new_with_model(self.pts_store)

        self.pts_combo.set_entry_text_column(0)
        self.pts_combo.set_active(0)

        if len(self.disklabels) > 1:
            self.pts_combo.set_sensitive(True)

        else:
            self.pts_combo.set_sensitive(False)

        self.label_list = Gtk.Label()
        self.label_list.set_text(_("Select new partition table type:"))

        self.grid.attach(self.label_list, 0, 1, 3, 1)
        self.grid.attach(self.pts_combo, 3, 1, 1, 1)

        self.pts_combo.connect("changed", self.on_devices_combo_changed)
        renderer_text = Gtk.CellRendererText()
        self.pts_combo.pack_start(renderer_text, True)
        self.pts_combo.add_attribute(renderer_text, "text", 0)


    def on_devices_combo_changed(self, event):

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
