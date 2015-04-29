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

import os, subprocess

#------------------------------------------------------------------------------#

_ = lambda x: gettext.translation("blivet-gui", fallback=True).gettext(x) if x != "" else ""

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

        items = [(None, _("Reload"), "<Control>R", self.blivet_gui.reload, None),
                 (None, _("Quit"), "<Control>Q", self.blivet_gui.quit)
                ]

        self.add_to_menu(file_menu, items)

        return file_menu_item

    def add_edit_menu(self):
        """ Menu item 'Edit'
        """

        edit_menu_item = Gtk.MenuItem(label=_("Edit"))
        edit_menu = Gtk.Menu()
        edit_menu_item.set_submenu(edit_menu)

        items = [("undo", _("Undo Last Action"), "<Control>Z", self.blivet_gui.actions_undo),
                 ("clear", _("Clear Queued Actions"), None, self.blivet_gui.clear_actions),
                 ("apply", _("Apply Queued Actions"), "<Control>A", self.blivet_gui.apply_event)
                ]

        self.add_to_menu(edit_menu, items)

        return edit_menu_item

    def add_device_menu(self):
        """ Menu item 'Device'
        """

        device_menu_item = Gtk.MenuItem(label=_("Device"))
        device_menu = Gtk.Menu()
        device_menu_item.set_submenu(device_menu)

        items = [("add", _("New"), "Insert", self.blivet_gui.add_partition),
                 ("delete", _("Delete"), "Delete", self.blivet_gui.delete_selected_partition),
                 ("edit", _("Edit"), None, self.blivet_gui.edit_device),
                 ("separator",),
                 ("unmount", _("Unmount"), None, self.blivet_gui.umount_partition),
                 ("decrypt", _("Decrypt"), None, self.blivet_gui.decrypt_device)
                ]

        self.add_to_menu(device_menu, items)

        return device_menu_item

    def add_help_menu(self):
        """ Menu item 'Help'
        """

        help_menu_item = Gtk.MenuItem(label=_("Help"))
        help_menu = Gtk.Menu()
        help_menu_item.set_submenu(help_menu)

        items = [(None, _("Contents"), "F1", self.on_help_item),
                 (None, _("About"), None, self.on_about_item),
                ]

        self.add_to_menu(help_menu, items)

        return help_menu_item

    def add_to_menu(self, menu, items):
        """ Add items to menu

            :param menu: menu
            :type menu: Gtk.Menu
            :param items: list of items to add
            :type items: list of Gtk.MenuItem

        """

        for item in items:
            if item[0] == "separator":
                menu.append(Gtk.SeparatorMenuItem())
                continue

            menu_item = Gtk.MenuItem()
            menu_item.set_label(item[1])
            menu_item.connect("activate", item[3])

            if item[2]:
                key, mod = Gtk.accelerator_parse(item[2])
                menu_item.add_accelerator("activate", self.agr, key, mod, Gtk.AccelFlags.VISIBLE)

            if item[0]:
                menu_item.set_sensitive(False)
                self.menu_items[item[0]] = menu_item

            menu.add(menu_item)

    def activate_menu_items(self, menu_item_names):
        """ Activate selected menu items

            :param menu_item_names: names of menu items to activate
            :type button_names: list of str

        """

        for item in menu_item_names:
            if item in self.menu_items.keys():
                self.menu_items[item].set_sensitive(True)

    def deactivate_menu_items(self, menu_item_names):
        """ Deactivate selected buttons

            :param menu_item_names: names of menu items to activate
            :type button_names: list of str

        """

        for item in menu_item_names:
            if item in self.menu_items.keys():
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
