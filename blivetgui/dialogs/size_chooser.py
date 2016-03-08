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

from . helpers import supported_raids

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
        if down_limit >= 1.0 or down_limit >= 0:
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


from blivet.devicelibs.raid import get_raid_level


class GUIWidget(object):

    def __init__(self, glade_file):

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain("blivet-gui")
        self.builder.add_from_file(locate_ui_file(glade_file))

        self.widgets = self.builder.get_objects()

        self.blocked_signals = []

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
            if hasattr(widget, "set_visible"):  # for liststores
                widget.set_visible(visibility)

    def set_sensitive(self, sensitivity):
        """ Set all widgets sensitivity

            :param sensitivity: sensitivity
            :type sensitivity: bool

        """
        for widget in self.widgets:
            if hasattr(widget, "set_sensitive"):  # for liststores
                widget.set_sensitive(sensitivity)

    def block_signal(self, signal, block):
        if block:
            self.blocked_signals.append(signal)
        else:
            if signal in self.blocked_signals:
                self.blocked_signals.remove(signal)

    def get_sensitive(self):
        return all([widget.get_sensitive() for widget in self.widgets if hasattr(widget, "get_sensitive")])


class RaidChooser(GUIWidget):

    def __init__(self):

        GUIWidget.__init__(self, "raid_chooser.ui")

        self.supported_raids = supported_raids()

        self.box = self.builder.get_object("box")
        self.combobox_raid = self.builder.get_object("combobox_raid")
        self.liststore_raid = self.builder.get_object("liststore_raid")

        self._changed_signal = None

        self.raid_change_handler = None

    def update(self, device_type, parents):
        if self._changed_signal:
            self.combobox_raid.handler_block(self._changed_signal)

        self.liststore_raid.clear()

        for raid in self.supported_raids[device_type]:
            if raid.name == "container":
                continue
            if len(parents) >= raid.min_members:
                self.liststore_raid.append((raid.name, raid))

        if self._changed_signal:
            self.combobox_raid.handler_unblock(self._changed_signal)

        self.combobox_raid.set_active(0)

        # select linear raid type for lvs
        try:
            self.selected = "linear"
        except ValueError:
            pass

        if len(self.liststore_raid) > 1:
            self.set_sensitive(True)
        else:
            self.set_sensitive(False)

    @property
    def selected(self):
        it = self.combobox_raid.get_active_iter()

        if it is None:
            return
        else:
            return self.liststore_raid[it][0]

    @selected.setter
    def selected(self, raid_type):

        for idx, raid in enumerate(self.liststore_raid):
            if raid[0] == raid_type:
                self.combobox_raid.set_active(idx)
                return

        # selected raid type not found
        raise ValueError("RAID type %s is not available for selection." % raid_type)

    def connect(self, signal, method, *args):
        """ Connect a signal hadler """

        if signal == "changed":
            self._changed_signal = self.combobox_raid.connect("changed", method, args)

        else:
            raise TypeError("Unknown signal type %s" % signal)


class SizeArea(GUIWidget):

    def __init__(self, device_type, parents, min_size, raid_type):

        GUIWidget.__init__(self, "size_area.ui")

        self.device_type = device_type
        self.parents = parents
        self.raid_type = raid_type

        self.frame = self.builder.get_object("frame_size")
        self.grid = self.builder.get_object("grid")

        self._min_size = min_size
        self._max_size = None

        # is the advanced selection active?
        self.advanced_selection = False

        self.main_chooser = SizeChooser(max_size=self.max_size, min_size=self.min_size)
        self.main_chooser.connect("size-changed", self._on_main_size_changed)
        self.grid.attach(self.main_chooser.grid, 0, 0, 5, 1)

        self._add_advanced_area()

    def _add_advanced_area(self):

        checkbutton_manual = self.builder.get_object("checkbutton_manual")
        checkbutton_manual.connect("toggled", self._on_manual_toggled)

        # remove checkbutton_manual from widgets so it isn't affected when setting size area (in)sensitive
        self.widgets.remove(checkbutton_manual)

        if len(self.parents) > 1:
            if self.device_type in ("lvmthinpool", "lvm snapshot"):
                checkbutton_manual.set_sensitive(False)
            else:
                checkbutton_manual.set_sensitive(True)
        else:
            checkbutton_manual.set_sensitive(False)

        self.parent_area = ParentArea(self.device_type, self.parents, self.min_size, self.raid_type, self.main_chooser)

        self.parent_area.connect("size-changed", self._on_advanced_size_changed)
        self.grid.attach(self.parent_area.frame, 0, 2, 5, 1)
        self.widgets.append(self.parent_area)

        self.show()

        # raid selected, only advanced size selection should be available
        if self.raid_type not in ("linear", "single", None):
            checkbutton_manual.set_active(True)
            checkbutton_manual.set_sensitive(False)
        else:
            self.parent_area.hide()
            self.parent_area.total_size = self.max_size  # update selected size of parent areas

    @property
    def min_size(self):
        return self._min_size

    @min_size.setter
    def min_size(self, new_size):

        if new_size >= self.max_size:
            raise ValueError("New minimum size is larger than current maximum size.")

        self._min_size = new_size

        # set min size for main chooser
        self.main_chooser.min_size = new_size

        # set min size for all size chooser areas
        for chooser in self.parent_area.choosers:
            chooser.min_size = new_size

    @property
    def max_size(self):
        if self._max_size is None:
            if self.raid_type not in ("linear", "single", None):
                raid_level = get_raid_level(self.raid_type)
                self._max_size = raid_level.get_net_array_size(len(self.parents),
                                                               min([free for _parent, free in self.parents]))
            else:
                self._max_size = sum([free for _parent, free in self.parents])

        return self._max_size

    @max_size.setter
    def max_size(self, new_size):
        if self.device_type not in ("lvmthinpool", "lvmlv", None):  # FIXME
            raise RuntimeError("Setting maximum size is not allowed for %s device type." % self.device_type)

        self._max_size = new_size
        self.main_chooser.max_size = new_size

    def _on_manual_toggled(self, checkbutton):
        """ Advanced selection toggled """

        if checkbutton.get_active():
            self.parent_area.show()
            if self.device_type not in ("lvmlv", "lvmthinpool", "lvm snapshot"):
                self.main_chooser.set_sensitive(False)
            self.advanced_selection = True

            # for lvmlv show raid chooser inside parent area
            if self.device_type == "lvmlv":
                self.parent_area.raid_chooser.update(self.device_type, self.parents)

        else:
            self.parent_area.hide()
            self.main_chooser.set_sensitive(True)
            self.advanced_selection = False

            # when hiding advanced selection, automatically choose all parents
            for chooser in self.parent_area.choosers:
                chooser.selected = True
            self.main_chooser.max_size = self.parent_area.total_max
            self.main_chooser.selected_size = self.main_chooser.max_size

    def _on_advanced_size_changed(self, total_size):
        """ Handler for size change in advanced selection """

        if self.main_chooser.selected_size != total_size:
            self.main_chooser.selected_size = total_size

    def _on_main_size_changed(self, total_size):
        """ Handler for size change in main size selection """

        if self.parent_area.total_size != total_size:
            self.parent_area.total_size = total_size

    def get_selection(self):
        return self.parent_area.get_selection()


class ParentArea(GUIWidget):

    def __init__(self, device_type, parents, min_size, raid_type, main_chooser):

        GUIWidget.__init__(self, "parent_area.ui")

        self.status = False  # is parent area visible/active?

        self.device_type = device_type
        self.parents = parents
        self.min_size = min_size
        self.raid_type = raid_type

        self.main_chooser = main_chooser

        self.choosers = []  # parent choosers in this area

        self.size_change_handler = None

        self.frame = self.builder.get_object("frame")
        self.grid = self.builder.get_object("grid")

        self.raid_chooser = RaidChooser()
        self.raid_chooser.connect("changed", self._on_raid_changed)
        self.grid.attach(self.raid_chooser.box, 0, 0, 1, 1)

        self._add_parent_choosers()
        self.show()

        # hide raid chooser for non-lvs
        if self.device_type != "lvmlv":
            self.raid_chooser.hide()

    def _add_parent_choosers(self):
        for idx, (parent, free) in enumerate(self.parents):
            # with raid selected, all parents have to has the same size (and max size)
            if self.raid_type not in ("linear", "single", None):
                max_size = min([free for _parent, free in self.parents])
            else:
                max_size = free

            if self.device_type in ("lvmlv", "lvmthinpool", "lvm snapshot"):
                chooser = ParentChooser(parent, False, self.min_size, max_size)
            else:
                chooser = ParentChooser(parent, True, self.min_size, max_size)
            chooser.connect("size-changed", self._on_parent_changed)
            chooser.connect("parent-toggled", self._on_parent_toggled)
            self.choosers.append(chooser)
            self.widgets.append(chooser)
            self.grid.attach(chooser.grid, 0, idx + 1, 1, 1)

            # for non-lvms parents are already selected, changes are not allowed
            if self.device_type not in ("lvmlv",):
                chooser.selected = True  # select parent
                chooser.selectable = False  # make the select button insentive

    def connect(self, signal, method, *args):
        """ Connect a signal hadler """

        if signal == "size-changed":
            self.size_change_handler = SignalHandler(method=method, args=args)

        else:
            raise TypeError("Unknown signal type %s" % signal)

    def _on_parent_changed(self, new_size, *_args):
        """ Parent selection changed -- either size or parent toggled """

        # no size choosers for lvmlv parents
        if self.device_type == "lvmlv":
            return

        # raid -- all parents have to has the same size
        if self.raid_type not in ("linear", "single", None):
            for chooser in self.choosers:
                if chooser.selected_size != new_size:
                    chooser.selected_size = new_size

        if self.size_change_handler is not None:
            self.size_change_handler.method(self.total_size, *self.size_change_handler.args)

    def _on_parent_toggled(self, *_args):
        """ Parent selection changed -- either size or parent toggled """

        # hidden, do not change max size
        if not self.status:
            return

        # update raid chooser but keep selection, if possible
        selected_raid = self.raid_chooser.selected
        parents = [chooser.parent for chooser in self.choosers if chooser.selected]
        if parents:  # do not update if there are currently no parents selected
            self.raid_chooser.update(self.device_type, parents)

        try:
            self.raid_chooser.selected = selected_raid
        except ValueError:
            pass

        max_size = self.total_max
        if max_size == size.Size(0):          # just to make Gtk.Scale happy and not set max size < min size
            self.main_chooser.max_size = self.main_chooser.min_size
        else:
            self.main_chooser.max_size = max_size

    def _on_raid_changed(self, *_args):
        """ Raid type selection changed """

        self.raid_type = self.raid_chooser.selected

        # update main chooser max size based on the raid type selected
        self.main_chooser.max_size = self.total_max

    @property
    def total_max(self):
        """ Max size selectable in this area """
        total_max = size.Size(0)

        # for raids, total size must be calculated separately
        if self.raid_type not in ("linear", "single", None):
            raid_level = get_raid_level(self.raid_type)
            total_max = raid_level.get_net_array_size(len([chooser for chooser in self.choosers if chooser.max_size]),
                                                      min([chooser.max_size for chooser in self.choosers if chooser.selected]))
        else:
            for chooser in self.choosers:
                if chooser.selected:
                    total_max += chooser.max_size

        return total_max

    @property
    def total_size(self):
        """ Total size selected in this area """
        total_size = size.Size(0)

        # for raids, total size must be calculated separately
        if self.raid_type not in ("linear", "single", None):
            raid_level = get_raid_level(self.raid_type)
            total_size = raid_level.get_net_array_size(len([chooser for chooser in self.choosers if chooser.selected]),
                                                       min([chooser.selected_size for chooser in self.choosers if chooser.selected]))
        else:
            for chooser in self.choosers:
                total_size += chooser.selected_size

        return total_size

    @total_size.setter
    def total_size(self, new_size):
        if new_size > sum([chooser.max_size for chooser in self.choosers]):
            raise ValueError("New size is bigger than allowed maximum size.")

        # don't update total size for lvs with advanced selection
        if self.device_type in ("lvmlv", "lvmthinpool") and self.status:
            return

        allocated = size.Size(0)
        for chooser in self.choosers:
            if allocated < new_size:
                chooser.selected = True

                if chooser.max_size < (new_size - allocated):
                    chooser.selected_size = chooser.max_size
                    allocated += chooser.max_size
                else:
                    chooser.selected_size = (new_size - allocated)
                    allocated = new_size
            else:
                chooser.selected = False

    def show(self):
        super().show()
        self.status = True

    def hide(self):
        super().hide()
        self.status = False

    def get_selection(self):
        selection = []
        for chooser in self.choosers:
            # for lvs just return total size -- we don't support choosing parent sizes for lvs
            if self.device_type == "lvmlv":
                selected_size = self.main_chooser.selected_size
            else:
                selected_size = chooser.selected_size
            selection.append((chooser.parent, selected_size))

        return selection


class ParentChooser(GUIWidget):

    def __init__(self, parent, show_size, min_size=None, max_size=None):

        GUIWidget.__init__(self, "parent_chooser.ui")

        self.parent = parent
        self.show_size = show_size
        self._max_size = max_size
        self._min_size = min_size
        self._selected_size = max_size

        self._selected = False

        self.parent_toggled_handler = None
        self.size_change_handler = None

        self.grid = self.builder.get_object("grid")

        self.checkbutton_use = self.builder.get_object("checkbutton_use")
        self.checkbutton_use.connect("toggled", self._on_parent_toggled)

        label_device = self.builder.get_object("label_device")
        label_device.set_text(parent.name)

        label_size = self.builder.get_object("label_size")
        label_size.set_text(str(max_size))

        if self.show_size:
            self.size_chooser = SizeChooser(max_size=max_size, min_size=min_size)
            self.size_chooser.connect("size-changed", self._on_size_chooser_changed)
            self.grid.attach(self.size_chooser.grid, 3, 0, 1, 1)
            self.widgets.append(self.size_chooser)

        self.show()

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, status):
        self._selected = status
        self.checkbutton_use.set_active(status)

        # call the signal handler to set the size limits but don't emit the signal
        self._on_parent_toggled(self.checkbutton_use, False)

    @property
    def selectable(self):
        return self.checkbutton_use.get_sensitive()

    @selectable.setter
    def selectable(self, status):
        self.checkbutton_use.set_sensitive(status)

    def _on_parent_toggled(self, checkbutton, emit_signal=True):

        self._selected = checkbutton.get_active()

        if self._selected:
            if self.show_size:
                self.size_chooser.set_sensitive(True)
                self.size_chooser.min_size = self.min_size
            self.selected_size = self.max_size
        else:
            if self.show_size:
                self.size_chooser.set_sensitive(False)
                self.size_chooser.min_size = size.Size(0)
            self.selected_size = size.Size(0)

        # call the signal handler for the parent-toggled event
        if self.parent_toggled_handler is not None and emit_signal:
            self.parent_toggled_handler.method(self._selected, self.parent, *self.parent_toggled_handler.args)

    def _on_size_chooser_changed(self, new_size, *_args):
        if self.show_size and self.selected_size != new_size:
            self.selected_size = new_size

    def connect(self, signal, method, *args):
        """ Connect a signal hadler """

        if signal == "parent-toggled":
            self.parent_toggled_handler = SignalHandler(method=method, args=args)

        elif signal == "size-changed":
            self.size_change_handler = SignalHandler(method=method, args=args)

        else:
            raise TypeError("Unknown signal type %s" % signal)

    @property
    def selected_size(self):
        return self._selected_size

    @selected_size.setter
    def selected_size(self, new_size):
        if self.show_size and self.size_chooser.selected_size != new_size:
            self.size_chooser.selected_size = new_size
        self._selected_size = new_size

        if self.size_change_handler is not None:
            self.size_change_handler.method(new_size, *self.size_change_handler.args)

    @property
    def min_size(self):
        return self._min_size

    @min_size.setter
    def min_size(self, new_size):
        if self.show_size:
            self.size_chooser.min_size = new_size
        self._min_size = new_size

    @property
    def max_size(self):
        return self._max_size

    @max_size.setter
    def max_size(self, new_size):
        if self.show_size:
            self.size_chooser.max_size = new_size
        self._max_size = new_size


class SizeChooser(GUIWidget):

    def __init__(self, max_size, min_size, current_size=None):
        """
            :param max_size: maximum size that user can choose
            :type max_size: blivet.size.Size
            :param min_size: minimum size that user can choose
            :type min_size: blivet.size.Size
            :param current_size: current size of edited device
            :type current_size: blivet.size.Size
        """

        GUIWidget.__init__(self, "size_chooser.ui")

        self._max_size = max_size
        self._min_size = min_size

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
        return size.Size(str(self._scale.get_value()) + " " + size.unit_str(self.selected_unit))

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
                                    "." + str(digits) + "f") + " " + size.unit_str(unit))
        self._scale.add_mark(float(self.max_size.convert_to(unit)), Gtk.PositionType.BOTTOM,
                             format(self.max_size.convert_to(unit),
                                    "." + str(digits) + "f") + " " + size.unit_str(unit))

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

        selected_size = size.Size(str(self._scale.get_value()) + " " + size.unit_str(old_unit))

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

    def get_selection(self):
        """ Get selected size """

        return self.selected_size
