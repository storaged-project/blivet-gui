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
# ---------------------------------------------------------------------------- #

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

from gi.repository import Gtk, Gdk

from .rectangle import Rectangle

# ---------------------------------------------------------------------------- #


class PhysicalView(object):
    def __init__(self, blivet_gui):
        """
        Initialize the gui boxes.

        Args:
            self: (todo): write your description
            blivet_gui: (todo): write your description
        """
        self.blivet_gui = blivet_gui

        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.vbox.set_name("bg-visualization")

        self.rectangles = []
        self.boxes = []

        self._devices_list = None

    def visualize_parents(self, devices_list):
        """
        Visualize parents of the device.

        Args:
            self: (todo): write your description
            devices_list: (todo): write your description
        """
        self._devices_list = devices_list
        self._clear()

        root_iter = devices_list.get_iter_first()
        self._visualization_loop(root_iter)

        self.vbox.show_all()

    def _visualization_loop(self, treeiter, box=None, rect_widths=None):
        """
        Make a loop.

        Args:
            self: (todo): write your description
            treeiter: (todo): write your description
            box: (todo): write your description
            rect_widths: (todo): write your description
        """
        while treeiter:
            depth = self._devices_list.iter_depth(treeiter)
            # lower level of the tree -> visualization of childs
            if depth:
                (device, is_valid) = self._devices_list[treeiter]

                if is_valid:
                    rect = self._new_rectangle(device, "child-valid-" + self._get_child_position(treeiter), width=rect_widths[device])
                else:
                    rect = self._new_rectangle(device, "child-invalid-" + self._get_child_position(treeiter), width=rect_widths[device])
                box.pack_start(child=rect, expand=True, fill=True, padding=0)

            else:
                parent_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                self.boxes.append(parent_box)
                self.vbox.pack_start(child=parent_box, expand=False, fill=False, padding=0)
                rect = self._new_rectangle(self._devices_list[treeiter][0], "root-device", width=100)
                parent_box.pack_start(child=rect, expand=False, fill=False, padding=0)

                # every "root" device has children; if not, something is very wrong
                if not self._devices_list.iter_has_child(treeiter):
                    raise RuntimeError

                child_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
                parent_box.pack_start(child=child_box, expand=True, fill=True, padding=0)
                self.boxes.append(child_box)

                # it's not possible to get width of child box, so we take width
                # of the vbox a substract width of parent device and its padding
                box_width = self.vbox.get_allocation().width - 100 - 2 * 10
                # compute rectangle widths for children
                widths = self._compute_rect_widths(parent_iter=treeiter, view_width=box_width)

                child_iter = self._devices_list.iter_children(treeiter)
                self._visualization_loop(child_iter, child_box, rect_widths=widths)

            treeiter = self._devices_list.iter_next(treeiter)

    def _compute_rect_widths(self, parent_iter, view_width):
        """
        Compute the widths of each element in the tree.

        Args:
            self: (todo): write your description
            parent_iter: (int): write your description
            view_width: (int): write your description
        """
        width_dict = {}
        allocated_width = 0

        # set minimal sizes
        treeiter = self._devices_list.iter_children(parent_iter)
        while treeiter:
            (device, is_valid) = self._devices_list[treeiter]
            if is_valid:
                min_size = 100  # min_size for valid devices
            else:
                min_size = 10  # min_size for invalid devices
            width_dict[device] = min_size
            allocated_width += min_size

            treeiter = self._devices_list.iter_next(treeiter)

        # already allocated all available space (or more) just with minimal sizes
        if allocated_width >= view_width:
            return width_dict

        # allocate remaining space
        self._allocate_remaining_space(self._devices_list.iter_children(parent_iter), view_width, allocated_width, width_dict)

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
            if width_dict:  # empty dict
                width_dict[list(width_dict.keys())[0]] += (allocated_width - available_width)

    def _get_total_device_size(self, treeiter):
        """ Return size (in bytes) of all devices on current level

            :param treeiter: first iter on given level
            :type treeiter: Gtk.TreeIter

        """

        total_size = 0
        while treeiter:
            total_size += self._devices_list[treeiter][0].size.convert_to()
            treeiter = self._devices_list.iter_next(treeiter)

        return total_size

    def _clear(self):
        """
        Clears all boxes.

        Args:
            self: (todo): write your description
        """
        for rect in self.rectangles:
            rect.hide()
            rect.destroy()
        self.rectangles = []

        for box in self.boxes:
            box.hide()
            box.destroy()
        self.boxes = []

    def _new_rectangle(self, device, rtype="", width=90, height=90):
        """
        Return a new rectangle.

        Args:
            self: (todo): write your description
            device: (todo): write your description
            rtype: (str): write your description
            width: (float): write your description
            height: (todo): write your description
        """
        # no labels for 'invalid rectangles' in physical view
        label = not rtype.startswith("child-invalid-")

        rect = Rectangle(rtype, None, width, height, device, label)
        rect.connect("button-press-event", self._on_button_press)
        self.rectangles.append(rect)

        return rect

    def _get_child_position(self, child_iter):
        """
        Get the child of the devices.

        Args:
            self: (todo): write your description
            child_iter: (int): write your description
        """
        parent_iter = self._devices_list.iter_parent(child_iter)
        num_childs = self._devices_list.iter_n_children(parent_iter)

        if self._devices_list[child_iter][0] == self._devices_list[self._devices_list.iter_nth_child(parent_iter, 0)][0]:
            return "first"
        elif self._devices_list[child_iter][0] == self._devices_list[self._devices_list.iter_nth_child(parent_iter, num_childs - 1)][0]:
            return "last"
        else:
            return "inner"

    def _on_button_press(self, button, event):
        """
        Button press press press press.

        Args:
            self: (todo): write your description
            button: (todo): write your description
            event: (todo): write your description
        """
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            if button.device.is_disk or button.device.type in ("lvmvg", "btrfs volume", "mdarray"):
                self.blivet_gui.switch_device_view(button.device)
