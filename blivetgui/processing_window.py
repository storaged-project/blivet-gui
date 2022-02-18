# -*- coding: utf-8 -*-
# processing_window.py
# Gtk.Window
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
# ---------------------------------------------------------------------------- #

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Pango", "1.0")

from gi.repository import Gtk, GdkPixbuf, Pango

from .i18n import _

# ---------------------------------------------------------------------------- #


class ProcessingActions(Gtk.Dialog):
    """ Processing actions dialog
    """

    def __init__(self, blivet_gui, actions):
        """
            :param blivet-gui: BlivetGUI instance
            :type blivet-gui: :class:`~.blivetgui.BlivetGUI`
            :param actions: number of actions to process
            :type actions: int

        """

        self.blivet_gui = blivet_gui
        self.actions = actions

        self.finished_actions = 0

        Gtk.Dialog.__init__(self)

        self.set_transient_for(self.blivet_gui.main_window)
        self.set_title(_("Processing"))
        self.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK)

        self.set_border_width(8)
        self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        self.set_response_sensitive(Gtk.ResponseType.OK, False)

        self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10, column_spacing=5)
        self.grid.set_margin_bottom(12)

        box = self.get_content_area()
        box.add(self.grid)

        self.pulse = True

        self.label = Gtk.Label()
        self.label.set_size_request(350, -1)
        self.label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label.set_line_wrap(True)

        self.grid.attach(self.label, 0, 0, 3, 1)

        self.progressbar = Gtk.ProgressBar()
        self.grid.attach(self.progressbar, 0, 1, 3, 1)

        self.expander = Gtk.Expander(label=_("Show actions"), expanded=False)
        self.grid.attach(self.expander, 0, 2, 3, 1)

        self.actions_view, self.actions_list = self.add_action_view()

        self.set_resizable(True)
        self.show_all()

    def add_action_view(self):
        """ Show list of actions
        """

        icon_theme = Gtk.IconTheme.get_default()  # pylint: disable=no-value-for-parameter
        icon_add = Gtk.IconTheme.load_icon(icon_theme, "list-add-symbolic", 16, 0)
        icon_delete = Gtk.IconTheme.load_icon(icon_theme, "edit-delete-symbolic", 16, 0)
        icon_edit = Gtk.IconTheme.load_icon(icon_theme, "edit-select-all-symbolic", 16, 0)

        actions_list = Gtk.ListStore(GdkPixbuf.Pixbuf, str, GdkPixbuf.Pixbuf)

        for action in self.actions:
            if action.is_destroy or action.is_remove:
                actions_list.append([icon_delete, str(action), None])
            elif action.is_add or action.is_create:
                actions_list.append([icon_add, str(action), None])
            else:
                actions_list.append([icon_edit, str(action), None])

        actions_view = Gtk.TreeView(model=actions_list)
        actions_view.set_headers_visible(False)
        actions_view.set_vexpand(True)
        actions_view.set_hexpand(True)

        renderer_pixbuf = Gtk.CellRendererPixbuf()
        column_pixbuf = Gtk.TreeViewColumn(None, renderer_pixbuf, pixbuf=0)
        actions_view.append_column(column_pixbuf)

        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn(None, renderer_text, text=1)
        actions_view.append_column(column_text)

        renderer_pixbuf = Gtk.CellRendererPixbuf()
        column_pixbuf = Gtk.TreeViewColumn(None, renderer_pixbuf, pixbuf=2)
        actions_view.append_column(column_pixbuf)

        self.expander.add(actions_view)

        return actions_view, actions_list

    def _set_applied_icon(self, position):
        icon_theme = Gtk.IconTheme.get_default()  # pylint: disable=no-value-for-parameter
        icon_applied = Gtk.IconTheme.lookup_icon(icon_theme, "emblem-ok-symbolic", 16,
                                                 Gtk.IconLookupFlags.GENERIC_FALLBACK)
        if not icon_applied:
            # we did our best getting the icon, better no icon than a crash
            return

        icon_pixbuf = Gtk.IconInfo.load_icon(icon_applied)
        path = Gtk.TreePath(position)
        treeiter = self.actions_list.get_iter(path)
        self.actions_list.set_value(treeiter, 2, icon_pixbuf)

    def start(self):
        """ Start the dialog
        """

        self.progressbar.set_fraction(0)
        self.run()
        self.destroy()

    def stop(self):
        """ End the thread
        """

        self.progressbar.set_fraction(1)
        self.set_response_sensitive(Gtk.ResponseType.OK, True)
        self.label.set_markup("<b>%s</b>" % _("All queued actions have been processed."))

        # it is possible that there are no finished actions -- e.g. when adding
        # and removing the same partition -- blivet-gui scheduled 2 actions but
        # blivet actually won't create and destroy the partition, it will just
        # delete both actions
        # TODO: actually update 'blivet-gui actions' before running do_it and
        # update number of scheduled actions to match 'blivet actions'
        if self.finished_actions:
            self._set_applied_icon(self.finished_actions - 1)

        # now set resizable to False, so the dialog's size automatically adjusts
        self.set_resizable(False)

    def progress_msg(self, message):
        self.label.set_markup(_("<b>Processing action {num} of {total}</b>:"
                                "\n<i>{action}</i>").format(num=self.finished_actions,
                                                            total=len(self.actions),
                                                            action=message))

        if self.finished_actions:
            self._set_applied_icon(self.finished_actions - 1)

        self.progressbar.set_fraction(self.finished_actions / len(self.actions))
        self.finished_actions += 1
