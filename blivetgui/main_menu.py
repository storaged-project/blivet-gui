# -*- coding: utf-8 -*-
# main_menu.py
# Main menu
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

import gettext

from gi.repository import Gtk

from .dialogs.other_dialogs import AboutDialog
from .dialogs.message_dialogs import ErrorDialog, WarningDialog

import os, subprocess

#------------------------------------------------------------------------------#

_ = lambda x: gettext.ldgettext("blivet-gui", x)

#------------------------------------------------------------------------------#

class MainMenu(object):
    """ Main menu for blivet-gui
    """

    def __init__(self, blivet_gui):

        self.blivet_gui = blivet_gui

        self.menu_bar = Gtk.MenuBar()

        self.icon_theme = Gtk.IconTheme.get_default()

        self.agr = Gtk.AccelGroup()
        self.blivet_gui.main_window.add_accel_group(self.agr)

        self.menu_items = {}

        self.menu_bar.add(self.add_file_menu())
        self.menu_bar.add(self.add_edit_menu())
        self.menu_bar.add(self.add_device_menu())
        self.menu_bar.add(self.add_help_menu())

    def add_file_menu(self):
        """ Menu item 'File'
        """

        file_menu_item = Gtk.MenuItem(label=_("File"))

        file_menu = Gtk.Menu()
        file_menu_item.set_submenu(file_menu)

        reload_item = Gtk.MenuItem()
        reload_item.set_label(_("Reload"))
        key, mod = Gtk.accelerator_parse("<Control>R")
        reload_item.add_accelerator("activate", self.agr, key, mod, Gtk.AccelFlags.VISIBLE)

        reload_item.connect("activate", self.on_reload_item)

        file_menu.add(reload_item)

        quit_item = Gtk.MenuItem()
        quit_item.set_label(_("Quit"))
        key, mod = Gtk.accelerator_parse("<Control>Q")
        quit_item.add_accelerator("activate", self.agr, key, mod, Gtk.AccelFlags.VISIBLE)

        quit_item.connect("activate", self.on_quit_item)
        file_menu.add(quit_item)

        return file_menu_item

    def add_edit_menu(self):
        """ Menu item 'Edit'
        """

        edit_menu_item = Gtk.MenuItem(label=_("Edit"))
        edit_menu = Gtk.Menu()
        edit_menu_item.set_submenu(edit_menu)

        undo_item = Gtk.MenuItem()
        undo_item.set_label(_("Undo Last Action"))
        key, mod = Gtk.accelerator_parse("<Control>Z")
        undo_item.add_accelerator("activate", self.agr, key, mod, Gtk.AccelFlags.VISIBLE)

        undo_item.connect("activate", self.on_undo_item)
        undo_item.set_sensitive(False)
        edit_menu.add(undo_item)

        self.menu_items["undo"] = undo_item

        clear_item = Gtk.MenuItem()
        clear_item.set_label(_("Clear Queued Actions"))

        clear_item.connect("activate", self.on_clear_item)
        clear_item.set_sensitive(False)
        edit_menu.add(clear_item)

        self.menu_items["clear"] = clear_item

        apply_item = Gtk.MenuItem()
        apply_item.set_label(_("Apply Queued Actions"))
        key, mod = Gtk.accelerator_parse("<Control>A")
        apply_item.add_accelerator("activate", self.agr, key, mod, Gtk.AccelFlags.VISIBLE)

        apply_item.connect("activate", self.on_apply_item)
        apply_item.set_sensitive(False)
        edit_menu.add(apply_item)

        self.menu_items["apply"] = apply_item

        return edit_menu_item

    def add_device_menu(self):
        """ Menu item 'Device'
        """

        device_menu_item = Gtk.MenuItem(label=_("Device"))
        device_menu = Gtk.Menu()
        device_menu_item.set_submenu(device_menu)

        add_item = Gtk.MenuItem()
        add_item.set_label(_("New"))
        key, mod = Gtk.accelerator_parse("Insert")
        add_item.add_accelerator("activate", self.agr, key, mod, Gtk.AccelFlags.VISIBLE)

        add_item.connect("activate", self.on_add_item)
        add_item.set_sensitive(False)
        device_menu.add(add_item)

        self.menu_items["add"] = add_item

        delete_item = Gtk.MenuItem()
        delete_item.set_label(_("Delete"))
        key, mod = Gtk.accelerator_parse("Delete")
        delete_item.add_accelerator("activate", self.agr, key, mod, Gtk.AccelFlags.VISIBLE)

        delete_item.connect("activate", self.on_delete_item)
        delete_item.set_sensitive(False)
        device_menu.add(delete_item)

        self.menu_items["delete"] = delete_item

        edit_item = Gtk.MenuItem()
        edit_item.set_label(_("Edit"))

        edit_item.connect("activate", self.on_edit_item)
        edit_item.set_sensitive(False)
        device_menu.add(edit_item)

        self.menu_items["edit"] = edit_item

        device_menu.append(Gtk.SeparatorMenuItem())

        umount_item = Gtk.MenuItem()
        umount_item.set_label(_("Unmount"))

        umount_item.connect("activate", self.on_umount_item)
        umount_item.set_sensitive(False)
        device_menu.add(umount_item)

        self.menu_items["unmount"] = umount_item

        decrypt_item = Gtk.MenuItem()
        decrypt_item.set_label(_("Decrypt"))

        decrypt_item.connect("activate", self.on_decrypt_item)
        decrypt_item.set_sensitive(False)
        device_menu.add(decrypt_item)

        self.menu_items["decrypt"] = decrypt_item

        return device_menu_item

    def add_help_menu(self):
        """ Menu item 'Help'
        """

        help_menu_item = Gtk.MenuItem(label=_("Help"))
        help_menu = Gtk.Menu()
        help_menu_item.set_submenu(help_menu)

        help_item = Gtk.MenuItem()
        help_item.set_label(_("Contents"))
        key, mod = Gtk.accelerator_parse("F1")
        help_item.add_accelerator("activate", self.agr, key, mod, Gtk.AccelFlags.VISIBLE)

        help_item.connect("activate", self.on_help_item)
        help_menu.add(help_item)

        about_item = Gtk.MenuItem()
        about_item.set_label(_("About"))

        about_item.connect("activate", self.on_about_item)
        help_menu.add(about_item)

        return help_menu_item

    def activate_menu_items(self, menu_item_names):
        """ Activate selected menu items

            :param menu_item_names: names of menu items to activate
            :type button_names: list of str

        """

        for item in menu_item_names:
            self.menu_items[item].set_sensitive(True)

    def deactivate_menu_items(self, menu_item_names):
        """ Deactivate selected buttons

            :param menu_item_names: names of menu items to activate
            :type button_names: list of str

        """

        for item in menu_item_names:
            self.menu_items[item].set_sensitive(False)

    def deactivate_all(self):
        """ Deactivate all partition based buttons
        """

        for item in self.menu_items:
            if item not in ("apply", "clear", "undo"):
                self.menu_items[item].set_sensitive(False)

    def on_about_item(self, *args):
        """ Onselect action for 'About'
        """

        AboutDialog(self.blivet_gui.main_window)

    def on_help_item(self, *args):
        """ Onselect action for 'Help'
        """

        if not os.access('/usr/share/help/C/blivet-gui/index.page', os.R_OK):
            msg = _("Documentation for blivet-gui hasn't been found.\n\n" \
                "Online version of documentation is available at " \
                "http://vojtechtrefny.github.io/blivet-gui")

            self.blivet_gui.show_warning_dialog(msg)
            return

        try:
            fnull = open(os.devnull, "w")

            user = os.getenv("PKEXEC_UID")

            if user:
                subprocess.Popen(["yelp", "/usr/share/help/C/blivet-gui/index.page"],
                                 stdout=fnull, stderr=subprocess.STDOUT,
                                 preexec_fn=lambda: (os.setuid(int(user))))

            else:
                subprocess.Popen(["yelp", "/usr/share/help/C/blivet-gui/index.page"],
                                 stdout=fnull, stderr=subprocess.STDOUT)

        except OSError:
            msg = _("You need \"Yelp\" to see the documentation.\n\n" \
                    "Online version of documentation is available at " \
                    "http://vojtechtrefny.github.io/blivet-gui")

            self.blivet_gui.show_error_dialog(msg)

    def on_undo_item(self, *args):
        """ Onselect action for 'Undo Last Action'
        """
        self.blivet_gui.actions_undo()

    def on_clear_item(self, *args):
        """ Onselect action for 'Clear Queued Actions'
        """
        self.blivet_gui.clear_actions()

    def on_apply_item(self, *args):
        """ Onselect action for 'Apply Queued Actions'
        """
        self.blivet_gui.apply_event()

    def on_add_item(self, *args):
        """ Onselect action for 'New'
        """
        self.blivet_gui.add_partition()

    def on_delete_item(self, *args):
        """ Onselect action for 'Delete'
        """
        self.blivet_gui.delete_selected_partition()

    def on_edit_item(self, *args):
        """ Onselect action for 'Edit'
        """
        self.blivet_gui.edit_device()

    def on_umount_item(self, *args):
        """ Onselect action for 'Unmount'
        """
        self.blivet_gui.umount_partition()

    def on_decrypt_item(self, *args):
        """ Onselect action for 'Decrypt'
        """
        self.blivet_gui.decrypt_device()

    def on_quit_item(self, *args):
        """ Onselect action for 'Quit'
        """
        self.blivet_gui.quit()

    def on_reload_item(self, *args):
        """ Onselect action for 'Reload'
        """
        self.blivet_gui.reload()
