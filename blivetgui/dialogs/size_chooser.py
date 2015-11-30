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

from ..i18n import _
from ..gui_utils import locate_ui_file

# ---------------------------------------------------------------------------- #

SUPPORTED_UNITS = ["B", "kB", "MB", "GB", "TB", "kiB", "MiB", "GiB", "TiB"]
UNIT_DICT = {"B": size.B, "kB": size.KB, "MB": size.MB, "GB": size.GB, "TB": size.TB,
             "kiB": size.KiB, "MiB": size.MiB, "GiB": size.GiB, "TiB": size.TiB}

# ---------------------------------------------------------------------------- #


def conv(unit):
    """ Convert unit string to blivet.size unit
    """

    if unit not in UNIT_DICT.keys():
        raise ValueError

    return UNIT_DICT[unit]


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


class SizeChooserArea(object):

    def __init__(self, dialog_type, device_name, max_size, min_size, current_size=None, update_clbk=None):
        """

            :param dialog_type: type of dialog ('add' or 'edit')
            :type dialog_type: str
            :param device_name: name of device (edited or parent)
            :type device_name: str
            :param max_size: maximum size that user can choose
            :type max_size: blivet.size.Size
            :param min_size: minimum size that user can choose
            :type min_size: blivet.size.Size
            :param current_size: current size of edited device
            :type current_size: blivet.size.Size
            :param update_clbk: callback to update other size chooser in dialog
            :type update_clbk: method

        """

        self.dialog_type = dialog_type

        self.device_name = device_name

        self.max_size = max_size
        self.min_size = min_size
        self.current_size = current_size

        self.update_clbk = update_clbk

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain("blivet-gui")
        self.builder.add_from_file(locate_ui_file("size_area.ui"))

        self.widgets = self.builder.get_objects()

        self.selected_unit = None

        self.frame = self.builder.get_object("frame_size")
        self.frame.set_label(device_name)

        self.scale, self.spin_size, self.unit_chooser = self.set_size_widgets()

    def set_size_widgets(self, unit=_("MiB")):
        """ Configure size widgets (Gtk.Scale, Gtk.SpinButton)
        """

        scale = self.builder.get_object("scale_size")
        spin = self.builder.get_object("spinbutton_size")

        adjustment = Gtk.Adjustment(0, self.min_size.convert_to(conv(unit)), self.max_size.convert_to(conv(unit)), 1, 10, 0)

        scale.set_adjustment(adjustment)
        spin.set_adjustment(adjustment)

        scale.add_mark(self.min_size.convert_to(conv(unit)), Gtk.PositionType.BOTTOM, str(self.min_size))

        if self.dialog_type == "add":
            scale.set_value(self.max_size.convert_to(conv(unit)))
            scale.add_mark(self.max_size.convert_to(conv(unit)), Gtk.PositionType.BOTTOM, str(self.max_size))
            spin.set_value(self.max_size.convert_to(conv(unit)))

        elif self.dialog_type == "edit":
            scale.set_value(self.current_size.convert_to(conv(unit)))
            scale.add_mark(self.max_size.convert_to(conv(unit)), Gtk.PositionType.BOTTOM, str(self.max_size))
            spin.set_value(self.current_size.convert_to(conv(unit)))

        combobox_size = self.builder.get_object("combobox_size")
        for unit in SUPPORTED_UNITS:
            combobox_size.append_text(unit)

        # set MiB as default
        self.selected_unit = "MiB"
        combobox_size.set_active(SUPPORTED_UNITS.index("MiB"))

        combobox_size.connect("changed", self.on_unit_combo_changed)
        scale.connect("value-changed", self.scale_moved, spin)
        spin.connect("value-changed", self.spin_size_moved, scale)

        return scale, spin, combobox_size

    def adjust_size_scale(self, selected_size, unit="MiB"):
        """ Adjust size scale with selected size and unit
        """

        self.scale.set_range(self.min_size.convert_to(conv(unit)), self.max_size.convert_to(conv(unit)))
        self.scale.clear_marks()

        increment, digits = get_size_precision(self.min_size.convert_to(conv(unit)), self.max_size.convert_to(conv(unit)))
        self.scale.set_increments(increment, increment * 10)
        self.scale.set_digits(digits)

        self.scale.add_mark(0, Gtk.PositionType.BOTTOM,
                            format(self.min_size.convert_to(conv(unit)), "." + str(digits) + "f") + " " + unit)
        self.scale.add_mark(float(self.max_size.convert_to(conv(unit))), Gtk.PositionType.BOTTOM,
                            format(self.max_size.convert_to(conv(unit)), "." + str(digits) + "f") + " " + unit)

        self.spin_size.set_range(self.min_size.convert_to(conv(unit)),
                                 self.max_size.convert_to(conv(unit)))
        self.spin_size.set_increments(increment, increment * 10)
        self.spin_size.set_digits(digits)

        if selected_size > self.max_size:
            self.scale.set_value(self.max_size.convert_to(conv(unit)))
        elif selected_size < self.min_size:
            self.scale.set_value(self.min_size.convert_to(conv(unit)))
        else:
            self.scale.set_value(selected_size.convert_to(conv(unit)))

    def update_size_limits(self, min_size=None, max_size=None):
        if min_size:
            self.min_size = min_size
        if max_size:
            self.max_size = max_size

        self.adjust_size_scale(self.get_selected_size(), self.selected_unit)

    def set_selected_size(self, selected_size):
        self.scale.set_value(selected_size.convert_to(conv(self.selected_unit)))

    def get_selected_size(self):
        return size.Size(str(self.scale.get_value()) + " " + self.selected_unit)

    def on_unit_combo_changed(self, combo):
        """ On-change action for unit combo
        """

        new_unit = combo.get_active_text()
        old_unit = self.selected_unit
        self.selected_unit = new_unit

        selected_size = size.Size(str(self.scale.get_value()) + " " + old_unit)

        self.adjust_size_scale(selected_size, new_unit)
        return

    def scale_moved(self, scale, spin):
        """ On-change action for size scale
        """

        spin.set_value(scale.get_value())

        selected_size = size.Size(str(self.scale.get_value()) + " " + self.selected_unit)

        if self.update_clbk:
            self.update_clbk(selected_size)

    def spin_size_moved(self, spin, scale):
        """ On-change action for size spin
        """

        scale.set_value(spin.get_value())

    def destroy(self):
        """ Destroy all size widgets
        """

        for widget in self.widgets:
            if hasattr(widget, "hide"):
                widget.hide()
                widget.destroy()

    def show(self):
        """ Show all size widgets
        """

        self.set_visible(True)

    def hide(self):
        """ Hide all size widgets
        """

        self.set_visible(False)

    def set_visible(self, visibility):
        """ Hide/show all size widgets
        """

        for widget in self.widgets:
            if hasattr(widget, "set_visible"):
                widget.set_visible(visibility)

    def set_sensitive(self, sensitivity):
        """ Set all widgets sensitivity

            :param sensitivity: sensitivity
            :type sensitivity: bool

        """
        for widget in self.widgets:
            if hasattr(widget, "set_sensitive"):
                widget.set_sensitive(sensitivity)

    def get_sensitive(self):
        return all([widget.get_sensitive() for widget in self.widgets if hasattr(widget, "get_sensitive")])

    def get_selection(self):
        """ Get selected size
        """

        unit = UNIT_DICT[self.selected_unit].abbr + "B"  # selected_unit is localized
        selected_size = size.Size(str(self.scale.get_value()) + " " + unit)

        return selected_size
