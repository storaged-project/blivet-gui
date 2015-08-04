# -*- coding: utf-8 -*-
# logical_view.py
# 'Physical' visualization for devices
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

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk

from .rectangle import Rectangle

#------------------------------------------------------------------------------#

class PhysicalView(object):
    def __init__(self, blivet_gui):
        self.blivet_gui = blivet_gui

        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        self.rectangles = []
        self.boxes = []

        self._devices_list = None

    def visualize_parents(self, devices_list):
        self._devices_list = devices_list
        self._clear()

        root_iter = devices_list.get_iter_first()
        self._visualization_loop(root_iter)

        self.vbox.show_all()

    def _visualization_loop(self, treeiter, box=None):
        while treeiter:
            depth = self._devices_list.iter_depth(treeiter)
            # lower level of the tree -> visualization of childs
            if depth:
                (device, is_valid) = self._devices_list[treeiter]

                if is_valid:
                    rect = self._new_rectangle(device, "child-valid-" + self._get_child_position(treeiter))
                else:
                    rect = self._new_rectangle(device, "child-invalid-" + self._get_child_position(treeiter))
                box.pack_start(child=rect, expand=True, fill=True, padding=0)

            else:
                parent_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                self.boxes.append(parent_box)
                self.vbox.pack_start(child=parent_box, expand=False, fill=False, padding=0)
                rect = self._new_rectangle(self._devices_list[treeiter][0], "root-device")
                parent_box.pack_start(child=rect, expand=False, fill=False, padding=0)

                # every "root" device has children; if not, something is very wrong
                if not self._devices_list.iter_has_child(treeiter):
                    raise RuntimeError

                child_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
                parent_box.pack_start(child=child_box, expand=True, fill=True, padding=0)
                self.boxes.append(child_box)

                child_iter = self._devices_list.iter_children(treeiter)
                self._visualization_loop(child_iter, child_box)

            treeiter = self._devices_list.iter_next(treeiter)

    def _clear(self):
        for rect in self.rectangles:
            rect.hide()
            rect.destroy()
        self.rectangles = []

        for box in self.boxes:
            box.hide()
            box.destroy()
        self.boxes = []

    def _new_rectangle(self, device, rtype="", width=90, height=90):
        label = not rtype.startswith("child-invalid-")
        rect = Rectangle(rtype, None, width, height, device, label)
        self.rectangles.append(rect)

        return rect

    def _get_child_position(self, child_iter):
        parent_iter = self._devices_list.iter_parent(child_iter)
        num_childs = self._devices_list.iter_n_children(parent_iter)

        if self._devices_list[child_iter][0] == self._devices_list[self._devices_list.iter_nth_child(parent_iter, 0)][0]:
            return "first"
        elif self._devices_list[child_iter][0] == self._devices_list[self._devices_list.iter_nth_child(parent_iter, num_childs - 1)][0]:
            return "last"
        else:
            return "inner"
