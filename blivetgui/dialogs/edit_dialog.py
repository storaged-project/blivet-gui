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
#------------------------------------------------------------------------------#

import os

import gettext

from gi.repository import Gtk

from add_dialog import SizeChooserArea

#------------------------------------------------------------------------------#

_ = lambda x: gettext.ldgettext("blivet-gui", x)

#------------------------------------------------------------------------------#

SUPPORTED_FS = ["ext2", "ext3", "ext4", "xfs", "reiserfs", "swap", "vfat"]

#------------------------------------------------------------------------------#

class UserSelection(object):
    def __init__(self, edit_device, resize, size, format, filesystem, mountpoint):

        self.edit_device = edit_device
        self.resize = resize
        self.size = size
        self.format = format
        self.filesystem = filesystem
        self.mountpoint = mountpoint

class EditDialog(Gtk.Dialog):
    """ Dialog window allowing user to edit partition including selecting size,
        fs, label etc.
    """

    def __init__(self, parent_window, edited_device, resizable, kickstart=False):
        """

            :param parent_window: parent window
            :type parent_window: Gtk.Window
            :param partition_name: name of device
            :type partition_name: str
            :param resizable: is partition resizable, minSize, maxSize
            :type resizable: tuple
            :param kickstart: kickstart mode
            :type kickstart: bool

        """

        self.edited_device = edited_device
        self.resizable = resizable
        self.kickstart = kickstart
        self.parent_window = parent_window

        Gtk.Dialog.__init__(self, _("Edit device"), None, 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_transient_for(self.parent_window)
        self.set_resizable(False) # auto shrink after removing/hiding widgets

        self.widgets_dict = {}

        self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10,
            column_spacing=5)
        self.grid.set_border_width(10)

        box = self.get_content_area()
        box.add(self.grid)

        self.show_all()

        self.size_area = self.add_size_chooser()

        self.format_check, self.filesystems_combo = self.add_fs_chooser()

        self.mountpoint_entry = self.add_mountpoint()

        if self.resizable[0]:
            self.show_widgets(["size"])

        if self.kickstart:
            self.show_widgets(["mountpoint"])

        self.show_widgets(["fs"])

    def add_size_chooser(self):

        size_area = SizeChooserArea(dialog=self, dialog_type="edit", parent_device=None,
            max_size=self.resizable[2], min_size=self.resizable[1],
            edited_device=self.edited_device)

        self.grid.attach(size_area.frame, 0, 0, 6, 1)

        self.widgets_dict["size"] = [size_area]

        return size_area

    def add_fs_chooser(self):

        label_format = Gtk.Label(label=_("Format?:"), xalign=1)
        label_format.get_style_context().add_class("dim-label")
        self.grid.attach(label_format, 0, 1, 1, 1)

        format_check = Gtk.CheckButton()
        self.grid.attach(format_check, 1, 1, 1, 1)
        format_check.connect("toggled", self.on_format_changed)

        label_fs = Gtk.Label(label=_("Filesystem:"), xalign=1)
        label_fs.get_style_context().add_class("dim-label")
        self.grid.attach(label_fs, 0, 2, 1, 1)

        filesystems_combo = Gtk.ComboBoxText()
        filesystems_combo.set_entry_text_column(0)
        filesystems_combo.set_sensitive(False)

        self.widgets_dict["fs"] = [label_format, format_check, label_fs,
            filesystems_combo]

        for fs in SUPPORTED_FS:
            filesystems_combo.append_text(fs)

        self.grid.attach(filesystems_combo, 1, 2, 2, 1)

        return (format_check, filesystems_combo)

    def add_mountpoint(self):

        label_mountpoint = Gtk.Label(label=_("Mountpoint:"), xalign=1)
        label_mountpoint.get_style_context().add_class("dim-label")
        self.grid.attach(label_mountpoint, 0, 3, 1, 1)

        mountpoint_entry = Gtk.Entry()
        self.grid.attach(mountpoint_entry, 1, 3, 2, 1)

        self.widgets_dict["mountpoint"] = [label_mountpoint, mountpoint_entry]

        return mountpoint_entry

    def on_format_changed(self, event):

        if self.format_check.get_active():
            self.filesystems_combo.set_sensitive(True)

        else:
            self.filesystems_combo.set_sensitive(False)

    def update_size_areas(self, size):
        """ Update all size areas to selected size
            (used for raids where all parents has same size)

            .. note:: Copied from AddDialog for future use
        """

        pass

    def show_widgets(self, widget_types):

        for widget_type in widget_types:
            if widget_type == "mountpoint" and not self.kickstart:
                continue

            else:
                for widget in self.widgets_dict[widget_type]:
                    widget.show()

    def hide_widgets(self, widget_types):

        for widget_type in widget_types:
            if widget_type == "mountpoint" and not self.kickstart:
                continue

            else:
                for widget in self.widgets_dict[widget_type]:
                    widget.hide()

    def get_selection(self):

        if self.kickstart:
            mountpoint = self.mountpoint_entry.get_text()

        else:
            mountpoint = None

        if self.resizable[0]:
            resize, size = self.size_area.get_selection()

        else:
            resize = False
            size = None

        return UserSelection(edit_device=self.edited_device,
            resize=resize,
            size=size,
            format=self.format_check.get_active(),
            filesystem=self.filesystems_combo.get_active_text(),
            mountpoint=mountpoint)
