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
from blivet.devicelibs.raid import Single, Linear

from .widgets import GUIWidget, SignalHandler
from ..i18n import _
from ..communication.proxy_utils import ProxyDataContainer

from collections import OrderedDict

# ---------------------------------------------------------------------------- #

UNITS = OrderedDict([("B", size.B), ("KB", size.KB), ("MB", size.MB),
                     ("GB", size.GB), ("TB", size.TB), ("KiB", size.KiB),
                     ("MiB", size.MiB), ("GiB", size.GiB), ("TiB", size.TiB)])
# ---------------------------------------------------------------------------- #


class SizeSelection(ProxyDataContainer):

    def __init__(self, total_size, parents):
        super().__init__(total_size=total_size, parents=parents)


class ParentSelection(ProxyDataContainer):

    def __init__(self, parent_device, free_space, selected_size):
        super().__init__(parent_device=parent_device,
                         free_space=free_space,
                         selected_size=selected_size)

# ---------------------------------------------------------------------------- #


class SizeArea(GUIWidget):

    name = "size area"
    glade_file = "size_area.ui"

    def __init__(self, device_type, parents, min_limit, max_limit, raid_type):
        """
            :param device_type: type of device we are creating
            :param parents: list of available/selected parents
            :param min_limit: minimal size limit for new device based on currently
                              selected options (e.g. filesystem type)
            :param max_limit: maximum size limit for new device based on currently
                              selected options (e.g. filesystem type)
            :param raid_type: currently selected raid level
        """

        super().__init__()

        self.device_type = device_type
        self.parents = parents
        self.raid_type = raid_type

        self._parent_area = None

        self.frame = self._builder.get_object("frame_size")
        self.grid = self._builder.get_object("grid")

        self._min_size_limit = min_limit
        self._max_size_limit = max_limit

        # "main" size chooser
        self.main_chooser = SizeChooser(max_size=self.max_size, min_size=self.min_size)
        self.grid.attach(self.main_chooser.grid, 0, 0, 5, 1)

        size_allowed = self._allow_size_selection()
        self.main_chooser.set_sensitive(size_allowed)

        self.main_chooser.selected_size = self.max_size

        # checkbutton for advanced/manual parent selection
        checkbutton_manual = self._builder.get_object("checkbutton_manual")
        checkbutton_manual.connect("toggled", self._on_manual_toggled)
        self.widgets.remove(checkbutton_manual)

        advanced_allowed = self._allow_advanced_configuration()
        if advanced_allowed:
            checkbutton_manual.set_sensitive(True)
        else:
            checkbutton_manual.set_sensitive(False)

        advanced_enforced = self._enforce_advanced_configuration()
        if advanced_enforced:
            checkbutton_manual.set_active(True)
            checkbutton_manual.set_sensitive(False)
        else:
            checkbutton_manual.set_active(False)

    # PROPERTIES
    @property
    def min_size(self):
        """ Minimal size selectable in this area. Depends on currently available
            parents, raid level and limits for the newly created device
        """
        if self._parent_area is None:
            return max(sum((parent.min_size + parent.reserved_size) for parent in self.parents),
                       self.min_size_limit)
        else:
            return self._parent_area.total_min

    @property
    def min_size_limit(self):
        """ Limit for minimal size based on 'other' limits, e.g. limits for
            selected filesystem, device type etc.
        """
        return self._min_size_limit

    @min_size_limit.setter
    def min_size_limit(self, new_size):
        if new_size <= 0:
            raise ValueError("Size limit must be greater than zero.")

        if new_size > self.max_size:
            raise ValueError("Size limit for minimal size cannot be greater than current maximum size.")

        self._min_size_limit = new_size

        # set min size for the chooser
        # (if parent area exists, it takes care of main chooser)
        if self._parent_area is None:
            self.main_chooser.min_size = self.min_size

    @property
    def max_size(self):
        """ Max size selectable in this area. Depends on currently available
            parents, raid level and limits for the newly created device
        """
        if self._parent_area is None:
            return min(sum(parent.max_size for parent in self.parents), self.max_size_limit)
        else:
            return self._parent_area.total_max

    @property
    def max_size_limit(self):
        """ Limit for maximum size based on 'other' limits, e.g. limits for
            selected filesystem, device type etc.
        """
        return self._max_size_limit

    @max_size_limit.setter
    def max_size_limit(self, new_size):
        if new_size <= 0:
            raise ValueError("Size limit must be greater than zero.")

        if new_size < self.min_size:
            raise ValueError("Size limit for maximum size cannot be smaller than current minimum size.")

        self._max_size_limit = new_size

        # set min size for the chooser
        # (if parent area exists, it takes care of main chooser)
        if self._parent_area is None:
            self.main_chooser.max_size = self.max_size

    def set_size_limits(self, min_size_limit, max_size_limit):
        """ Set both size limits at once avoiding issues with new size limits being outside of
            existing limits. E.g. when changing limits from (1 MiB, 2 MiB) to (256 MiB, 1 GiB)
            changing the min limit will fail because it is greater than existing max limit.
        """

        if min_size_limit > self.max_size:
            self.max_size_limit = max_size_limit
            self.min_size_limit = min_size_limit
        elif max_size_limit < self.min_size:
            self.min_size_limit = min_size_limit
            self.max_size_limit = max_size_limit
        else:
            self.max_size_limit = max_size_limit
            self.min_size_limit = min_size_limit

    # PUBLIC METHODS
    def connect(self, signal_name, signal_handler, *args):  # pylint: disable=unused-argument
        """ Connect a signal handler """

        raise TypeError("Unknown signal type '%s' for widget %s" % (signal_name, self.name))

    def validate_user_input(self):
        selection = self.get_selection()

        if selection.total_size > self.max_size_limit:
            msg = _("Currently selected size is greater than maximum limit for this selection.")
            return (False, msg)
        if selection.total_size < self.min_size_limit:
            msg = _("Currently selected size is smaller than minimum limit for this selection.")
            return (False, msg)
        else:
            return (True, None)

    def get_selection(self):
        """ Get user selection. Consist of total size selected ('usable' size
            for the newly created device) and list of parents with sizes for
            them (either specified by user or just fraction of total size)
        """
        if self._parent_area is None:
            # no advanced selection -> we will use all available parents and set
            # same size for each of them and return total selected size
            total_size = self.main_chooser.selected_size
            parents = self._get_parents_allocation()
            return SizeSelection(total_size=total_size, parents=parents)
        else:
            # selection is handled by the parent area
            return self._parent_area.get_selection()

    def set_parents_min_size(self, new_size):
        """ Set (same) min size for all parents """

        # update parents
        for parent in self.parents:
            parent.min_size = new_size

        if self._parent_area is None:
            self.main_chooser.min_size = self.min_size
        else:
            self._parent_area.set_choosers_min_size(new_size)

    def set_parents_reserved_size(self, reserved_size):
        """ Set (same) reserved size for all parents """

        # update parents
        for parent in self.parents:
            parent.reserved_size = reserved_size

        if self._parent_area is None:
            self.main_chooser.min_size = self.min_size
        else:
            self._parent_area.set_choosers_reserved_size(reserved_size)

    # PRIVATE METHODS
    def _allow_size_selection(self):
        return self.device_type not in ("lvmvg", "lvm thinsnapshot")

    def _allow_advanced_configuration(self):
        # manual configuration of parents is allowed only for devices with multiple
        # parents but not for thinpools, lvm snapshots and linear LVs
        if self.parents and len(self.parents) > 1:
            if self.device_type in ("lvmthinpool", "lvm snapshot"):
                return False
            elif self.device_type == "lvmlv" and self.raid_type in (Linear, None):
                return False
            else:
                return True
        else:
            return False

    def _enforce_advanced_configuration(self):
        # always show if raid level is selected
        return self.raid_type not in (Linear, Single, None)

    def _add_advanced_area(self):
        self._parent_area = ParentArea(self.device_type, self.parents, self.raid_type, self.main_chooser)
        self.grid.attach(self._parent_area.frame, 0, 2, 5, 1)
        self.widgets.append(self._parent_area)

        self.main_chooser.set_sensitive(False)

    def _remove_advanced_area(self):
        self._parent_area.destroy()
        self.widgets.remove(self._parent_area)
        self._parent_area = None

        self.main_chooser.set_sensitive(True)

    def _get_parents_allocation(self):
        """ Without advanced area we need to choose how much space to use on
            each parent
        """
        total_size = self.main_chooser.selected_size
        res = []

        unallocated_parents = self.parents[:]
        allocated_size = size.Size(0)
        while allocated_size < total_size:
            smallest_parent = min([p for p in unallocated_parents], key=lambda x: x.max_size)
            if (smallest_parent.max_size * len(unallocated_parents)) >= (total_size - allocated_size):
                # just put remaining size / number of remaining parents to each parent
                for parent in unallocated_parents:
                    res.append(ParentSelection(parent_device=parent.device,
                                               free_space=parent.free_space,
                                               selected_size=(total_size - allocated_size) // len(unallocated_parents)))
                    allocated_size += ((total_size - allocated_size) // len(unallocated_parents))
                    unallocated_parents.remove(parent)
            else:
                # use entire smallest remaining parent
                res.append(ParentSelection(parent_device=smallest_parent.device,
                                           free_space=smallest_parent.free_space,
                                           selected_size=smallest_parent.max_size))
                allocated_size += smallest_parent.max_size
                unallocated_parents.remove(smallest_parent)

        return res

    # SIGNAL HANDLERS
    def _on_manual_toggled(self, checkbutton):
        """ Advanced selection toggled """

        if checkbutton.get_active():
            self._add_advanced_area()
        else:
            self._remove_advanced_area()


class ParentArea(GUIWidget):
    """ Widget for advanced/manual configuration of parents. ParentArea shows all
        available parents and allows user to select size for them.
    """

    name = "parent area"
    glade_file = "parent_area.ui"

    def __init__(self, device_type, parents, raid_type, main_chooser):

        super().__init__()

        self.device_type = device_type
        self.parents = parents
        self.raid_type = raid_type
        self.main_chooser = main_chooser

        self.choosers = []  # parent choosers in this area
        self._size_change_handlers = []

        self.frame = self._builder.get_object("frame")
        self.grid = self._builder.get_object("grid")

        self._add_parent_choosers()
        self._update_main_chooser()

        self.show()

    # PROPERTIES
    @property
    def selected_choosers(self):
        return [chooser for chooser in self.choosers if chooser.selected]

    @property
    def total_max(self):
        """ Max size selectable in this area """
        total_max = size.Size(0)

        # for raids, total max size must be calculated separately
        if self.raid_type not in (Linear, Single, None):
            total_max = self.raid_type.get_net_array_size(len(self.selected_choosers),
                                                          min([ch.max_size for ch in self.selected_choosers]))
        else:
            for chooser in self.choosers:
                if chooser.selected:
                    total_max += chooser.max_size

        return total_max

    @property
    def total_min(self):
        """ Min size selectable in this area """
        total_min = size.Size(0)

        # for raids, total min size must be calculated separately
        if self.raid_type not in (Linear, Single, None):
            total_min = self.raid_type.get_net_array_size(len(self.selected_choosers),
                                                          min([ch.min_size for ch in self.selected_choosers]))
        else:
            for chooser in self.choosers:
                if chooser.selected:
                    total_min += chooser.min_size

        return total_min

    @property
    def total_size(self):
        """ Total size selected in this area """

        total_size = size.Size(0)

        # for raids, total size must be calculated separately
        if self.raid_type not in (Linear, Single, None):
            total_size = self.raid_type.get_net_array_size(len(self.selected_choosers),
                                                           min([ch.selected_size for ch in self.selected_choosers]))
        else:
            for chooser in self.choosers:
                total_size += chooser.selected_size

        return total_size

    # PUBLIC METHODS
    def connect(self, signal_name, signal_handler, *args):  # pylint: disable=unused-argument
        """ Connect a signal handler """

        raise TypeError("Unknown signal type '%s' for widget %s" % (signal_name, self.name))

    def get_selection(self):
        parents = []
        for chooser in self.choosers:
            if chooser.selected:
                parents.append(ParentSelection(parent_device=chooser.parent,
                                               free_space=chooser.free_space,
                                               selected_size=chooser.selected_size))

        return SizeSelection(total_size=self.total_size, parents=parents)

    def set_choosers_min_size(self, new_size):
        """ Set (same) new size for all choosers in this area """

        for chooser in self.choosers:
            chooser.min_size = new_size
        self._update_main_chooser()

    def set_choosers_reserved_size(self, new_size):
        """ Set (same) new size for all choosers in this area """

        for chooser in self.choosers:
            chooser.reserved_size = new_size
        self._update_main_chooser()

    # PRIVATE METHODS
    def _allow_select_chooser(self, chooser):
        # parents are selectable only for LVs
        if self.device_type != "lvmlv":
            return False

        # we need more parents than current raid level requires
        if len(self.parents) <= self.raid_type.min_members:
            return False

        # and we need to have selected more parents than current raid level requires
        # but in this case always allow to select currently unselected choosers
        if len(self.selected_choosers) <= self.raid_type.min_members:
            if chooser.selected:
                return False
            else:
                return True

        # return True and hope for the best
        return True

    def _add_parent_choosers(self):
        for idx, parent in enumerate(self.parents):
            # with raid selected, all parents have to has the same size (and max size)
            if self.raid_type not in (Linear, Single, None):
                max_size = min([parent.max_size for parent in self.parents])
            else:
                max_size = parent.max_size

            # parents are selectable only for LVs (if there are more than current
            # raid level requires), for other device types parents
            # are selected from parent list in AddDialog itself
            parent_selectable = self.device_type == "lvmlv" and len(self.parents) >= self.raid_type.min_members

            # size is selectable for all parents except for PVs
            size_selectable = parent.device.format.type != "lvmpv"

            chooser = ParentChooser(parent=parent.device, free_space=parent.free_space,
                                    min_size=parent.min_size, max_size=max_size,
                                    reserved_size=parent.reserved_size,
                                    selected=True, parent_selectable=parent_selectable,
                                    size_selectable=size_selectable)

            # signal handlers
            chooser.connect("size-changed", self._on_parent_size_changed, chooser)
            chooser.connect("parent-toggled", self._on_parent_toggled, chooser)

            self.choosers.append(chooser)
            self.widgets.append(chooser)
            self.grid.attach(chooser.grid, 0, idx + 1, 1, 1)

    def _update_main_chooser(self):
        self.main_chooser.max_size = self.total_max
        self.main_chooser.min_size = self.total_min
        self.main_chooser.selected_size = self.total_size

    def _set_choosers_size(self, new_size):
        """ Set new size (same) for all choosers """

        for chooser in self.choosers:
            if chooser.selected_size != new_size:
                chooser.selected_size = new_size

    # SIGNAL HANDLERS
    def _on_parent_size_changed(self, new_size, chooser, *_args):
        """ Parent selection changed -- either size or parent toggled """

        # chooser was deselected -- this also changes selected size to 0, but we
        # don't want to handle this "size change"
        if not chooser.selected:
            return

        # raid -- all parents have to has the same size
        if self.raid_type not in (Linear, Single, None):
            self._set_choosers_size(new_size)

        # update main chooser with news min/max/selected size
        self._update_main_chooser()

    def _on_parent_toggled(self, _selected, chooser, *_args):
        """ Parent selection changed """

        # adjust selectability of other choosers based on current selection
        # (e.g. we don't want to allow deselecting more choosers than need
        # by selected raid level)
        for ch in self.choosers:
            if ch == chooser:
                continue
            ch.parent_selectable = self._allow_select_chooser(ch)

        # update main chooser with news min/max/selected size
        self._update_main_chooser()


class ParentChooser(GUIWidget):
    """ Widget that represents one 'parent' device in ParentArea. It allows to
        set size for selected parent and (in some cases) to select or deselect
        that parent device.
    """

    name = "parent chooser"
    glade_file = "parent_chooser.ui"

    def __init__(self, parent, free_space, min_size, max_size, reserved_size, selected, parent_selectable, size_selectable):

        super().__init__()

        self.parent = parent
        self.free_space = free_space
        self._max_size = max_size
        self._min_size = min_size
        self._reserved_size = reserved_size
        self._selected = selected

        self._parent_toggled_handlers = []
        self._size_change_handlers = []

        self.grid = self._builder.get_object("grid")

        self.checkbutton_use = self._builder.get_object("checkbutton_use")
        self.checkbutton_use.connect("toggled", self._on_parent_toggled)

        # set labels with names of the device and its maximum size
        label_device = self._builder.get_object("label_device")
        label_device.set_text(self.parent.name)
        label_size = self._builder.get_object("label_size")
        label_size.set_text(str(max_size))

        # add SizeChooser
        self.size_chooser = SizeChooser(max_size=max_size, min_size=min_size)
        self.grid.attach(self.size_chooser.grid, 3, 0, 1, 1)
        self.widgets.append(self.size_chooser)

        # now set the initial state of this ParentChooser
        self.selected = selected
        self.selected_size = max_size

        if not parent_selectable:
            self.checkbutton_use.set_sensitive(False)
        if not size_selectable:
            self.size_chooser.set_sensitive(False)

        self.show()

    # PROPERTIES
    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, status):
        self._selected = status

        # mark the button as (not) selected
        if self.checkbutton_use.get_active() != status:
            self.checkbutton_use.set_active(status)

        if status:
            self.size_chooser.set_sensitive(True)
            self.size_chooser.min_size = self.min_size
            self.selected_size = self.max_size
        else:
            self.size_chooser.set_sensitive(False)
            self.size_chooser.min_size = size.Size(0)
            self.selected_size = size.Size(0)

    @property
    def selected_size(self):
        return self.size_chooser.selected_size

    @selected_size.setter
    def selected_size(self, new_size):
        if self.size_chooser.selected_size == new_size:
            return

        self.size_chooser.selected_size = new_size

    @property
    def min_size(self):
        return (self._min_size + self._reserved_size)

    @min_size.setter
    def min_size(self, new_size):
        self._min_size = new_size
        self.size_chooser.min_size = self.min_size

    @property
    def max_size(self):
        return self._max_size

    @max_size.setter
    def max_size(self, new_size):
        self._max_size = new_size
        self.size_chooser.max_size = new_size

    @property
    def reserved_size(self):
        return self._reserved_size

    @reserved_size.setter
    def reserved_size(self, new_size):
        self._reserved_size = new_size

        # update the size chooser to reflect updated min size
        self.size_chooser.min_size = self.min_size

    # PUBLIC METHODS
    def connect(self, signal_name, signal_handler, *args):
        """ Connect a signal handler """

        if signal_name == "parent-toggled":
            self._parent_toggled_handlers.append(SignalHandler(method=signal_handler, args=args))
        elif signal_name == "size-changed":
            # just connect this directly to the size_chooser
            self.size_chooser.connect("size-changed", signal_handler, *args)
        else:
            raise TypeError("Unknown signal type '%s' for widget %s" % (signal_name, self.name))

    # SIGNAL HANDLERS
    def _on_parent_toggled(self, checkbutton):
        # set the button to be (not) selected
        # and set sensitivity and selection of the size chooser accordingly
        self.selected = checkbutton.get_active()

        # call the signal handler for the parent-toggled event
        for handler in self._parent_toggled_handlers:
            handler.method(self._selected, *handler.args)


class SizeChooser(GUIWidget):
    """ Widget for size configuration. Consist of Gtk.Scale and Gtk.SpinButton
        for size selection and Gtk.ComboBox for unit selection.
    """

    name = "size chooser"
    glade_file = "size_chooser.ui"

    def __init__(self, max_size, min_size, current_size=None):
        """
            :param max_size: maximum size that user can choose
            :type max_size: blivet.size.Size
            :param min_size: minimum size that user can choose
            :type min_size: blivet.size.Size
            :param current_size: current size of edited device
            :type current_size: blivet.size.Size
        """

        super().__init__()

        self._max_size = max_size
        self._min_size = min_size

        self.grid = self._builder.get_object("grid")

        self.selected_unit = self.default_unit
        self._size_change_handlers = []
        self._unit_change_handlers = []

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
        # XXX: block signals here?
        if selected_size > self.max_size or selected_size < self.min_size:
            raise ValueError("New size must be between minimal (%s) and maximum (%s) size." % (self.min_size, self.max_size))

        self._scale.set_value(selected_size.convert_to(self.selected_unit))

    @property
    def max_size(self):
        return self._max_size

    @max_size.setter
    def max_size(self, max_size):
        if max_size < 0:
            raise ValueError("New maximum size cannot be negative.")
        if max_size < self.min_size:
            raise ValueError("New maximum size cannot be smaller than current minimal size.")

        if max_size == self._max_size:
            return

        self._max_size = max_size
        self._reset_size_widgets(self.selected_size)

    @property
    def min_size(self):
        return self._min_size

    @min_size.setter
    def min_size(self, min_size):
        if min_size < 0:
            raise ValueError("New minimal size cannot be negative.")
        if min_size > self.max_size:
            raise ValueError("New minimal size cannot be bigger than current maximum size.")

        if min_size == self._min_size:
            return

        self._min_size = min_size
        self._reset_size_widgets(self.selected_size)

    @property
    def available_units(self):
        """ Units that should be available to select in this chooser --
            depends on size of the device, e.g. TiB will be available only
            for devices bigger than 2 TiB
        """
        units = []
        dev_size = (self.max_size - self.min_size) or self.max_size

        if dev_size < size.Size("2 B"):
            return [size.B]

        for unit in UNITS.keys():
            if size.Size("2 " + unit) <= dev_size:
                units.append(UNITS[unit])

        return units

    @property
    def default_unit(self):
        """ Default, preselected unit -- GiB for devices larger that 5 GiB,
            otherwise the biggest available unit
        """
        dev_size = self.max_size - self.min_size
        if dev_size >= size.Size("5 GiB"):
            return size.GiB
        elif dev_size >= size.Size("5 MiB"):
            return size.MiB
        else:
            return self.available_units[-1]

    def connect(self, signal_name, signal_handler, *args):
        """ Connect a signal handler """

        if signal_name == "size-changed":
            self._size_change_handlers.append(SignalHandler(method=signal_handler, args=args))

        elif signal_name == "unit-changed":
            self._unit_change_handlers.append(SignalHandler(method=signal_handler, args=args))

        else:
            raise ValueError("Unknown signal type %s" % signal_name)

    def _scale_precision(self, unit):
        """ Get number of decimal places to be displayed for selected unit
            and step for the scale.
            We should allow one decimal place for GB and bigger (step 0.1)
            and no decimal values for MiB and smaller (step 1).

            :param unit: selected size unit
            :type unit: size unit constant (e.g. blivet.size.KiB)
        """

        if size.Size("1 " + size.unit_str(unit)) >= size.Size("1 GB"):
            return (1, 0.1)
        else:
            return (0, 1)

    def _set_size_widgets(self):
        """ Configure size widgets (Gtk.Scale, Gtk.SpinButton) """

        scale = self._builder.get_object("scale_size")
        spin = self._builder.get_object("spinbutton_size")

        default_unit = self.default_unit

        adjustment = Gtk.Adjustment(value=0,
                                    lower=self.min_size.convert_to(default_unit),
                                    upper=self.max_size.convert_to(default_unit),
                                    step_increment=1,
                                    page_increment=10,
                                    page_size=0)

        scale.set_adjustment(adjustment)
        spin.set_adjustment(adjustment)

        digits, increment = self._scale_precision(default_unit)
        scale.set_increments(increment, increment * 10)
        scale.set_digits(digits)

        spin.set_increments(increment, increment * 10)
        spin.set_digits(digits)

        scale.add_mark(self.min_size.convert_to(default_unit),
                       Gtk.PositionType.BOTTOM, str(self.min_size))
        scale.add_mark(self.max_size.convert_to(default_unit),
                       Gtk.PositionType.BOTTOM, str(self.max_size))

        combobox_size = self._builder.get_object("combobox_size")
        for unit in self.available_units:
            combobox_size.append_text(size.unit_str(unit))

        # set default unit
        self.selected_unit = default_unit
        combobox_size.set_active(self.available_units.index(default_unit))

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

        digits, increment = self._scale_precision(unit)
        self._scale.set_increments(increment, increment * 10)
        self._scale.set_digits(digits)

        self._scale.add_mark(self.min_size.convert_to(unit),
                             Gtk.PositionType.BOTTOM, str(self.min_size))
        self._scale.add_mark(self.max_size.convert_to(unit),
                             Gtk.PositionType.BOTTOM, str(self.max_size))

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

        for handler in self._unit_change_handlers:
            handler.method(self.selected_unit, *handler.args)

    def _on_scale_moved(self, scale, spin):
        """ On-change action for size scale """

        spin.set_value(scale.get_value())

        for handler in self._size_change_handlers:
            handler.method(self.selected_size, *handler.args)

    def _on_spin_moved(self, spin, scale):
        """ On-change action for size spin """

        scale.set_value(spin.get_value())

    def get_selection(self):
        """ Get selected size """

        return self.selected_size
