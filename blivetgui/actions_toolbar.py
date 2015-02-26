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

_ = lambda x: gettext.ldgettext("blivet-gui", x)

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
        """ Fill toolbar with buttons #FIXME: automate this
        """

        button_add = Gtk.ToolButton()
        button_add.set_icon_name("list-add-symbolic")
        button_add.set_sensitive(False)
        button_add.set_tooltip_text(_("Create new device"))
        self.toolbar.insert(button_add, 0)
        self.buttons["add"] = button_add
        button_add.connect("clicked", self.on_add_clicked)

        button_delete = Gtk.ToolButton()
        button_delete.set_icon_name("edit-delete-symbolic")
        button_delete.set_sensitive(False)
        button_delete.set_tooltip_text(_("Delete selected device"))
        self.toolbar.insert(button_delete, 1)
        self.buttons["delete"] = button_delete
        button_delete.connect("clicked", self.on_delete_clicked)

        self.toolbar.insert(Gtk.SeparatorToolItem(), 2)

        button_edit = Gtk.ToolButton()
        button_edit.set_icon_name("edit-select-all-symbolic")
        button_edit.set_sensitive(False)
        button_edit.set_tooltip_text(_("Edit or resize device"))
        self.toolbar.insert(button_edit, 3)
        self.buttons["edit"] = button_edit
        button_edit.connect("clicked", self.on_edit_clicked)

        button_umount = Gtk.ToolButton()
        button_umount.set_icon_name("media-eject-symbolic")
        button_umount.set_sensitive(False)
        button_umount.set_tooltip_text(_("Unmount selected device"))
        self.toolbar.insert(button_umount, 4)
        self.buttons["unmount"] = button_umount
        button_umount.connect("clicked", self.on_umount_clicked)

        button_decrypt = Gtk.ToolButton()
        button_decrypt.set_icon_name("dialog-password-symbolic")
        button_decrypt.set_sensitive(False)
        button_decrypt.set_tooltip_text(_("Decrypt selected device"))
        self.toolbar.insert(button_decrypt, 5)
        self.buttons["decrypt"] = button_decrypt
        button_decrypt.connect("clicked", self.on_decrypt_clicked)

        self.toolbar.insert(Gtk.SeparatorToolItem(), 6)

        button_apply = Gtk.ToolButton()
        button_apply.set_icon_name("object-select-symbolic")
        button_apply.set_sensitive(False)
        button_apply.set_tooltip_text(_("Apply queued actions"))
        self.toolbar.insert(button_apply, 7)
        self.buttons["apply"] = button_apply
        button_apply.connect("clicked", self.on_apply_clicked)

        button_undo = Gtk.ToolButton()
        button_undo.set_icon_name("edit-undo-symbolic")
        button_undo.set_sensitive(False)
        button_undo.set_tooltip_text(_("Undo"))
        self.toolbar.insert(button_undo, 8)
        self.buttons["undo"] = button_undo
        button_undo.connect("clicked", self.on_undo_clicked)

        button_clear = Gtk.ToolButton()
        button_clear.set_icon_name("edit-clear-all-symbolic")
        button_clear.set_sensitive(False)
        button_clear.set_tooltip_text(_("Clear queued actions"))
        self.toolbar.insert(button_clear, 9)
        self.buttons["clear"] = button_clear
        button_clear.connect("clicked", self.on_clear_clicked)

    def activate_buttons(self, button_names):
        """ Activate selected buttons

            :param button_names: names of buttons to activate
            :type button_names: list of str

        """

        for button in button_names:
            self.buttons[button].set_sensitive(True)

    def deactivate_buttons(self, button_names):
        """ Deactivate selected buttons

            :param button_names: names of buttons to deactivate
            :type button_names: list of str

        """

        for button in button_names:
            self.buttons[button].set_sensitive(False)

    def deactivate_all(self):
        """ Deactivate all partition based buttons
        """

        for button in self.buttons:
            if button not in ("apply", "clear", "undo", "redo"):
                self.buttons[button].set_sensitive(False)

    def on_delete_clicked(self, button):
        """ Onclick action for delete button
        """
        self.blivet_gui.delete_selected_partition()

    def on_add_clicked(self, button):
        """ Onclick action for add button
        """
        self.blivet_gui.add_partition()

    def on_edit_clicked(self, button):
        """ Onclick action for edit button
        """
        self.blivet_gui.edit_device()

    def on_umount_clicked(self, button):
        """ Onclick action for umount button
        """
        self.blivet_gui.umount_partition()

    def on_decrypt_clicked(self, button):
        """ Onclick action for decrypt button
        """
        self.blivet_gui.decrypt_device()

    def on_apply_clicked(self, button):
        """ Onclick action for edit button
        """
        self.blivet_gui.apply_event()

    def on_clear_clicked(self, button):
        """ Onselect action for 'Clear Queued Actions'
        """
        self.blivet_gui.clear_actions()

    def on_undo_clicked(self, button):
        """ Onselect action for 'Undo' button
        """
        self.blivet_gui.actions_undo()
