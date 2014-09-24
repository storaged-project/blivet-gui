# -*- coding: utf-8 -*-
# dialogs.py
# Gtk.DrawingArea for device visualization
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

from gi.repository import Gtk, Gdk, Gio

import gettext

import cairo

#------------------------------------------------------------------------------#

APP_NAME = "blivet-gui"

dirname, filename = os.path.split(os.path.abspath(__file__))

gettext.bindtextdomain('blivetgui', dirname + '/i18n')
gettext.textdomain('blivetgui')
_ = gettext.gettext

#------------------------------------------------------------------------------#

class cairo_rectangle():

    def __init__(self, x, y, width, height, color):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color

    def is_in(self, p_x, p_y):
        """ Is point [p_x, p_y] inside this rectangle

            :param p_x: point x coordinate
            :type p_x: int
            :param p_y: point y coordinate
            :type p_y: int

        """

        return (p_x >= self.x and p_x <= self.x + self.width and
            p_y >= self.y and p_y <= self.y + self.height)

    def __gt__(self, other):

        return self.height > other.height

    def __lt__(self, other):

        return self.height < other.height

    def __str__(self):
        return "Cairo rectangle object\nStarting point: [" + self.x + "|" + \
                self.y + "]\nwidth: " + self.width + " height: " + self.height

class device_canvas(Gtk.DrawingArea):

    def __init__(self, blivet_utils, list_partitions):
        Gtk.DrawingArea.__init__(self)

        self.b = blivet_utils
        self.list_partitions = list_partitions

        self.connect('draw', self.draw_event)
        self.connect('button-press-event', self.button_press_event)

        self.set_events(self.get_events()
                | Gdk.EventMask.LEAVE_NOTIFY_MASK
                | Gdk.EventMask.BUTTON_PRESS_MASK
                | Gdk.EventMask.POINTER_MOTION_MASK
                | Gdk.EventMask.POINTER_MOTION_HINT_MASK)

        # dict rectangles-partitions_list treeiters
        self.rectangles = {}

        # color changing for partitions
        self.color = 0

    def visualize_device(self, partitions_list, partitions_view, parent_device):
        """ Visualize selected device

            :param partitions_list: list of device children
            :type partitions_list: Gtk.TreeStore
            :param partitions_view: view associated with partitions_list
            :type partitions_view: Gtk.TreeView
            :param parent_device: parent device
            :type parent_device: blivet.Device

        """

        self.partitions_list = partitions_list
        self.partitions_view = partitions_view
        self.parent = parent_device

        self.rectangles = {} # delete old rectangles-treeiters

        self.queue_draw()

    def update_visualisation(self):
        """ Redraw image
        """

        self.queue_draw()

    def detect_extended(self):
        """ Detect extended partitions

        """

        extended = False
        num_logical = 0

        for partition in self.partitions:

            if hasattr(partition, "isExtended") and partition.isExtended:
                extended = True # there is extended partition

            if hasattr(partition, "isLogical") and partition.isLogical:
                num_logical += 1

        return (extended, num_logical)

    def pick_color(self, partition):

        if hasattr(partition, "isExtended") and partition.isExtended:
            return [0, 1, 1]

        elif hasattr(partition, "isFreeSpace") and partition.isFreeSpace:
            return [0.75, 0.75, 0.75]

        elif partition.format and partition.format.type == "lvmpv":
            return [0.921, 0.694, 0.239]
        elif partition.type == "lvmvg":
            return [0.874, 0.258, 0.117]
        elif partition.format and partition.format.type == "luks":
            return [0.25, 0.25, 0.25]
        elif partition.type == "btrfs volume":
            return [0.921, 0.694, 0.239]
        else:
            self.color += 1
            return [[0.239, 0.921, 0.353],
            [0.239, 0.467, 0.921]][self.color % 2]

    def compute_rectangles_size(self, partition, parent, parent_width, height,
        num_parts, parts_size, parts_left, size_left, start, depth):
        """ Compute sizes (in px) of partition rectangle

            :param partition: partition
            :type partition: blivet.Device
            :param parent: parent device
            :type parent: blivet.Device
            :param parent_width: size of parent 'element' (in px)
            :type parent_width: int
            :param height: canvas height
            :type height: int
            :param num_parts: number of partitions (children) for current parent
            :type num_parts: int
            :param parts_left: number of partitions (children) currently not drawn
            :type parts_left: int
            :param start: starting x-coordinate
            :type start: int
            :param depth: current tree depth
            :type depth: int
            :returns: rectangle size and location
            :rtype: class:cairo_rectangle

        """
        if parts_size > parent.size:
            total_size = round(parts_size.convertTo(spec="MiB"))
        else:
            total_size = round(parent.size.convertTo(spec="MiB"))

        x = start + depth

        part_width = round(partition.size.convertTo(spec="MiB"))*(parent_width)/total_size

        # last partition gets all space left
        if parts_left == 1:
            part_width = size_left

        # size of partition rect must be at least 'parent_width / (num_parts*2)'
        elif part_width < parent_width / (num_parts*2):
            part_width = parent_width / (num_parts*2)

        # we need to left space for smaller partition (at least 'width / (num_parts*2)', see above)
        elif part_width > parent_width - ((num_parts-1)* (parent_width / (num_parts*2))):
            part_width = parent_width - (num_parts-1) * (parent_width/ (num_parts*2))

        # [x, y, width, height, [r,g,b]]
        r = cairo_rectangle(round(x), depth, round(part_width), height - 2*depth,
            self.pick_color(partition))

        return r

    def draw_selected_rectangle(self, cairo_ctx, r):
        """ Draw rectangle with selection
        """

        cairo_ctx.set_source_rgb(*r.color)
        cairo_ctx.rectangle(r.x, r.y, r.width, r.height)
        cairo_ctx.fill()

        cairo_ctx.set_source_rgb(1, 1, 1)
        cairo_ctx.rectangle(r.x + 5, r.y + 5, r.width - 10, r.height - 10)
        cairo_ctx.fill()

        cairo_ctx.set_source_rgb(1, 0.98, 0.18)
        cairo_ctx.set_line_width(2)

        cairo_ctx.set_dash([2.0, 2.0])

        # top line
        cairo_ctx.move_to(r.x + 2, r.y + 2)
        cairo_ctx.line_to(r.x + r.width - 2, r.y + 2)

        # bottom line
        cairo_ctx.move_to(r.x + 2, r.y + r.height - 2)
        cairo_ctx.line_to(r.x + r.width - 2, r.y + r.height - 2)

        # left line
        cairo_ctx.move_to(r.x + 2, r.y + 2)
        cairo_ctx.line_to(r.x + 2, r.y + r.height - 2)

        # right line
        cairo_ctx.move_to(r.x + r.width - 2, r.y + 2)
        cairo_ctx.line_to(r.x + r.width - 2, r.y + r.height - 2)

        cairo_ctx.stroke()

    def draw_rectangle(self, cairo_ctx, r):
        """ Draw rectangle
        """

        cairo_ctx.set_source_rgb(*r.color)
        cairo_ctx.rectangle(r.x, r.y, r.width, r.height)
        cairo_ctx.fill()

        cairo_ctx.set_source_rgb(1, 1, 1)
        cairo_ctx.rectangle(r.x + 5, r.y + 5, r.width - 10, r.height - 10)
        cairo_ctx.fill()

    def draw_info(self, cairo_ctx, r, name, size):

        # default system font
        settings = Gio.Settings('org.gnome.desktop.interface')
        font_name = settings.get_string('font-name')

        cairo_ctx.set_source_rgb(0, 0, 0)
        cairo_ctx.select_font_face(font_name, cairo.FONT_SLANT_NORMAL,
            cairo.FONT_WEIGHT_NORMAL)

        while cairo_ctx.text_extents(name)[-2] > r.width - 20:
            name = name[:-1]
            if len(name) > 3:
                name = name[:-3] + "..."

        # name of partition
        cairo_ctx.move_to(r.x + r.width/2 - cairo_ctx.text_extents(name)[-2]/2,
            r.y + r.height/2)
        cairo_ctx.show_text(name)

        while cairo_ctx.text_extents(size)[-2] > r.width - 20:
            size = size[:-1]
            if len(size) > 3:
                size = size[:-3] + "..."

        # size of partition
        cairo_ctx.move_to(r.x + r.width/2 - cairo_ctx.text_extents(size)[-2]/2,
            r.y + r.height/2 + 10)
        cairo_ctx.show_text(size)

    def draw_event(self, da, cairo_ctx):
        """ Drawing event for partition visualisation

            :param da: drawing area
            :type da: Gtk.DrawingArea
            :param cairo_ctx: Cairo context
            :type cairo_ctx: Cairo.Context

        """

        self.color = 0
        self.cairo_ctx = cairo_ctx

        # paint the canvas
        cairo_ctx.set_source_rgb(1, 1, 1)
        cairo_ctx.paint()

        # cavas size
        width = da.get_allocated_width()
        height = da.get_allocated_height()

        # get selected line
        selection = self.partitions_view.get_selection()
        model, selected_treeiter = selection.get_selected()

        def draw_loop(self, treeiter, start, depth, parent, parent_size):
            """ Recursive function to draw rectangles

                :param treeiter: iter pointing at root
                :type treeiter: Gtk.TreeIter
                :param start: point to start width drawing (end of last drawn rect)
                :type start: int
                :param depth: depth in tree*5 (5 px is visible part of parent rect)
                :type depth: int
                :param parent: parent device
                :type parent: blivet.Device
                :param parent_size: current size of parent rect in px
                :type parent_size: int

            """

            # count number of partitions on current level
            num_parts = 0
            parts_size = 0
            it = treeiter

            while it:
                num_parts += 1
                parts_size += self.partitions_list[treeiter][0].size
                it = self.partitions_list.iter_next(it)

            if depth != 0:
                parent_size -= 10
            parts_left = num_parts
            size_left = parent_size

            while treeiter != None:
                rectangle = self.compute_rectangles_size(self.partitions_list[treeiter][0],
                    parent, parent_size, height, num_parts, parts_size, parts_left,
                    size_left, start, depth)
                self.rectangles[rectangle] = treeiter

                size_left -= rectangle.width
                parts_left -= 1

                if selected_treeiter and self.partitions_list.get_path(treeiter) == self.partitions_list.get_path(selected_treeiter):
                    self.draw_selected_rectangle(cairo_ctx, rectangle)

                else:
                    self.draw_rectangle(cairo_ctx, rectangle)

                self.draw_info(cairo_ctx, rectangle, self.partitions_list[treeiter][0].name,
                    str(self.partitions_list[treeiter][0].size))

                if self.partitions_list.iter_has_child(treeiter):
                    childiter = self.partitions_list.iter_children(treeiter)
                    draw_loop(self, childiter, start, depth + 5,
                        self.partitions_list[treeiter][0], rectangle.width)

                start += rectangle.width
                treeiter = self.partitions_list.iter_next(treeiter)

            return

        root_iter = self.partitions_list.get_iter_first()
        draw_loop(self, root_iter, 0, 0, self.parent, width)

        return True

    def button_press_event(self, da, event):
        """ Button press event for partition image
        """

        result = None

        for rectangle in self.rectangles:
            if rectangle.is_in(event.x, event.y):
                if not result:
                    result = rectangle
                elif result > rectangle:
                    # there is another rectangle (device) over previously selected
                    result = rectangle

        if result:

            path = self.partitions_list.get_path(self.rectangles[result])

            self.partitions_view.set_cursor(path)
            self.queue_draw()

        # right button popup menu
        if event.button == 3:
            self.list_partitions.popup_menu.get_menu.popup(None, None, None,
                None, event.button, event.time)

        return True
