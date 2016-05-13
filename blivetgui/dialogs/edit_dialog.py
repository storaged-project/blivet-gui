# -*- coding: utf-8 -*-
# edit_dialog.py
# Gtk.Dialog for editting devices
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

from blivet.size import Size

from .size_chooser import SizeChooser
from .helpers import supported_filesystems
from ..gui_utils import locate_ui_file
from ..communication.proxy_utils import ProxyDataContainer
from ..i18n import _

# ---------------------------------------------------------------------------- #


class ResizeDialog(object):

    def __init__(self, main_window, resize_device, resize_info):
        self.main_window = main_window
        self.resize_device = resize_device
        self.resize_info = resize_info

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain("blivet-gui")
        self.builder.add_from_file(locate_ui_file("resize_dialog.ui"))

        self.dialog = self.builder.get_object("resize_dialog")
        self.dialog.set_transient_for(self.main_window)

        self.box = self.builder.get_object("box")

        button_cancel = self.builder.get_object("button_cancel")
        button_cancel.connect("clicked", self._on_cancel_button)

        button_resize = self.builder.get_object("button_resize")
        button_resize.connect("clicked", self._on_resize_button)

        if self.resize_info.resizable:
            self.size_chooser = self._add_size_chooser()
        else:
            self._add_resize_info()

    def _add_size_chooser(self):
        size_chooser = SizeChooser(max_size=self.resize_info.max_size,
                                   min_size=self.resize_info.min_size,
                                   current_size=self.resize_device.size)
        self.box.pack_start(child=size_chooser.grid, expand=True, fill=True, padding=0)

        return size_chooser

    def _add_resize_info(self):
        label_info = Gtk.Label()

        if self.resize_info.error:
            label_info.set_markup(_("<b>This device cannot be resized:</b>\n<i>{0}</i>").format(self.resize_info.error))
        else:
            label_info.set_markup("<b>%s</b>" % _("This device cannot be resized."))

        self.box.pack_start(child=label_info, expand=True, fill=True, padding=0)

    def run(self):
        response = self.dialog.run()

        if response == Gtk.ResponseType.REJECT:
            self.dialog.destroy()
            return ProxyDataContainer(edit_device=self.resize_device, resize=False, size=None)
        else:
            selected_size = self.size_chooser.get_selection()
            resize = selected_size != self.resize_device.size
            self.dialog.destroy()
            return ProxyDataContainer(edit_device=self.resize_device, resize=resize, size=selected_size)

    def _on_cancel_button(self, _button):
        self.dialog.response(Gtk.ResponseType.REJECT)

    def _on_resize_button(self, _button):
        self.dialog.response(Gtk.ResponseType.ACCEPT)


class FormatDialog(object):

    def __init__(self, main_window, edit_device):
        self.main_window = main_window
        self.edit_device = edit_device

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain("blivet-gui")
        self.builder.add_from_file(locate_ui_file("format_dialog.ui"))

        self.dialog = self.builder.get_object("format_dialog")
        self.dialog.set_transient_for(self.main_window)

        button_cancel = self.builder.get_object("button_cancel")
        button_cancel.connect("clicked", self._on_cancel_button)

        button_format = self.builder.get_object("button_format")
        button_format.connect("clicked", self._on_format_button)

        self.fs_combo = self.builder.get_object("comboboxtext_format")

        supported_fs = supported_filesystems()
        if self.edit_device.size > Size("8 MiB"):
            supported_fs.append("lvmpv")
        for fs in supported_fs:
            self.fs_combo.append_text(fs)

        if "ext4" in supported_fs:
            self.fs_combo.set_active(supported_fs.index("ext4"))
        else:
            self.fs_combo.set_active(0)

    def run(self):
        response = self.dialog.run()

        if response == Gtk.ResponseType.REJECT:
            self.dialog.destroy()
            return ProxyDataContainer(edit_device=self.edit_device, format=False, filesystem=None)
        else:
            selected_fmt = self.fs_combo.get_active_text()
            if selected_fmt == "unformatted":
                selected_fmt = None
            self.dialog.destroy()
            return ProxyDataContainer(edit_device=self.edit_device, format=True, filesystem=selected_fmt)

    def _on_cancel_button(self, _button):
        self.dialog.response(Gtk.ResponseType.REJECT)

    def _on_format_button(self, _button):
        self.dialog.response(Gtk.ResponseType.ACCEPT)


class LVMEditDialog(Gtk.Dialog):
    """ Dialog window allowing user to edit lvmvg
    """

    def __init__(self, parent_window, edited_device, free_info):
        """

            :param parent_window: parent window
            :type parent_window: Gtk.Window
            :param edited_device: device selected to edit
            :type edited_device: class blivet.Device

        """

        self.edited_device = edited_device
        self.parent_window = parent_window
        self.free_info = free_info

        Gtk.Dialog.__init__(self, _("Edit device"), None, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_transient_for(self.parent_window)
        self.set_resizable(False)  # auto shrink after removing/hiding widgets

        self.widgets_dict = {}

        self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10, column_spacing=5)
        self.grid.set_border_width(10)

        box = self.get_content_area()
        box.add(self.grid)

        self.add_parent_list()
        self.button_add, self.button_remove = self.add_toggle_buttons()

        self.show_all()

        self.add_store = self.add_parents()
        self.remove_store = self.remove_parents()

    def add_parent_list(self):

        parents_store = Gtk.ListStore(str, str, str)

        for parent in self.edited_device.parents:
            parents_store.append([parent.name, "lvmpv", str(parent.size)])

        parents_view = Gtk.TreeView(model=parents_store)
        renderer_text = Gtk.CellRendererText()

        column_name = Gtk.TreeViewColumn(_("Device"), renderer_text, text=0)
        column_type = Gtk.TreeViewColumn(_("Type"), renderer_text, text=1)
        column_size = Gtk.TreeViewColumn(_("Size"), renderer_text, text=2)

        parents_view.append_column(column_name)
        parents_view.append_column(column_type)
        parents_view.append_column(column_size)

        parents_view.set_headers_visible(True)

        label_list = Gtk.Label(label=_("Parent devices:"), xalign=1)
        label_list.get_style_context().add_class("dim-label")

        self.grid.attach(label_list, 0, 1, 1, 1)
        self.grid.attach(parents_view, 1, 1, 3, 3)

    def add_toggle_buttons(self):

        button_add = Gtk.ToggleButton(_("Add parent"))
        self.grid.attach(button_add, 0, 4, 1, 1)

        button_remove = Gtk.ToggleButton(_("Remove parent"))
        self.grid.attach(button_remove, 1, 4, 1, 1)

        button_add.connect("toggled", self.on_button_toggled, "add", button_remove)
        button_remove.connect("toggled", self.on_button_toggled, "remove", button_add)

        return button_add, button_remove

    def add_parents(self):

        if len(self.free_info) == 0:
            label_none = Gtk.Label(label=_("There are currently no empty physical volumes or\n"
                                           "disks with enough free space to create one."))
            self.grid.attach(label_none, 0, 5, 4, 1)

            self.widgets_dict["add"] = [label_none]

            return None

        else:
            parents_store = Gtk.ListStore(object, object, bool, str, str, str)
            parents_view = Gtk.TreeView(model=parents_store)

            renderer_toggle = Gtk.CellRendererToggle()
            renderer_toggle.connect("toggled", self.on_cell_toggled, parents_store)

            renderer_text = Gtk.CellRendererText()

            column_toggle = Gtk.TreeViewColumn("Add?", renderer_toggle, active=2)
            column_name = Gtk.TreeViewColumn(_("Device"), renderer_text, text=3)
            column_type = Gtk.TreeViewColumn(_("Type"), renderer_text, text=4)
            column_size = Gtk.TreeViewColumn(_("Size"), renderer_text, text=5)

            parents_view.append_column(column_toggle)
            parents_view.append_column(column_name)
            parents_view.append_column(column_type)
            parents_view.append_column(column_size)

            parents_view.set_headers_visible(True)

            label_list = Gtk.Label(label=_("Available devices:"), xalign=1)
            label_list.get_style_context().add_class("dim-label")

            self.grid.attach(label_list, 0, 5, 1, 1)
            self.grid.attach(parents_view, 1, 5, 4, 3)

            for ftype, free in self.free_info:
                if ftype == "lvmpv":
                    pv = free.parents[0]
                    parents_store.append([pv, free, False, pv.name, "lvmpv", str(free.size)])
                else:
                    disk = free.parents[0]
                    parents_store.append([disk, free, False, disk.name, "free region", str(free.size)])

            self.widgets_dict["add"] = [label_list, parents_view]

            return parents_store

    def on_cell_toggled(self, _toggle, path, store):
        store[path][2] = not store[path][2]

    def on_cell_radio_toggled(self, _toggle, path, store):
        for row in store:
            row[2] = (row.path == Gtk.TreePath(path))

    def remove_parents(self):

        # get removable pvs
        removable_pvs = [pv for pv in self.edited_device.pvs if (pv.size // self.edited_device.pe_size) <= self.edited_device.free_extents]

        if len(removable_pvs) == 0:
            label_none = Gtk.Label(label=_("There is no physical volume that could be\n"
                                           "removed from this volume group."))
            self.grid.attach(label_none, 0, 5, 4, 1)

            self.widgets_dict["remove"] = [label_none]

            return None

        else:
            parents_store = Gtk.ListStore(object, object, bool, str, str, str)
            parents_view = Gtk.TreeView(model=parents_store)

            parents_view.set_tooltip_text(_("Currently is possible to remove only one parent at time."))

            renderer_radio = Gtk.CellRendererToggle()
            renderer_radio.connect("toggled", self.on_cell_radio_toggled, parents_store)
            renderer_radio.set_radio(True)

            renderer_text = Gtk.CellRendererText()

            column_radio = Gtk.TreeViewColumn("Remove?", renderer_radio, active=2)
            column_name = Gtk.TreeViewColumn(_("Device"), renderer_text, text=3)
            column_type = Gtk.TreeViewColumn(_("Type"), renderer_text, text=4)
            column_size = Gtk.TreeViewColumn(_("Size"), renderer_text, text=5)

            parents_view.append_column(column_radio)
            parents_view.append_column(column_name)
            parents_view.append_column(column_type)
            parents_view.append_column(column_size)

            parents_view.set_headers_visible(True)

            label_list = Gtk.Label(label=_("Available devices:"), xalign=1)
            label_list.get_style_context().add_class("dim-label")

            self.grid.attach(label_list, 0, 5, 1, 1)
            self.grid.attach(parents_view, 1, 5, 4, 3)

            for pv in removable_pvs:
                parents_store.append([pv, None, False, pv.name, "lvmpv", str(pv.size)])

            self.widgets_dict["remove"] = [label_list, parents_view]

            return parents_store

    def on_button_toggled(self, clicked_button, button_type, other_button):

        if clicked_button.get_active():
            other_button.set_active(False)
            self.show_widgets([button_type])

        else:
            self.hide_widgets([button_type])

    def show_widgets(self, widget_types):

        for widget_type in widget_types:
            for widget in self.widgets_dict[widget_type]:
                widget.show()

    def hide_widgets(self, widget_types):

        for widget_type in widget_types:
            for widget in self.widgets_dict[widget_type]:
                widget.hide()

    def get_selection(self):

        parents_list = []

        if self.button_add.get_active():
            action_type = "add"

            if self.add_store:
                for row in self.add_store:
                    if row[2] and row[0].type == "partition":
                        parents_list.append(row[0])

                    if row[2] and row[0].type == "disk":
                        parents_list.append(row[1])

        elif self.button_remove.get_active():
            action_type = "remove"
            if self.remove_store:
                for row in self.remove_store:
                    if row[2]:
                        parents_list.append(row[0])

        else:
            action_type = None

        return ProxyDataContainer(edit_device=self.edited_device,
                                  action_type=action_type,
                                  parents_list=parents_list)
