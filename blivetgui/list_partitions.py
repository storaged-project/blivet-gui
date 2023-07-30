# -*- coding: utf-8 -*-
# list_partitions.py
# Load and display partitions for selected device
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


class ListPartitions(object):
    """ List of children of selected device
    """

    def __init__(self, blivet_gui):

        self.blivet_gui = blivet_gui

        self.installer_mode = self.blivet_gui.installer_mode

        self.partitions_list = self.blivet_gui.builder.get_object("liststore_logical")
        self.partitions_view = self.blivet_gui.builder.get_object("treeview_logical")

        self.partitions_view.connect("button-release-event", self.on_right_click_event)

        self.select = self.partitions_view.get_selection()
        self.select.connect("changed", self.on_partition_selection_changed)

        self.selected_partition = None

    def update_partitions_list(self, selected_device):
        """ Update partition view with selected disc children (partitions)

            :param selected_device: selected device from list (eg. disk or VG)
            :type device_name: blivet.Device

        """

        self.partitions_list.clear()

        def _get_real_child(child):
            """ When adding a child device, we actually might want to add one
                of its children instead -- e.g. when adding a partition that
                is a PV we want to add the VG ("group device") etc.
            """
            if self._is_group_device(child):
                return self.blivet_gui.client.remote_call("get_group_device", child)
            elif child.format and child.format.type in ("luks", "integrity") and child.children:
                return self.blivet_gui.client.remote_call("get_luks_device", child)
            else:
                return child

        def _add_chilren(childs, parent_iter=None):
            for child in childs:
                if child.children:
                    child_iter = self._add_to_store(child, parent_iter)
                    _add_chilren(self.blivet_gui.client.remote_call("get_children", child), child_iter)

                else:
                    new_child = _get_real_child(child)
                    self._add_to_store(new_child, parent_iter)

        if selected_device.is_disk:
            childs = self.blivet_gui.client.remote_call("get_disk_children", selected_device)
            for child in childs.partitions:
                child = _get_real_child(child)
                child_iter = self._add_to_store(child)
                if hasattr(child, "is_extended") and child.is_extended:
                    for logical in childs.logicals:
                        logical = _get_real_child(logical)
                        self._add_to_store(logical, child_iter)

        # lvmvg always has some children, at least a free space
        elif selected_device.type == "lvmvg":
            childs = self.blivet_gui.client.remote_call("get_children", selected_device)
            _add_chilren(childs, None)

        # for btrfs volumes and mdarrays its necessary to add the device itself to the view
        # because these devices don't need to have children (only btrfs volume or only mdarray
        # is a valid, usable device)
        elif selected_device.type == "btrfs volume" or (selected_device.type == "mdarray" and not selected_device.children):
            parent_iter = self._add_to_store(selected_device)
            childs = self.blivet_gui.client.remote_call("get_children", selected_device)
            _add_chilren(childs, parent_iter)

        else:
            childs = self.blivet_gui.client.remote_call("get_children", selected_device)
            _add_chilren(childs, None)

        # select first line in partitions view
        self.select.select_path("0")
        # expand all expanders
        self.partitions_view.expand_all()

    def _is_group_device(self, blivet_device):
        # btrfs volume on raw disk
        if blivet_device.type in ("btrfs volume", "lvmvg"):
            return True

        if blivet_device.format and blivet_device.format.type in ("lvmpv", "btrfs", "mdmember"):
            return (len(blivet_device.children) > 0)

        # encrypted group device
        if blivet_device.format and blivet_device.format.type in ("luks", "integrity") and blivet_device.children:
            luks_device = self.blivet_gui.client.remote_call("get_luks_device", blivet_device)
            if luks_device.format and luks_device.format.type in ("lvmpv", "btrfs", "mdmember"):
                return (len(luks_device.children) > 0)

        return False

    def _add_to_store(self, device, parent_iter=None):
        """ Add new device to partitions list

            :param device: device to add
            :type device: blivet.device.Device
            :param parent_iter: parent iter for this device
            :type parent_iter: Gtk.TreeIter or None
        """

        devtype = "lvm" if device.type == "lvmvg" else "raid" if device.type == "mdarray" else device.type

        if device.format.type:
            fmt = device.format.type
        else:
            if device.format.name != "Unknown":
                # format recognized by blkid but not supported by blivet
                fmt = device.format.name
            else:
                fmt = None

        if self.installer_mode:
            mnt = device.format.mountpoint if (device.format and device.format.mountable) else None
        else:
            is_mounted = bool(device.format.system_mountpoint) if (device.format and device.format.mountable) else False
            if is_mounted:
                mnts = self.blivet_gui.client.remote_call("get_system_mountpoints", device)
                mnt = ", ".join(mnts)
            else:
                mnt = None

        if device.format.type and hasattr(device.format, "label") and device.format.label:
            label = device.format.label if len(device.format.label) < 18 else device.format.label[:15] + "..."
        else:
            label = ""

        device_iter = self.partitions_list.append(parent_iter, [device, device.name, devtype, fmt, str(device.size), label, mnt])

        return device_iter

    def _allow_recursive_delete_device(self, device):
        if device.type not in ("btrfs volume", "mdarray", "lvmvg"):
            return False

        def _device_descendants(device):
            descendants = []
            for child in device.children:
                descendants.append(child)
                descendants.extend(_device_descendants(child))

            return descendants

        for d in _device_descendants(device):
            if not self._allow_delete_device(d, recursive=True):
                return False

        return True

    def _allow_delete_device(self, device, recursive=False):
        if device.protected:
            return False

        if device.type in ("free space",):
            return False

        elif not recursive and not device.isleaf:
            return False

        else:
            if not device.format.type:
                return True

            elif device.format.type == "swap":
                return not device.format.status

            else:
                if not device.format.mountable:
                    return True

                else:
                    return not device.format.status

    def _allow_resize_device(self, device):
        if device.protected or device.children or device.format_immutable:
            return False

        if not device._resizable:
            return False

        return True

    def _allow_format_device(self, device):
        if device.protected or device.children:
            return False

        if device.type not in ("partition", "lvmlv", "luks/dm-crypt", "mdarray"):
            return False

        if device.type == "partition" and device.is_extended:
            return False

        if device.format.type in ("mdmember", "btrfs"):
            return False

        return not device.format.status

    def _allow_set_mountpoint(self, device):
        if not self.blivet_gui.installer_mode:
            return False

        if device.type in ("lvmthinsnapshot", "lvmsnapshot") and not device.exists:
            return False

        # do not allow to set mountpoints for devices that are not "direct"
        # (e.g. partition formatted to btrfs -- the mountpoint must be set for
        # the btrfs volume on top of it)
        if not device.direct:
            return False

        return device.format.mountable

    def _allow_set_partition_table(self, device):
        # there is no special "device" representing disks in the UI
        # so we are "editing" a free space
        if device.type != "free space":
            return False

        # empty disk without disklabel
        if device.is_uninitialized_disk:
            return True

        # empty disk with disklabel
        if device.is_empty_disk and device.disk.format.type == "disklabel":
            return True

        return False

    def _allow_relabel_device(self, device):
        if device.protected or device.format.status:
            return False

        return device.format.labeling() and device.format.relabels()

    def _allow_add_device(self, device):
        if device.protected:
            return False

        if device.type in ("free space", "btrfs volume", "btrfs subvolume", "lvmthinpool"):
            return True

        # empty lvmpv
        if device.format and device.format.type == "lvmpv":
            return not device.children

        # snapshot of thin lv -- only if exists
        if device.type == "lvmthinlv":
            return device.exists

        # snapshot of lvmlv -- only if there is free space in the vg and if exists
        if device.type == "lvmlv":
            return device.vg.free_space >= device.vg.pe_size and device.exists

        return False

    def activate_action_buttons(self, selected_device):
        """ Activate buttons in toolbar based on selected device

            :param selected_device: Selected partition
            :type selected_device: Gtk.TreeModelRow

        """

        device = selected_device[0]

        self.blivet_gui.deactivate_all_actions()

        if device.type != "free space":
            self.blivet_gui.activate_device_actions(["info"])

        if self._allow_delete_device(device) or self._allow_recursive_delete_device(device):
            self.blivet_gui.activate_device_actions(["delete"])

        if self._allow_resize_device(device):
            self.blivet_gui.activate_device_actions(["resize"])

        if self._allow_format_device(device):
            self.blivet_gui.activate_device_actions(["format"])

        if self._allow_relabel_device(device):
            self.blivet_gui.activate_device_actions(["label"])

        if self._allow_add_device(device):
            self.blivet_gui.activate_device_actions(["add"])

        if self._allow_set_mountpoint(device):
            self.blivet_gui.activate_device_actions(["mountpoint"])

        if self._allow_set_partition_table(device):
            self.blivet_gui.activate_device_actions(["partitiontable"])

        if device.type == "lvmvg":
            self.blivet_gui.activate_device_actions(["parents"])

        if device.format:
            if device.format.type == "luks" and not device.format.status and device.format.exists:
                self.blivet_gui.activate_device_actions(["decrypt"])

            elif device.format.mountable and device.format.system_mountpoint:
                self.blivet_gui.activate_device_actions(["unmount"])

    def select_device(self, device):
        """ Select device from list """

        def _search(model, path, treeiter, device):
            if model[treeiter][0] == device:
                self.select.select_path(path)

        self.partitions_list.foreach(_search, device)

    def on_partition_selection_changed(self, selection):
        """ On selected partition action
        """

        model, treeiter = selection.get_selected()

        if treeiter:
            self.blivet_gui.deactivate_all_actions()
            self.activate_action_buttons(model[treeiter])
            self.selected_partition = model[treeiter]
            self.blivet_gui.logical_view.select_rectanlge(device=self.selected_partition[0])

        else:
            self.blivet_gui.deactivate_all_actions()

    def on_right_click_event(self, treeview, event):
        """ Right click event on partition treeview
        """

        if event.button == 3:
            selection = treeview.get_selection()

            if selection:
                self.blivet_gui.popup_menu.menu.popup_at_pointer(None)
