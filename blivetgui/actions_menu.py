# -*- coding: utf-8 -*-
# actions_menu.py
# Toolbar class
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
#------------------------------------------------------------------------------#

from gi.repository import Gtk

import gettext

#------------------------------------------------------------------------------#

_ = lambda x: gettext.translation("blivet-gui", fallback=True).gettext(x) if x != "" else ""

#------------------------------------------------------------------------------#

class ActionsMenu(object):
    """ Popup context menu for devices
    """

    def __init__(self, blivet_gui):
        self.blivet_gui = blivet_gui
        self.menu = Gtk.Menu()

        # Dict to translate menu item names (str) to menu items (Gtk.MenuItem)
        self.menu_items = {}

        self.create_menu()

    def create_menu(self):
        """ Create popup menu
        """

        items = [(_("New"), "add", self.blivet_gui.add_partition),
                 (_("Delete"), "delete", self.blivet_gui.delete_selected_partition),
                 (_("Edit"), "edit", self.blivet_gui.edit_device),
                 (_("Unmount"), "unmount", self.blivet_gui.umount_partition),
                 (_("Decrypt"), "decrypt", self.blivet_gui.decrypt_device),
                 (_("Information"), "info", self.blivet_gui.device_information)]

        for item in items:
            menu_item = Gtk.MenuItem()
            menu_item.set_label(item[0])

            menu_item.connect("activate", item[2])
            menu_item.set_sensitive(False)
            self.menu.add(menu_item)

            self.menu_items[item[1]] = menu_item

        self.menu.show_all()

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
            self.menu_items[item].set_sensitive(False)
