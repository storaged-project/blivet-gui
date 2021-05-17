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
# ---------------------------------------------------------------------------- #

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

from gi.repository import Gtk, Gdk

from .rectangle import Rectangle

# ---------------------------------------------------------------------------- #

RECT_MIN_SIZE = 100

# ---------------------------------------------------------------------------- #


class LogicalView(object):

    def __init__(self, blivet_gui):
        self.blivet_gui = blivet_gui

        self.hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        self.hbox.set_name("bg-visualization")
        self.rectangles = []
        self.boxes = []

        self._devices_list = None
        self._ignore_toggle = False

        self._view_width = 0
        self._allocated_width = 0

    def visualize_devices(self, devices_list):
        self._devices_list = devices_list

        self._view_width = self.hbox.get_parent().get_allocation().width
        rect_widths = self._compute_rect_widths()

        self._clear()
        root_iter = devices_list.get_iter_first()

        if not root_iter:
            return

        self._visualization_loop(rect_widths, root_iter, self.hbox)

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

    def _visualization_loop(self, rect_widths, treeiter, box):
        while treeiter:
            depth = self._devices_list.iter_depth(treeiter)
            rect_width = rect_widths[self._devices_list[treeiter][0]]
            if depth:
                child_type = "child-rect-" + self._get_child_position(treeiter)
                rect = self._new_rectangle(self._devices_list[treeiter][0], child_type, width=rect_width)
                box.pack_start(child=rect, expand=True, fill=True, padding=0)
            else:
                if self._devices_list.iter_has_child(treeiter):
                    # device with children, add a vbox
                    vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=True)
                    self.boxes.append(vbox)
                    box.pack_start(child=vbox, expand=True, fill=True, padding=0)

                    # rectangle for parent device
                    rect = self._new_rectangle(self._devices_list[treeiter][0], "parent-rect", width=rect_width)
                    vbox.pack_start(child=rect, expand=True, fill=True, padding=0)

                    # hbox for children
                    child_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                    self.boxes.append(child_box)
                    vbox.pack_start(child=child_box, expand=True, fill=True, padding=0)

                    # _virtualization_loop for children
                    childiter = self._devices_list.iter_children(treeiter)
                    self._visualization_loop(rect_widths, childiter, child_box)
                else:
                    rect = self._new_rectangle(self._devices_list[treeiter][0], width=rect_width)
                    box.pack_start(child=rect, expand=True, fill=True, padding=0)

            treeiter = self._devices_list.iter_next(treeiter)

    def _compute_rect_widths(self):
        allocated_width = len(self._devices_list) - 1  # spacing
        width_dict = {}

        # set minimal sizes
        treeiter = self._devices_list.get_iter_first()
        while treeiter:
            if self._devices_list.iter_has_child(treeiter):
                # allocate minimal sizes for child devices
                min_size = 0
                child_iter = self._devices_list.iter_children(treeiter)
                while child_iter:
                    # for 'child' devices, minimal size is a half of 'normal' device
                    width_dict[self._devices_list[child_iter][0]] = RECT_MIN_SIZE // 2
                    min_size += RECT_MIN_SIZE // 2
                    child_iter = self._devices_list.iter_next(child_iter)

                # minimal size for parent depends on number of children, but can't be
                # smaller than actual RECT_MIN_SIZE for device
                if min_size < RECT_MIN_SIZE:
                    min_size = RECT_MIN_SIZE
            else:
                min_size = RECT_MIN_SIZE
            width_dict[self._devices_list[treeiter][0]] = min_size
            allocated_width += min_size

            treeiter = self._devices_list.iter_next(treeiter)

        # already allocated all available space (or more) just with minimal sizes
        if allocated_width >= self._view_width:
            return width_dict

        # allocate remaining space
        else:
            treeiter = self._devices_list.get_iter_first()
            self._allocate_remaining_space(treeiter, self._view_width, allocated_width, width_dict)

        # allocate space for child devices
        # (had to wait until width of parent is final)
        treeiter = self._devices_list.get_iter_first()
        while treeiter:
            if self._devices_list.iter_has_child(treeiter):
                children_allocated = self._devices_list.iter_n_children(treeiter) * (RECT_MIN_SIZE // 2)
                self._allocate_remaining_space(treeiter=self._devices_list.iter_children(treeiter),
                                               available_width=width_dict[self._devices_list[treeiter][0]],
                                               allocated_width=children_allocated,
                                               width_dict=width_dict)
            treeiter = self._devices_list.iter_next(treeiter)

        return width_dict

    def _allocate_remaining_space(self, treeiter, available_width, allocated_width, width_dict):
        """ Allocate remaining space (px) for devices based on its size

            :param treeiter: first iter on given level (or None for first iter)
            :type treeiter: Gtk.TreeIter
            :param available_width: total available width for rectangles in px
            :type available_width: int
            :param allocated_width: currently allocated (used) width
            :type allocated_width: int
            :param width_dict: dict with devices and currently allocated with
            :type width_dict: dict

        """

        total_size = self._get_total_device_size(treeiter)
        if total_size == 0:
            return

        remaining_space = (available_width - allocated_width)
        if not remaining_space:
            return

        while treeiter:
            device = self._devices_list[treeiter][0]
            extra_space = int(remaining_space * (device.size.convert_to() / total_size))
            width_dict[device] += extra_space
            allocated_width += extra_space

            treeiter = self._devices_list.iter_next(treeiter)

        # still some space remaining, probably because of rounding
        # just add it to the first device in dict
        if allocated_width < available_width:
            width_dict[list(width_dict.keys())[0]] += (allocated_width - available_width)

    def _get_total_device_size(self, treeiter=None):
        """ Return size (in bytes) of all devices on current level

            :param treeiter: first iter on given level (or None for first iter)
            :type treeiter: Gtk.TreeIter or None

        """

        if not treeiter:
            treeiter = self._devices_list.get_iter_first()

        total_size = 0
        while treeiter:
            total_size += self._devices_list[treeiter][0].size.convert_to()
            treeiter = self._devices_list.iter_next(treeiter)

        return total_size

    def _new_rectangle(self, device, rtype="", width=-1, height=-1):
        button_group = self.rectangles[0] if self.rectangles else None

        rect = Rectangle(rtype, button_group, width, height, device)
        rect.connect("toggled", self._on_rectangle_toggle)
        rect.connect("button-release-event", self._on_button_release)
        rect.connect("button-press-event", self._on_button_press)
        self.rectangles.append(rect)

        return rect

    def _get_child_position(self, child_iter):
        parent_iter = self._devices_list.iter_parent(child_iter)
        num_childs = self._devices_list.iter_n_children(parent_iter)

        if num_childs == 1:
            return "single"
        elif self._devices_list[child_iter][0] == self._devices_list[self._devices_list.iter_nth_child(parent_iter, 0)][0]:
            return "first"
        elif self._devices_list[child_iter][0] == self._devices_list[self._devices_list.iter_nth_child(parent_iter, num_childs - 1)][0]:
            return "last"
        else:
            return "inner"

    def select_rectanlge(self, device):
        for rect in self.rectangles:
            if rect.device == device:
                rect.set_active(True)

    def _on_rectangle_toggle(self, button):
        if not self._ignore_toggle:
            self._ignore_toggle = True
            self.blivet_gui.list_partitions.select_device(button.device)
            self._ignore_toggle = False

    def _on_button_release(self, button, event):
        if event.button == 3:
            self._on_rectangle_toggle(button)  # select the button
            self.blivet_gui.popup_menu.menu.popup_at_pointer(None)

    def _on_button_press(self, button, event):
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            if button.device.is_disk or button.device.type in ("lvmvg", "btrfs volume", "mdarray"):
                self.blivet_gui.switch_device_view(button.device)
