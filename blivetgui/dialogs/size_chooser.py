# -*- coding: utf-8 -*-
# size_chooser.py
# Widget allowing to select device size either Gtk.Scale or Gtk.SpinButton
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

from gi.repository import Gtk

from blivet import size

from ..gui_utils import locate_ui_file

from collections import OrderedDict, namedtuple

# ---------------------------------------------------------------------------- #

UNITS = OrderedDict([("B", size.B), ("kB", size.KB), ("MB", size.MB),
                     ("GB", size.GB), ("TB", size.TB), ("KiB", size.KiB),
                     ("MiB", size.MiB), ("GiB", size.GiB), ("TiB", size.TiB)])
# ---------------------------------------------------------------------------- #


def get_size_precision(down_limit, up_limit):
    """ Get precision for scale
    """

    step = 1.0
    digits = 0

    while True:
        if down_limit >= 1.0:
            break

        down_limit *= 10
        step /= 10
        digits += 1

    # always offer at least 10 steps to adjust size
    if up_limit - down_limit < 10 * step:
        step /= 10
        digits += 1

    return step, digits

# ---------------------------------------------------------------------------- #


SignalHandler = namedtuple("SignalHandler", ["method", "args"])


class SizeChooser(object):

    def __init__(self, max_size, min_size, current_size=None):
        """
            :param max_size: maximum size that user can choose
            :type max_size: blivet.size.Size
            :param min_size: minimum size that user can choose
            :type min_size: blivet.size.Size
            :param current_size: current size of edited device
            :type current_size: blivet.size.Size
        """

        self._max_size = max_size
        self._min_size = min_size

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain("blivet-gui")
        self.builder.add_from_file(locate_ui_file("size_chooser.ui"))

        self.widgets = self.builder.get_objects()

        self.grid = self.builder.get_object("grid")

        self.selected_unit = size.MiB
        self.size_change_handler = None
        self.unit_change_handler = None

        self._scale, self._spin, self._unit_chooser = self._set_size_widgets()

        # for edited device, set its current size
        if current_size is not None:
            self.selected_size = current_size
        else:
            self.selected_size = max_size

    @property
    def selected_size(self):
        return size.Size(str(self._scale.get_value()) + " " + self.selected_unit.abbr + "B")

    @selected_size.setter
    def selected_size(self, selected_size):
        self._scale.set_value(selected_size.convert_to(self.selected_unit))

    @property
    def max_size(self):
        return self._max_size

    @max_size.setter
    def max_size(self, max_size):
        self._max_size = max_size
        self._reset_size_widgets(self.selected_size)

    @property
    def min_size(self):
        return self._min_size

    @min_size.setter
    def min_size(self, min_size):
        self._min_size = min_size
        self._reset_size_widgets(self.selected_size)

    def connect(self, signal, method, *args):
        """ Connect a signal hadler """

        if signal == "size-changed":
            self.size_change_handler = SignalHandler(method=method, args=args)

        elif signal == "unit-changed":
            self.unit_change_handler = SignalHandler(method=method, args=args)

        else:
            raise TypeError("Unknown signal type %s" % signal)

    def _set_size_widgets(self):
        """ Configure size widgets (Gtk.Scale, Gtk.SpinButton) """

        scale = self.builder.get_object("scale_size")
        spin = self.builder.get_object("spinbutton_size")

        adjustment = Gtk.Adjustment(0, self.min_size.convert_to(size.MiB),
                                    self.max_size.convert_to(size.MiB), 1, 10, 0)

        scale.set_adjustment(adjustment)
        spin.set_adjustment(adjustment)

        scale.add_mark(self.min_size.convert_to(size.MiB),
                       Gtk.PositionType.BOTTOM, str(self.min_size))
        scale.add_mark(self.max_size.convert_to(size.MiB),
                       Gtk.PositionType.BOTTOM, str(self.max_size))

        combobox_size = self.builder.get_object("combobox_size")
        for unit in list(UNITS.keys()):
            combobox_size.append_text(unit)

        # set MiB as default
        self.selected_unit = size.MiB
        combobox_size.set_active(list(UNITS.keys()).index("MiB"))

        combobox_size.connect("changed", self._on_unit_changed)
        scale.connect("value-changed", self._on_scale_moved, spin)
        spin.connect("value-changed", self._on_spin_moved, scale)

        return scale, spin, combobox_size

    def _reset_size_widgets(self, selected_size):
        """ Adjust size scale with selected size and unit """

        unit = self.selected_unit

        self._scale.set_range(self.min_size.convert_to(unit),
                              self.max_size.convert_to(unit))
        self._scale.clear_marks()

        increment, digits = get_size_precision(self.min_size.convert_to(unit),
                                               self.max_size.convert_to(unit))
        self._scale.set_increments(increment, increment * 10)
        self._scale.set_digits(digits)

        self._scale.add_mark(0, Gtk.PositionType.BOTTOM,
                             format(self.min_size.convert_to(unit),
                                    "." + str(digits) + "f") + " " + unit.abbr + "B")
        self._scale.add_mark(float(self.max_size.convert_to(unit)), Gtk.PositionType.BOTTOM,
                             format(self.max_size.convert_to(unit),
                                    "." + str(digits) + "f") + " " + unit.abbr + "B")

        self._spin.set_range(self.min_size.convert_to(unit),
                             self.max_size.convert_to(unit))
        self._spin.set_increments(increment, increment * 10)
        self._spin.set_digits(digits)

        if selected_size > self.max_size:
            self.selected_size = self.max_size
        elif selected_size < self.min_size:
            self.selected_size = self.min_size
        else:
            self.selected_size = selected_size

    def update_size_limits(self, min_size=None, max_size=None):
        if min_size:
            self.min_size = min_size
        if max_size:
            self.max_size = max_size

        self._reset_size_widgets(self.selected_size)

    def _on_unit_changed(self, combo):
        """ On-change action for unit combo """

        new_unit = UNITS[combo.get_active_text()]
        old_unit = self.selected_unit
        self.selected_unit = new_unit

        selected_size = size.Size(str(self._scale.get_value()) + " " + old_unit.abbr + "B")

        self._reset_size_widgets(selected_size)

        if self.unit_change_handler is not None:
            self.unit_change_handler.method(self.selected_unit, *self.unit_change_handler.args)

    def _on_scale_moved(self, scale, spin):
        """ On-change action for size scale """

        spin.set_value(scale.get_value())

        if self.size_change_handler is not None:
            self.size_change_handler.method(self.selected_size, *self.size_change_handler.args)

    def _on_spin_moved(self, spin, scale):
        """ On-change action for size spin """

        scale.set_value(spin.get_value())

    def destroy(self):
        """ Destroy all size widgets """

        for widget in self.widgets:
            widget.hide()
            widget.destroy()

    def show(self):
        """ Show all size widgets """

        self.set_visible(True)

    def hide(self):
        """ Hide all size widgets """

        self.set_visible(False)

    def set_visible(self, visibility):
        """ Hide/show all size widgets

            :param visibility: visibility
            :type visibility: bool

        """

        for widget in self.widgets:
            widget.set_visible(visibility)

    def set_sensitive(self, sensitivity):
        """ Set all widgets sensitivity

            :param sensitivity: sensitivity
            :type sensitivity: bool

        """
        for widget in self.widgets:
            widget.set_sensitive(sensitivity)

    def get_sensitive(self):
        return all([widget.get_sensitive() for widget in self.widgets])

    def get_selection(self):
        """ Get selected size """

        return self.selected_size
