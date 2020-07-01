# -*- coding: utf-8 -*-
# list_parents.py
# Load and display parents for selected device
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


class ListParents(object):
    """ List of parents of selected device
    """

    def __init__(self, blivet_gui):
        self.blivet_gui = blivet_gui
        self.parents_list = self.blivet_gui.builder.get_object("liststore_physical")

    def update_parents_list(self, selected_device):
        self.parents_list.clear()

        # no physical view for disks, empty list and return
        if selected_device.is_disk:
            return

        parent_devices = self._get_parent_devices(selected_device)
        root_devices = self.blivet_gui.client.remote_call("get_roots", selected_device)

        for root in root_devices:
            root_iter = self.parents_list.append(None, [root, False])
            if root.is_disk:
                childs = self.blivet_gui.client.remote_call("get_disk_children", root).partitions
            elif root.type == "mdarray":
                childs = [root]
            else:
                childs = self.blivet_gui.client.remote_call("get_children", root)

            for child in childs:
                if child.type == "btrfs volume" and root.is_disk and root.format.type == "btrfs":
                    self.parents_list.append(root_iter, [root, True])
                elif child.type == "partition" and child.is_extended:
                    for parent in parent_devices:
                        if parent.type == "partition" and parent.is_logical and parent.disk.name == child.disk.name:
                            self.parents_list.append(root_iter, [parent, True])
                elif child.name in [d.name for d in parent_devices]:
                    self.parents_list.append(root_iter, [child, True])
                else:
                    self.parents_list.append(root_iter, [child, False])

    def _get_parent_devices(self, device):
        parents = []
        if device.type == "lvmvg":
            for pv in device.pvs:
                if pv.type == "luks/dm-crypt":
                    parents.append(pv.raw_device)
                else:
                    parents.append(pv)
        elif device.type in ("btrfs volume", "mdarray"):
            return device.members

        return parents
