# -*- coding: utf-8 -*-
# logical_view.py
# 'Logical' visualization for devices
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

class LogicalView(object):

    def __init__(self, blivet_gui):
        self.blivet_gui = blivet_gui

        self.hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.rectangles = []
        self.boxes = []

        self._ignore_toggle = False

    def visualize_devices(self, devices_list):
        self._clear()
        root_iter = devices_list.get_iter_first()
        self._visualization_loop(devices_list, root_iter, self.hbox)

        self.select_rectanlge(devices_list[root_iter][0])
        self.hbox.show_all()

    def _clear(self):
        for rect in self.rectangles:
            rect.hide()
            rect.destroy()
        self.rectangles = []

        for box in self.boxes:
            box.hide()
            box.destroy()
        self.boxes = []

    def _visualization_loop(self, devices_list, treeiter, box):
        while treeiter:
            depth = devices_list.iter_depth(treeiter)
            button_group = self.rectangles[0] if self.rectangles else None
            if depth:
                # num_childs = self.devices_list.iter_n_children(self.devices_list.iter_parent(treeiter))
                rect = Rectangle(group=button_group, width=-1, height=-1, device=devices_list[treeiter][0])
                rect.connect("toggled", self._on_rectangle_toggle)
                self.rectangles.append(rect)
                box.pack_start(child=rect, expand=True, fill=True, padding=0)
            else:
                rect = Rectangle(group=button_group, width=-1, height=-1, device=devices_list[treeiter][0])
                rect.connect("toggled", self._on_rectangle_toggle)
                self.rectangles.append(rect)

                if devices_list.iter_has_child(treeiter):
                    # device with children, add a vbox
                    vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=True)
                    self.boxes.append(vbox)
                    box.pack_start(child=vbox, expand=True, fill=True, padding=0)
                    vbox.pack_start(child=rect, expand=True, fill=True, padding=0)
                    # hbox for children
                    child_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                    self.boxes.append(child_box)
                    vbox.pack_start(child=child_box, expand=True, fill=True, padding=0)
                    childiter = devices_list.iter_children(treeiter)
                    self._visualization_loop(devices_list, childiter, child_box)
                else:
                    box.pack_start(child=rect, expand=True, fill=True, padding=0)

            treeiter = devices_list.iter_next(treeiter)

    def select_rectanlge(self, device):
        for rect in self.rectangles:
            if rect.device == device:
                rect.set_active(True)

    def _on_rectangle_toggle(self, button):
        if not self._ignore_toggle:
            self._ignore_toggle = True
            self.blivet_gui.list_partitions.select_device(button.device)
            self._ignore_toggle = False
