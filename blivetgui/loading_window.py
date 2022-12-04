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
gi.require_version("GLib", "2.0")
gi.require_version("Pango", "1.0")

from gi.repository import Gtk, GLib, Pango

from .i18n import _

# ---------------------------------------------------------------------------- #


class LoadingWindow(Gtk.Dialog):
    """ Processing actions dialog
    """

    def __init__(self, parent_window):
        """ :param main_window: BlivetGUI main window
        """

        Gtk.Dialog.__init__(self)

        self.set_transient_for(parent_window)
        self.set_title(_("Probing storage"))

        self.set_border_width(8)
        self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)

        self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10, column_spacing=5)
        self.grid.set_margin_bottom(12)

        box = self.get_content_area()
        box.add(self.grid)

        self.pulse = True

        self.label = Gtk.Label()
        self.label.set_size_request(350, -1)
        self.label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label.set_line_wrap(True)
        self.label.set_text(_("Scanning storage configuration..."))

        self.grid.attach(self.label, 0, 0, 3, 1)

        self.progressbar = Gtk.ProgressBar()
        self.grid.attach(self.progressbar, 0, 1, 3, 1)

        self.timeout_id = GLib.timeout_add(50, self.on_timeout, None)

        self.set_resizable(False)
        self.show_all()

    def stop(self):
        self.destroy()

    def start(self):
        """ Start the dialog
        """

        self.progressbar.set_fraction(0)
        self.run()
        self.destroy()

    def on_timeout(self, _user_data):
        """ Timeout function for progressbar pulsing
        """

        if self.pulse:
            self.progressbar.pulse()
            return True

        else:
            return False
