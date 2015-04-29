# -*- coding: utf-8 -*-
# actions_toolbar.py
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
#
#------------------------------------------------------------------------------#

from gi.repository import Gtk

import gettext

#------------------------------------------------------------------------------#

_ = lambda x: gettext.translation("blivet-gui", fallback=True).gettext(x) if x != "" else ""

#------------------------------------------------------------------------------#

class ActionsToolbar(object):
    """ Create toolbar with action buttons
    """

    def __init__(self, blivet_gui):
        self.blivet_gui = blivet_gui

        self.toolbar = Gtk.Toolbar()

        # Dict to translate button names (str) to buttons (Gtk.ToolButton)
        self.buttons = {}

        self.create_buttons()

    def create_buttons(self):
        """ Fill toolbar with buttons
        """

        items = [("add", _("Create new device"), "list-add-symbolic", self.blivet_gui.add_partition),
                 ("delete", _("Delete selected device"), "edit-delete-symbolic", self.blivet_gui.delete_selected_partition),
                 ("separator",),
                 ("edit", _("Edit or resize device"), "edit-select-all-symbolic", self.blivet_gui.edit_device),
                 ("unmount", _("Unmount selected device"), "media-eject-symbolic", self.blivet_gui.umount_partition),
                 ("decrypt", _("Decrypt selected device"), "dialog-password-symbolic", self.blivet_gui.decrypt_device),
                 ("separator",),
                 ("apply", _("Apply queued actions"), "object-select-symbolic", self.blivet_gui.apply_event),
                 ("undo", _("Undo"), "edit-undo-symbolic", self.blivet_gui.actions_undo),
                 ("clear", _("Clear queued actions"), "edit-clear-all-symbolic", self.blivet_gui.clear_actions)]



        for index, item in enumerate(items):
            if item[0] == "separator":
                self.toolbar.insert(Gtk.SeparatorToolItem(), index)

            else:
                button = Gtk.ToolButton()
                button.set_icon_name(item[2])
                button.set_sensitive(False)
                button.set_tooltip_text(item[1])
                self.toolbar.insert(button, index)
                self.buttons[item[0]] = button
                button.connect("clicked", item[3])

    def activate_buttons(self, button_names):
        """ Activate selected buttons

            :param button_names: names of buttons to activate
            :type button_names: list of str

        """

        for button in button_names:
            if button in self.buttons.keys():
                self.buttons[button].set_sensitive(True)

    def deactivate_buttons(self, button_names):
        """ Deactivate selected buttons

            :param button_names: names of buttons to deactivate
            :type button_names: list of str

        """

        for button in button_names:
            if button in self.buttons.keys():
                self.buttons[button].set_sensitive(False)

    def deactivate_all(self):
        """ Deactivate all partition based buttons
        """

        for button in self.buttons:
            if button not in ("apply", "clear", "undo", "redo"):
                self.buttons[button].set_sensitive(False)
