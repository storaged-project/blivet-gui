# -*- coding: utf-8 -*-
# edit_dialog.py
# Gtk.Dialog for editing devices
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

from .size_chooser import SizeChooser
from .helpers import is_mountpoint_valid, is_label_valid
from ..dialogs import message_dialogs
from ..gui_utils import locate_ui_file
from ..communication.proxy_utils import ProxyDataContainer
from ..i18n import _
from ..config import config

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

        self.size_chooser = None

        if self.resize_info.resizable:
            self.size_chooser = self._add_size_chooser()
        else:
            self._add_resize_info()
            button_resize.hide()

    def set_decorated(self, decorated):
        self.dialog.set_decorated(decorated)

        # no decoration --> display dialog title in the dialog
        if not decorated:
            label = self.builder.get_object("label_title")
            title = self.dialog.get_title()
            label.set_text(title)

    def _add_size_chooser(self):
        # blivet is very conservative with min size calculations for some devices
        # (especially partitions) so it is possible to have a device that is
        # bigger or smaller than blivet thinks is possible so we need to "adjust"
        # the current size to display it in the dialog
        if self.resize_device.size < self.resize_info.min_size:
            current_size = self.resize_info.min_size
        elif self.resize_device.size > self.resize_info.max_size:
            current_size = self.resize_info.max_size
        else:
            current_size = self.resize_device.size

        size_chooser = SizeChooser(max_size=self.resize_info.max_size,
                                   min_size=self.resize_info.min_size,
                                   current_size=current_size)
        self.box.pack_start(child=size_chooser.grid, expand=True, fill=True, padding=0)

        return size_chooser

    def _add_resize_info(self):
        label_info = Gtk.Label()

        if self.resize_info.error:
            label_info.set_markup(_("<b>This device cannot be resized:</b>\n<i>{0}</i>").format(self.resize_info.error))
        else:
            label_info.set_markup("<b>%s</b>" % _("This device cannot be resized."))

        self.box.pack_start(child=label_info, expand=True, fill=True, padding=0)
        label_info.show()

    def run(self):
        response = self.dialog.run()

        if response == Gtk.ResponseType.ACCEPT:
            # size_chooser is None --> resizing is not allowed and error was displayed
            if self.size_chooser is None:
                self.dialog.destroy()
                return ProxyDataContainer(edit_device=self.resize_device, resize=False, size=None)

            selected_size = self.size_chooser.get_selection()
            resize = selected_size != self.resize_device.size
            self.dialog.destroy()
            return ProxyDataContainer(edit_device=self.resize_device, resize=resize, size=selected_size)
        else:
            self.dialog.destroy()
            return ProxyDataContainer(edit_device=self.resize_device, resize=False, size=None)

    def _on_cancel_button(self, _button):
        self.dialog.response(Gtk.ResponseType.REJECT)

    def _on_resize_button(self, _button):
        self.dialog.response(Gtk.ResponseType.ACCEPT)


class FormatDialog(object):

    def __init__(self, main_window, edit_device, supported_filesystems,
                 mountpoints=None, installer_mode=False):
        self.main_window = main_window
        self.edit_device = edit_device
        self.supported_filesystems = supported_filesystems
        self.mountpoints = mountpoints
        self.installer_mode = installer_mode

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain("blivet-gui")
        self.builder.add_from_file(locate_ui_file("format_dialog.ui"))

        self.dialog = self.builder.get_object("format_dialog")
        self.dialog.set_transient_for(self.main_window)

        button_cancel = self.builder.get_object("button_cancel")
        button_cancel.connect("clicked", self._on_cancel_button)

        button_format = self.builder.get_object("button_format")
        button_format.connect("clicked", self._on_format_button)

        self.fs_combo = self.builder.get_object("combobox_format")
        self.fs_store = self.builder.get_object("liststore_format")
        self.label_entry = self.builder.get_object("entry_label")
        self.mnt_entry = self.builder.get_object("entry_mountpoint")

        for fs in self.supported_filesystems:
            if self._allow_format_size(fs):
                self.fs_store.append((fs, fs.type, fs.name))
        self.fs_store.append((None, "unformatted", _("unformatted")))

        # set the 'changed' signal after adding supported formats to avoid
        # triggering it for every format
        self.fs_combo.connect("changed", self._on_fs_combo_changed)

        if config.default_fstype in (fs.type for fs in self.supported_filesystems):
            self.fs_combo.set_active_id(config.default_fstype)
        else:
            self.fs_combo.set_active(0)

        # select previously selected mountpoint
        if self._current_mountpoint:
            self.mnt_entry.set_text(self._current_mountpoint)

        self.dialog.show_all()

        if not self.installer_mode:
            self.mnt_box = self.builder.get_object("box_mountpoint")
            self.mnt_box.hide()

    @property
    def _current_mountpoint(self):
        if self.edit_device.format.mountable:
            return self.edit_device.format.mountpoint
        else:
            return None

    def set_decorated(self, decorated):
        self.dialog.set_decorated(decorated)

        # no decoration --> display dialog title in the dialog
        if not decorated:
            label = self.builder.get_object("label_title")
            title = self.dialog.get_title()
            label.set_text(title)

    @property
    def selected_fs(self):
        tree_iter = self.fs_combo.get_active_iter()

        if tree_iter:
            model = self.fs_combo.get_model()
            fs_obj = model[tree_iter][0]
            return fs_obj

    def get_selection(self):
        if self.selected_fs is None:
            selected_fs = None
            selected_label = None
        else:
            selected_fs = self.selected_fs.type
            selected_label = self.label_entry.get_text() or None

        if self.installer_mode:
            selected_mnt = self.mnt_entry.get_text()
        else:
            selected_mnt = None

        return (selected_fs, selected_label, selected_mnt)

    def validate_user_input(self):
        selected_fs, selected_label, selected_mnt = self.get_selection()

        if selected_label:
            valid = is_label_valid(selected_fs, selected_label)
            if not valid:
                msg = _("\"{0}\" is not a valid label.").format(selected_label)
                message_dialogs.ErrorDialog(self.dialog, msg,
                                            not self.installer_mode)  # do not show decoration in installer mode
                return False

        if self.installer_mode and selected_mnt:
            valid, msg = is_mountpoint_valid(self.mountpoints, selected_mnt, self._current_mountpoint)
            if not valid:
                message_dialogs.ErrorDialog(self.dialog, msg,
                                            not self.installer_mode)  # do not show decoration in installer mode
                return False

        return True

    def run(self):
        response = self.dialog.run()

        if response == Gtk.ResponseType.ACCEPT:
            if not self.validate_user_input():
                return self.run()

            selected_fs, selected_label, selected_mnt = self.get_selection()
            self.dialog.destroy()
            return ProxyDataContainer(edit_device=self.edit_device, format=True,
                                      filesystem=selected_fs, label=selected_label,
                                      mountpoint=selected_mnt)
        else:
            self.dialog.destroy()
            return ProxyDataContainer(edit_device=self.edit_device, format=False,
                                      filesystem=None, label=None, mountpoint=None)

    def _allow_format_size(self, fs):
        if fs.max_size and self.edit_device.size > fs.max_size:
            return False

        if fs.min_size and self.edit_device.size < fs.min_size:
            return False

        return True

    def _on_fs_combo_changed(self, _widget):
        # mountpoint entry sensitivity
        if self.selected_fs is None or not self.selected_fs.mountable:
            self.mnt_entry.set_sensitive(False)
            self.mnt_entry.set_text("")
        else:
            self.mnt_entry.set_sensitive(True)

        # label entry sensitivity
        if self.selected_fs is None or not self.selected_fs.labeling():
            self.label_entry.set_sensitive(False)
            self.label_entry.set_text("")
        else:
            self.label_entry.set_sensitive(True)

    def _on_cancel_button(self, _button):
        self.dialog.response(Gtk.ResponseType.REJECT)

    def _on_format_button(self, _button):
        self.dialog.response(Gtk.ResponseType.ACCEPT)


class MountpointDialog(object):

    def __init__(self, main_window, edit_device, mountpoints=None, installer_mode=False):
        self.main_window = main_window
        self.edit_device = edit_device
        self.mountpoints = mountpoints
        self.installer_mode = installer_mode

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain("blivet-gui")
        self.builder.add_from_file(locate_ui_file("mountpoint_dialog.ui"))

        self.dialog = self.builder.get_object("mountpoint_dialog")
        self.dialog.set_transient_for(self.main_window)

        button_cancel = self.builder.get_object("button_cancel")
        button_cancel.connect("clicked", self._on_cancel_button)

        button_set = self.builder.get_object("button_set")
        button_set.connect("clicked", self._on_set_button)

        self.mnt_entry = self.builder.get_object("entry_mountpoint")

        # select previously selected mountpoint
        if self._current_mountpoint:
            self.mnt_entry.set_text(self._current_mountpoint)

        self.dialog.show_all()

    @property
    def _current_mountpoint(self):
        if self.edit_device.format.mountable:
            return self.edit_device.format.mountpoint
        else:
            return None

    def set_decorated(self, decorated):
        self.dialog.set_decorated(decorated)

        # no decoration --> display dialog title in the dialog
        if not decorated:
            label = self.builder.get_object("label_title")
            title = self.dialog.get_title()
            label.set_text(title)

    def validate_user_input(self):
        selected_mnt = self.mnt_entry.get_text()

        if self.installer_mode and selected_mnt:
            valid, msg = is_mountpoint_valid(self.mountpoints, selected_mnt, self._current_mountpoint)
            if not valid:
                message_dialogs.ErrorDialog(self.dialog, msg,
                                            not self.installer_mode)  # do not show decoration in installer mode
                return False

        return True

    def run(self):
        response = self.dialog.run()

        if response == Gtk.ResponseType.ACCEPT:
            if not self.validate_user_input():
                return self.run()

            selected_mnt = self.mnt_entry.get_text()
            self.dialog.destroy()
            return ProxyDataContainer(edit_device=self.edit_device, do_set=True,
                                      mountpoint=selected_mnt)
        else:
            self.dialog.destroy()
            return ProxyDataContainer(edit_device=self.edit_device, do_set=False,
                                      mountpoint=None)

    def _on_cancel_button(self, _button):
        self.dialog.response(Gtk.ResponseType.REJECT)

    def _on_set_button(self, _button):
        self.dialog.response(Gtk.ResponseType.ACCEPT)


class LabelDialog(object):

    def __init__(self, main_window, edit_device, installer_mode=False):
        self.main_window = main_window
        self.edit_device = edit_device
        self.installer_mode = installer_mode

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain("blivet-gui")
        self.builder.add_from_file(locate_ui_file("label_dialog.ui"))

        self.dialog = self.builder.get_object("label_dialog")
        self.dialog.set_transient_for(self.main_window)

        self.entry_label = self.builder.get_object("entry_label")

        button_cancel = self.builder.get_object("button_cancel")
        button_cancel.connect("clicked", self._on_cancel_button)

        button_format = self.builder.get_object("button_label")
        button_format.connect("clicked", self._on_format_button)

    def set_decorated(self, decorated):
        self.dialog.set_decorated(decorated)

        # no decoration --> display dialog title in the dialog
        if not decorated:
            label = self.builder.get_object("label_title")
            title = self.dialog.get_title()
            label.set_text(title)

    def _validate_user_input(self, label):
        if not self.edit_device.format.label_format_ok(label):
            msg = _("'{label}' is not a valid label for this filesystem").format(label=label)
            message_dialogs.ErrorDialog(self.dialog, msg,
                                        not self.installer_mode)  # do not show decoration in installer mode
            return False
        else:
            return True

    def run(self):
        response = self.dialog.run()

        if response == Gtk.ResponseType.ACCEPT:
            new_label = self.entry_label.get_text()
            if not self._validate_user_input(new_label):
                return self.run()
            else:
                self.dialog.destroy()
                return ProxyDataContainer(edit_device=self.edit_device, relabel=True, label=new_label)
        else:
            self.dialog.destroy()
            return ProxyDataContainer(edit_device=self.edit_device, relabel=False, label=None)

    def _on_cancel_button(self, _button):
        self.dialog.response(Gtk.ResponseType.REJECT)

    def _on_format_button(self, _button):
        self.dialog.response(Gtk.ResponseType.ACCEPT)


class UnmountDialog(object):

    def __init__(self, main_window, edit_device, mountpoints, installer_mode=False):
        self.main_window = main_window
        self.edit_device = edit_device
        self.installer_mode = installer_mode

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain("blivet-gui")
        self.builder.add_from_file(locate_ui_file("unmount_dialog.ui"))

        self.dialog = self.builder.get_object("unmount_dialog")
        self.dialog.set_transient_for(self.main_window)

        button_cancel = self.builder.get_object("button_cancel")
        button_cancel.connect("clicked", self._on_cancel_button)

        button_unmount = self.builder.get_object("button_unmount")
        button_unmount.connect("clicked", self._on_format_button)

        self.mountpoints_store = self.builder.get_object("mountpoints_store")
        for mountpoint in mountpoints:
            self.mountpoints_store.append([True, mountpoint])

        unmount_toggle = self.builder.get_object("unmount_toggle")
        unmount_toggle.connect("toggled", self._on_unmount_toggled)

    def set_decorated(self, decorated):
        self.dialog.set_decorated(decorated)

        # no decoration --> display dialog title in the dialog
        if not decorated:
            label = self.builder.get_object("label_title")
            title = self.dialog.get_title()
            label.set_text(title)

    def run(self):
        response = self.dialog.run()

        if response == Gtk.ResponseType.ACCEPT:
            mountpoints = []
            for row in self.mountpoints_store:
                if row[0]:
                    mountpoints.append(row[1])

            self.dialog.destroy()
            return ProxyDataContainer(edit_device=self.edit_device, unmount=True, mountpoints=mountpoints)
        else:
            self.dialog.destroy()
            return ProxyDataContainer(edit_device=self.edit_device, unmount=False, mountpoints=[])

    def _on_unmount_toggled(self, _toggle, path):
        self.mountpoints_store[path][0] = not self.mountpoints_store[path][0]

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

        Gtk.Dialog.__init__(self)

        self.set_transient_for(self.parent_window)
        self.set_resizable(False)  # auto shrink after removing/hiding widgets
        self.set_title(_("Edit device"))
        self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                         Gtk.STOCK_OK, Gtk.ResponseType.OK)

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

        self.grid.attach(label_list, 0, 1, 1, 1)
        self.grid.attach(parents_view, 1, 1, 3, 3)

    def add_toggle_buttons(self):

        button_add = Gtk.ToggleButton(label=_("Add a parent"))
        self.grid.attach(button_add, 0, 4, 1, 1)

        button_remove = Gtk.ToggleButton(label=_("Remove a parent"))
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

            column_toggle = Gtk.TreeViewColumn(_("Add?"), renderer_toggle, active=2)
            column_name = Gtk.TreeViewColumn(_("Device"), renderer_text, text=3)
            column_type = Gtk.TreeViewColumn(_("Type"), renderer_text, text=4)
            column_size = Gtk.TreeViewColumn(_("Size"), renderer_text, text=5)

            parents_view.append_column(column_toggle)
            parents_view.append_column(column_name)
            parents_view.append_column(column_type)
            parents_view.append_column(column_size)

            parents_view.set_headers_visible(True)

            label_list = Gtk.Label(label=_("Available devices:"), xalign=1)

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
            label_none = Gtk.Label(label=_("There isn't a physical volume that could be\n"
                                           "removed from this volume group."))
            self.grid.attach(label_none, 0, 5, 4, 1)

            self.widgets_dict["remove"] = [label_none]

            return None

        else:
            parents_store = Gtk.ListStore(object, object, bool, str, str, str)
            parents_view = Gtk.TreeView(model=parents_store)

            parents_view.set_tooltip_text(_("Currently it is possible to remove only one parent at time."))

            renderer_radio = Gtk.CellRendererToggle()
            renderer_radio.connect("toggled", self.on_cell_radio_toggled, parents_store)
            renderer_radio.set_radio(True)

            renderer_text = Gtk.CellRendererText()

            column_radio = Gtk.TreeViewColumn(_("Remove?"), renderer_radio, active=2)
            column_name = Gtk.TreeViewColumn(_("Device"), renderer_text, text=3)
            column_type = Gtk.TreeViewColumn(_("Type"), renderer_text, text=4)
            column_size = Gtk.TreeViewColumn(_("Size"), renderer_text, text=5)

            parents_view.append_column(column_radio)
            parents_view.append_column(column_name)
            parents_view.append_column(column_type)
            parents_view.append_column(column_size)

            parents_view.set_headers_visible(True)

            label_list = Gtk.Label(label=_("Available devices:"), xalign=1)

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
