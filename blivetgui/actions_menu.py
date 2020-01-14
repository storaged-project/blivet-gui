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
# ---------------------------------------------------------------------------- #


class ActionsMenu(object):
    """ Popup context menu for devices
    """

    def __init__(self, blivet_gui):
        self.blivet_gui = blivet_gui
        self.menu = self.blivet_gui.builder.get_object("actions_menu")

        # Dict to translate menu item names (str) to menu items (Gtk.MenuItem)
        self.menu_items = {}

        self.create_menu()

    def create_menu(self):
        """ Create popup menu
        """

        items = [("add", self.blivet_gui.add_device),
                 ("delete", self.blivet_gui.delete_selected_partition),
                 ("resize", self.blivet_gui.resize_device),
                 ("format", self.blivet_gui.format_device),
                 ("label", self.blivet_gui.edit_label),
                 ("unmount", self.blivet_gui.umount_partition),
                 ("decrypt", self.blivet_gui.decrypt_device),
                 ("info", self.blivet_gui.device_information),
                 ("parents", self.blivet_gui.edit_lvmvg),
                 ("mountpoint", self.blivet_gui.set_mountpoint),
                 ("partitiontable", self.blivet_gui.set_partition_table)]

        for item in items:
            menu_item = self.blivet_gui.builder.get_object("menuitem_" + item[0])
            menu_item.connect("activate", item[1])
            menu_item.set_sensitive(False)

            self.menu_items[item[0]] = menu_item

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
