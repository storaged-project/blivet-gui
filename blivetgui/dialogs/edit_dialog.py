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

from blivet import Size

from math import floor, ceil

#------------------------------------------------------------------------------#

_ = lambda x: gettext.ldgettext("blivet-gui", x)

#------------------------------------------------------------------------------#

class EditDialog(Gtk.Dialog):
    """ Dialog window allowing user to edit partition including selecting size,
        fs, label etc.
    """

    #FIXME add mountpoint validation -- os.path.isabs(path)
    def __init__(self, parent_window, partition_name, resizable, kickstart=False):
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

        self.partition_name = partition_name
        self.resizable = resizable
        self.resize = False
        self.kickstart = kickstart

        self.parent_window = parent_window

        Gtk.Dialog.__init__(self, _("Edit device"), None, 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_transient_for(self.parent_window)
        self.set_default_size(550, 200)

        self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10,
            column_spacing=5)

        box = self.get_content_area()
        box.add(self.grid)

        self.add_size_scale()
        self.add_fs_chooser()

        if kickstart:
            self.add_mountpoint()

        self.show_all()

    def add_size_scale(self):

        # blivet.Size cuts fractional part: Size('2000 KiB').convertTo('MiB') = 1 MiB
        # so the down limit for resizing would be 1 MiB even though it is not
        # possible to resize the partition to less than 2 MiB (rounded to MiBs)
        self.down_limit = int(ceil(self.resizable[1].convertTo("KiB")/1024))
        self.up_limit = int(floor(self.resizable[2].convertTo("KiB")/1024))
        self.current_size = int(self.resizable[3].convertTo("MiB"))

        self.scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL,
            adjustment=Gtk.Adjustment(0, self.down_limit, self.up_limit, 1, 10, 0))

        self.scale.set_hexpand(True)
        self.scale.set_valign(Gtk.Align.START)
        self.scale.set_digits(0)
        self.scale.set_value(self.current_size)
        self.scale.add_mark(self.down_limit, Gtk.PositionType.BOTTOM,
            (str(self.down_limit)))
        self.scale.add_mark(self.up_limit, Gtk.PositionType.BOTTOM,
            str(self.up_limit))

        if self.current_size not in [self.down_limit, self.up_limit]:
            self.scale.add_mark(self.current_size, Gtk.PositionType.BOTTOM,
                str(self.current_size))

        self.scale.connect("value-changed", self.scale_moved)

        self.grid.attach(self.scale, 0, 1, 6, 1) #left-top-width-height

        self.label_size = Gtk.Label()
        self.label_size.set_text(_("Volume size:"))
        self.grid.attach(self.label_size, 0, 2, 1, 1)

        self.spin_size = Gtk.SpinButton(adjustment=Gtk.Adjustment(0,
            self.down_limit, self.up_limit, 1, 10, 0))

        self.spin_size.set_numeric(True)
        self.spin_size.set_value(self.current_size)
        self.spin_size.connect("value-changed", self.spin_size_moved)

        self.grid.attach(self.spin_size, 1, 2, 1, 1)

        self.label_mb = Gtk.Label()
        self.label_mb.set_text(_("MiB"))
        self.grid.attach(self.label_mb, 2, 2, 1, 1)

        if self.resizable[0] == False or self.down_limit == self.up_limit:
            self.label_resize = Gtk.Label()
            self.label_resize.set_markup(_("<b>This device cannot be resized.</b>"))
            self.grid.attach(self.label_resize, 0, 0, 6, 1)

            self.scale.set_sensitive(False)
            self.spin_size.set_sensitive(False)

    def add_fs_chooser(self):

        self.label_format = Gtk.Label()
        self.label_format.set_text(_("Format?:"))
        self.grid.attach(self.label_format, 0, 3, 1, 1)

        self.format_check = Gtk.CheckButton()
        self.grid.attach(self.format_check, 1, 3, 1, 1)
        self.format_check.connect("toggled", self.on_format_changed)

        self.label_fs = Gtk.Label()
        self.label_fs.set_text(_("Filesystem:"))
        self.grid.attach(self.label_fs, 0, 4, 1, 1)

        filesystems = ["ext2", "ext3", "ext4", "xfs", "reiserfs", "vfat"]
        self.filesystems_combo = Gtk.ComboBoxText()
        self.filesystems_combo.set_entry_text_column(0)
        self.filesystems_combo.set_sensitive(False)

        self.filesystems_combo.connect("changed", self.filesystems_combo_changed)

        for fs in filesystems:
            self.filesystems_combo.append_text(fs)

        self.grid.attach(self.filesystems_combo, 1, 4, 2, 1)

        self.label_warn = Gtk.Label()
        self.grid.attach(self.label_warn, 0, 6, 6, 1)

    def add_name_chooser(self):

        self.label_entry = Gtk.Label()
        self.label_entry.set_text(_("Label:"))
        self.grid.attach(self.label_entry, 0, 4, 1, 1)

        self.name_entry = Gtk.Entry()
        self.grid.attach(self.name_entry, 1, 4, 2, 1)

    def add_mountpoint(self):

        self.mountpoint_label = Gtk.Label()
        self.mountpoint_label.set_text(_("Mountpoint:"))
        self.grid.attach(self.mountpoint_label, 0, 5, 1, 1)

        self.mountpoint_entry = Gtk.Entry()
        self.grid.attach(self.mountpoint_entry, 1, 5, 2, 1)

    def filesystems_combo_changed(self, event):

        pass

    def scale_moved(self, event):

        self.resize = True
        self.spin_size.set_value(self.scale.get_value())

    def spin_size_moved(self,event):

        self.resize = True
        self.scale.set_value(self.spin_size.get_value())

    def on_format_changed(self, event):

        if self.format_check.get_active():
            self.filesystems_combo.set_sensitive(True)
            self.label_warn.set_markup(_("<b>Warning: This will delete all " \
                " data on {0}!</b>").format(self.partition_name))

        else:
            self.filesystems_combo.set_sensitive(False)
            self.label_warn.set_markup("")

    def get_selection(self):

        if self.format_check.get_active():
            if self.kickstart:
                return (self.resize, self.spin_size.get_value(),
                    self.filesystems_combo.get_active_text(),
                    self.mountpoint_entry.get_text())

            else:
                return (self.resize, self.spin_size.get_value(),
                    self.filesystems_combo.get_active_text(), None)

        else:
            if self.kickstart:
                return (self.resize, self.spin_size.get_value(), None,
                    self.mountpoint_entry.get_text())

            else:
                return (self.resize, self.spin_size.get_value(), None, None)
