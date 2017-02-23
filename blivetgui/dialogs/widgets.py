# -*- coding: utf-8 -*-
# widgets.py
# GUI widgets for dialogs (mainly for AddDialog)
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
# ---------------------------------------------------------------------------- #

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk
from contextlib import contextmanager

from blivet.devicelibs.raid import RAID0, Single, Linear

from .helpers import supported_raids
from ..gui_utils import locate_ui_file


class GUIWidget(object):
    """ Helper class for 'composite' widgets for blivet-gui that reads given
        Glade file and implements some usefull Gtk.Widget methods
    """

    name = None
    glade_file = None

    def __init__(self):

        self._builder = Gtk.Builder()
        self._builder.set_translation_domain("blivet-gui")
        self._builder.add_from_file(locate_ui_file(self.glade_file))

        # the glade file has to have either box or grid as a top level widget
        self.box = self._builder.get_object("box") or self._builder.get_object("grid")

        # get list of all 'real' widgets in this widget
        self.widgets = self._builder.get_objects()

    @contextmanager
    def block_handlers(self, widget, handlers):
        for handler_id in handlers:
            widget.handler_block(handler_id)

        yield

        for handler_id in handlers:
            widget.handler_unblock(handler_id)

    def connect(self, signal_name, signal_handler, *args):
        raise NotImplementedError

    def destroy(self):
        """ Destroy this widgets """

        for widget in self.widgets:
            widget.hide()
            widget.destroy()

    def show(self):
        """ Show this widget """

        self.set_visible(True)

    def hide(self):
        """ Hide this widget """

        self.set_visible(False)

    def set_visible(self, visibility):
        """ Hide/show this widget

            :param visibility: visibility
            :type visibility: bool

        """

        for widget in self.widgets:
            if hasattr(widget, "set_visible"):
                # 'non-gui' widgets like treestores are in glade file but don't
                # have visibility, sensitivity etc. methods
                widget.set_visible(visibility)

    def get_visible(self):
        return all([widget.get_visible() for widget in self.widgets if hasattr(widget, "get_visible")])

    def set_sensitive(self, sensitivity):
        """ Set sensitivity for this widget

            :param sensitivity: sensitivity
            :type sensitivity: bool

        """
        for widget in self.widgets:
            if hasattr(widget, "set_sensitive"):
                # 'non-gui' widgets like treestores are in glade file but don't
                # have visibility, sensitivity etc. methods
                widget.set_sensitive(sensitivity)

    def get_sensitive(self):
        return all([widget.get_sensitive() for widget in self.widgets if hasattr(widget, "get_sensitive")])


class RaidChooser(GUIWidget):

    glade_file = "raid_chooser.ui"
    name = "raid chooser"
    supported_signals = ("changed",)

    def __init__(self):

        super().__init__()

        self.supported_raids = supported_raids()

        # temporarily disable LVM RAID
        self.supported_raids["lvmlv"] = [Linear]

        self._combobox_raid = self._builder.get_object("combobox_raid")
        self._liststore_raid = self._builder.get_object("liststore_raid")

        self._handler_ids = []

    @property
    def selected_level(self):
        treeiter = self._combobox_raid.get_active_iter()

        if treeiter:
            return self._liststore_raid[treeiter][1]

    @selected_level.setter
    def selected_level(self, raid_level):
        for idx, raid in enumerate(self._liststore_raid):
            if raid[1] == raid_level:
                self._combobox_raid.set_active(idx)
                return

        # selected raid type not found
        raise ValueError("RAID type %s is not available for selection." % raid_level)

    def connect(self, signal_name, signal_handler, *args):
        if signal_name not in self.supported_signals:
            raise ValueError("Widget %s doesn't support signal %s" % (self.name, signal_name))

        handler_id = self._combobox_raid.connect(signal_name, signal_handler, *args)
        self._handler_ids.append(handler_id)

        return handler_id

    def update(self, device_type, num_parents):
        """ Update list of available raid levels based on currently selected device """

        # block all currently connected signal handlers -- changing the liststore
        # results in emitting 'changed' signal for every added/removed raid level
        with self.block_handlers(self._combobox_raid, self._handler_ids):
            self._liststore_raid.clear()

            try:
                levels = self.supported_raids[device_type]
            except KeyError:
                levels = []

            for raid in levels:
                if num_parents >= raid.min_members:
                    self._liststore_raid.append((raid.name, raid))

        if len(self._liststore_raid) == 0:
            self.set_visible(False)
            self.set_sensitive(False)
        elif len(self._liststore_raid) > 1:
            self.set_visible(True)
            self.set_sensitive(True)
        else:
            self.set_visible(True)
            self.set_sensitive(False)

    def autoselect(self, device_type):
        """ Automatically select some 'sane' level for given device type """

        if device_type == "lvmlv":
            default_level = Linear
        elif device_type == "btrfs volume":
            default_level = Single
        elif device_type == "mdraid":
            default_level = RAID0
        else:
            default_level = None

        try:
            self.selected_level = default_level
        except ValueError:
            # default level not supported so just select first one in the list
            treeiter = self._liststore_raid.get_iter_first()

            if treeiter:
                self._combobox_raid.set_active_iter(treeiter)
