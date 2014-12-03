# -*- coding: utf-8 -*-
# message_dialogs.py
# misc Gtk.MessageDialogs
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

def locate_ui_file(filename):

    path = [os.path.split(os.path.abspath(__file__))[0] + '/../../data/ui/',
        '/usr/share/blivet-gui/ui/']

    for folder in path:
        fn = folder + filename
        if os.access(fn, os.R_OK):
            return fn

    raise RuntimeError("Unable to find glade file %s" % filename)

#------------------------------------------------------------------------------#

class WarningDialog():
    """ Basic warning dialog
    """

    def __init__(self, parent_window, msg):

        builder = Gtk.Builder()
        builder.add_from_file(locate_ui_file('warning_dialog.ui'))
        dialog = builder.get_object("warning_dialog")

        dialog.set_transient_for(parent_window)
        dialog.format_secondary_text(msg)

        dialog.show_all()
        dialog.run()
        dialog.destroy()

class ErrorDialog():
    """ Basic error dialog
    """

    def __init__(self, parent_window, msg):

        builder = Gtk.Builder()
        builder.add_from_file(locate_ui_file('error_dialog.ui'))
        dialog = builder.get_object("error_dialog")

        dialog.set_transient_for(parent_window)
        dialog.format_secondary_text(msg)

        dialog.show_all()
        dialog.run()
        dialog.destroy()

class InfoDialog():
    """ Basic error dialog
    """

    def __init__(self, parent_window, msg):

        builder = Gtk.Builder()
        builder.add_from_file(locate_ui_file('info_dialog.ui'))
        dialog = builder.get_object("info_dialog")

        dialog.set_transient_for(parent_window)
        dialog.format_secondary_text(msg)

        dialog.show_all()
        dialog.run()
        dialog.destroy()

class ExceptionDialog():

    def __init__(self, parent_window, msg, traceback):

        builder = Gtk.Builder()
        builder.add_from_file(locate_ui_file('exception_dialog.ui'))
        dialog = builder.get_object("exception_dialog")

        dialog.set_transient_for(parent_window)
        dialog.format_secondary_text(msg)

        exception_label = builder.get_object("exception_label")
        exception_label.set_text(traceback)

        dialog.show_all()
        dialog.run()
        dialog.destroy()

class ConfirmDialog():
    """ General confirmation dialog
    """

    def __init__(self, parent_window, title, msg):

        builder = Gtk.Builder()
        builder.add_from_file(locate_ui_file('confirm_dialog.ui'))
        self.dialog = builder.get_object("confirm_dialog")

        self.dialog.set_transient_for(parent_window)
        self.dialog.set_markup("<b>" + title + "</b>")
        self.dialog.format_secondary_text(msg)

        self.dialog.show_all()

    def run(self):

        response = self.dialog.run()

        self.dialog.destroy()

        return response == Gtk.ResponseType.OK


class ConfirmActionsDialog():
    """ Confirm execute actions
    """

    def __init__(self, parent_window, title, msg, actions):

        self.actions = actions

        builder = Gtk.Builder()
        builder.add_from_file(locate_ui_file('confirm_actions_dialog.ui'))
        self.dialog = builder.get_object("confirm_actions_dialog")

        self.dialog.set_transient_for(parent_window)
        self.dialog.set_markup("<b>" + title + "</b>")
        self.dialog.format_secondary_text(msg)

        self.show_actions(builder.get_object("scrolledwindow"))

        self.dialog.show_all()

    def show_actions(self, viewport):

        icon_theme = Gtk.IconTheme.get_default()
        icon_add = Gtk.IconTheme.load_icon(icon_theme, "list-add", 16, 0)
        icon_delete = Gtk.IconTheme.load_icon (icon_theme, "edit-delete", 16, 0)
        icon_edit = Gtk.IconTheme.load_icon(icon_theme, "edit-select-all", 16, 0)

        actions_list = Gtk.ListStore(GdkPixbuf.Pixbuf, str)

        for action in self.actions:
            if action.isDestroy or action.isRemove:
                actions_list.append([icon_delete, str(action)])
            elif action.isAdd or action.isCreate:
                actions_list.append([icon_add, str(action)])
            else:
                actions_list.append([icon_edit, str(action)])

        treeview = Gtk.TreeView(model=actions_list)
        treeview.set_headers_visible(False)
        treeview.set_vexpand(True)
        treeview.set_hexpand(True)

        selection = treeview.get_selection()
        self.selection_signal = selection.connect("changed", self.on_action_clicked)

        renderer_pixbuf = Gtk.CellRendererPixbuf()
        column_pixbuf = Gtk.TreeViewColumn(None, renderer_pixbuf, pixbuf=0)
        treeview.append_column(column_pixbuf)

        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn(None, renderer_text, text=1)
        treeview.append_column(column_text)

        viewport.add(treeview)

    def on_action_clicked(self, selection):

        model, treeiter = selection.get_selected()

        if treeiter and model:
            selection.handler_block(self.selection_signal)
            selection.unselect_iter(treeiter)
            selection.handler_unblock(self.selection_signal)

    def run(self):

        response = self.dialog.run()

        self.dialog.destroy()

        return response == Gtk.ResponseType.OK
