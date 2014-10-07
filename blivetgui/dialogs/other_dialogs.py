# -*- coding: utf-8 -*-
# other_dialogs.py
# misc Gtk.Dialog classes
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

from gi.repository import Gtk, GdkPixbuf

#------------------------------------------------------------------------------#

_ = lambda x: gettext.ldgettext("blivet-gui", x)

#------------------------------------------------------------------------------#

dirname, filename = os.path.split(os.path.abspath(__file__)) #FIXME

#------------------------------------------------------------------------------#

class AboutDialog():
    """ Standard 'about application' dialog
    """

    def __init__(self, parent_window):

        builder = Gtk.Builder()
        builder.add_from_file(dirname + '/../data/ui/about_dialog.ui')
        dialog = builder.get_object("about_dialog")

        dialog.set_transient_for(parent_window)

        dialog.show_all()
        dialog.run()
        dialog.destroy()


class LuksPassphraseDialog(Gtk.Dialog):
    """ Dialog window allowing user to enter passphrase to decrypt
    """

    def __init__(self, parent_window, device_name):
        """

            :param parent_window: parent window
            :type parent_window: Gtk.Window
            :param device_name: name of device to decrypt
            :type device_name: str

        """

        builder = Gtk.Builder()
        builder.add_from_file(dirname + '/../data/ui/luks_passphrase_dialog.ui')
        self.dialog = builder.get_object("dialog")

        self.dialog.set_transient_for(parent_window)

        self.entry_passphrase = builder.get_object("entry_passphrase")
        self.dialog.show_all()

    def run(self):

        response = self.dialog.run()

        if response == Gtk.ResponseType.OK:
            return self.entry_passphrase.get_text()

        else:
            return None

        self.dialog.destroy()

class KickstartFileSaveDialog():
    """ File choose dialog for kickstart file save
    """
    def __init__(self, parent_window):

        builder = Gtk.Builder()
        builder.add_from_file(dirname + '/../data/ui/kickstart_filesave_dialog.ui')
        self.dialog = builder.get_object("kickstart_filesave_dialog")

        self.dialog.set_transient_for(parent_window)

    def run(self):

        response = self.dialog.run()
        self.dialog.destroy()

        if response == Gtk.ResponseType.OK:
            return True

        else:
            return False

class KickstartSelectDevicesDialog(Gtk.Dialog):
    """ Dialog window allowing user to select which devices will be used in
        kickstart mode
    """

    def __init__(self, parent_window, blivet_disks):
        """

            :param parent_window: parent_window
            :type parent_window: Gtk.Window
            :param blivet_disks: disks in the system
            :type blivet_disks: blivet.Device

        """

        self.parent_window = parent_window
        self.blivet_disks = blivet_disks

        Gtk.Dialog.__init__(self, _("Select devices"), None, 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_transient_for(self.parent_window)

        self.set_border_width(10)

        self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10,
            column_spacing=5)

        box = self.get_content_area()
        box.add(self.grid)

        self.add_device_list()
        self.add_bootloader_chooser()

        self.show_all()

    def add_device_list(self):

        self.disks_store = Gtk.ListStore(object, bool, GdkPixbuf.Pixbuf, str)

        self.disks_view = Gtk.TreeView(model=self.disks_store)

        renderer_toggle = Gtk.CellRendererToggle()
        renderer_toggle.connect("toggled", self.on_cell_toggled)
        column_toggle = Gtk.TreeViewColumn(None, renderer_toggle, active=1)
        self.disks_view.append_column(column_toggle)

        renderer_pixbuf = Gtk.CellRendererPixbuf()
        column_pixbuf = Gtk.TreeViewColumn(None, renderer_pixbuf, pixbuf=2)
        self.disks_view.append_column(column_pixbuf)

        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn('Pango Markup', renderer_text, markup=3)
        self.disks_view.append_column(column_text)

        self.disks_view.set_headers_visible(False)

        icon_theme = Gtk.IconTheme.get_default()
        icon_disk = Gtk.IconTheme.load_icon(icon_theme, "drive-harddisk", 32, 0)
        icon_disk_usb = Gtk.IconTheme.load_icon(icon_theme, "drive-removable-media", 32, 0)

        for disk in self.blivet_disks:
            if disk.removable:
                self.disks_store.append([disk, False, icon_disk_usb, str(disk.name +
                    "\n<i><small>" + disk.model + "</small></i>")])
            else:
                self.disks_store.append([disk, False, icon_disk, str(disk.name +
                    "\n<i><small>" + disk.model + "</small></i>")])

        self.label_list = Gtk.Label()
        self.label_list.set_text(_("Please select at least one of shown devices:"))

        self.grid.attach(self.label_list, 0, 1, 1, 1) #left-top-width-height
        self.grid.attach(self.disks_view, 0, 2, 4, 4)

    def on_cell_toggled(self, event, path):

        self.disks_store[path][1] = not self.disks_store[path][1]

    def add_bootloader_chooser(self):

        self.label_boot = Gtk.Label()
        self.label_boot.set_text(_("Install bootloader?:"))
        self.grid.attach(self.label_boot, 0, 7, 1, 1)

        self.boot_check = Gtk.CheckButton()
        self.grid.attach(self.boot_check, 1, 7, 1, 1)
        self.boot_check.connect("toggled", self.on_boot_changed)

        self.label_boot_device = Gtk.Label()
        self.label_boot_device.set_text(_("Device to install bootloader:"))
        self.grid.attach(self.label_boot_device, 0, 8, 1, 1)

        self.boot_device_combo = Gtk.ComboBoxText()
        self.boot_device_combo.set_entry_text_column(0)
        self.boot_device_combo.set_sensitive(False)
        self.grid.attach(self.boot_device_combo, 1, 8, 2, 1)

        for disk in self.blivet_disks:
            self.boot_device_combo.append_text(disk.name)

        self.boot_device_combo.connect("changed", self.on_boot_device_combo_changed)

    def on_boot_changed(self, event):

        self.boot_device_combo.set_sensitive(not self.boot_device_combo.get_sensitive())

    def on_boot_device_combo_changed(self, event):
        pass

    def get_selection(self):

        selected_disks_names = []

        for row in self.disks_store:
            if row[1]:
                selected_disks_names.append(row[0].name)

        return (selected_disks_names, self.boot_device_combo.get_sensitive(),
            self.boot_device_combo.get_active_text())
