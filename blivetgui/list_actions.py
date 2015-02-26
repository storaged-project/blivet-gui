# -*- coding: utf-8 -*-
# list_partitions.py
# List of actions currently scheduled using blivet-gui
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

from gi.repository import Gtk, GdkPixbuf

import gettext

#------------------------------------------------------------------------------#

_ = lambda x: gettext.ldgettext("blivet-gui", x)

#------------------------------------------------------------------------------#

class ListActions(object):
    """ List of childs of selected device
    """

    def __init__(self, blivet_gui):

        self.blivet_gui = blivet_gui

        self.actions = 0
        self.actions_list = Gtk.TreeStore(GdkPixbuf.Pixbuf, str)

        self.actions_view = self.create_actions_view()

    def create_actions_view(self):
        """ Create treeview for actions

            :returns: treeview
            :rtype: Gtk.TreeView

        """

        treeview = Gtk.TreeView(model=self.actions_list)
        treeview.set_vexpand(True)
        treeview.set_hexpand(True)

        renderer_pixbuf = Gtk.CellRendererPixbuf()
        column_pixbuf = Gtk.TreeViewColumn(None, renderer_pixbuf, pixbuf=0)
        treeview.append_column(column_pixbuf)

        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn(None, renderer_text, text=1)
        treeview.append_column(column_text)

        treeview.set_headers_visible(False)

        return treeview

    def clear_actions_view(self):
        """ Delete all actions in actions view
        """

        self.actions = 0
        self.blivet_gui.actions_label.set_text(_("Pending actions ({0})").format(self.actions))
        self.actions_list.clear()

        self.blivet_gui.deactivate_options(["apply", "clear"])

        self.blivet_gui.update_partitions_view()

    def remove_action(self):
        """ Remove last action from the list
        """

        self.actions_list.remove(self.actions_list.get_iter(len(self.actions_list)-1))
        self.actions -= 1
        self.blivet_gui.actions_label.set_text(_("Pending actions ({0})").format(self.actions))

        if self.actions == 0:
            self.blivet_gui.deactivate_options(["clear", "apply", "undo"])

    def add_action(self):
        """ Add action to list
        """

        self.actions += 1
        self.blivet_gui.actions_label.set_text(_("Pending actions ({0})").format(self.actions))
        self.blivet_gui.activate_options(["undo"])

    def clear(self):
        self.actions = 0
        self.actions_list.clear()
        self.blivet_gui.actions_label.set_text(_("Pending actions ({0})").format(self.actions))

        self.blivet_gui.deactivate_options(["undo"])

    def update_actions_view(self, action_type=None, action_desc=None, blivet_actions=None):
        """ Update list of scheduled actions

            :param action_type: type of action (delete/add/edit)
            :type action_type: str
            :param action_desc: description of scheduled action
            :type partition_name: str

        """

        icon_theme = Gtk.IconTheme.get_default()
        icon_add = Gtk.IconTheme.load_icon(icon_theme, "list-add", 16, 0)
        icon_delete = Gtk.IconTheme.load_icon(icon_theme, "edit-delete", 16, 0)
        icon_edit = Gtk.IconTheme.load_icon(icon_theme, "edit-select-all", 16, 0)

        action_icons = {"add" : icon_add, "delete" : icon_delete, "edit" : icon_edit}


        parent_iter = self.actions_list.append(None, [action_icons[action_type], action_desc])

        for action in blivet_actions:
            self.actions_list.append(parent_iter, [None, str(action)])

        self.actions_view.expand_all()
        self.blivet_gui.actions_label.set_text(_("Pending actions ({0})").format(self.actions))

        self.blivet_gui.activate_options(["apply", "clear"])