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
#------------------------------------------------------------------------------#

import threading, traceback

import gettext

from gi.repository import Gtk, GObject

#------------------------------------------------------------------------------#

_ = lambda x: gettext.ldgettext("blivet-gui", x)

#------------------------------------------------------------------------------#

class ProcessingActions(Gtk.Dialog):
    """ Processing actions dialog
    """

    def __init__(self, blivet_gui):

        self.blivet_gui = blivet_gui

        Gtk.Dialog.__init__(self, _("Proccessing"), None, 0, (Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_transient_for(self.blivet_gui.main_window)

        self.set_border_width(8)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_response_sensitive(Gtk.ResponseType.OK, False)

        self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10, column_spacing=5)
        self.grid.set_margin_bottom(12)

        box = self.get_content_area()
        box.add(self.grid)

        self.pulse = True
        self.success = False
        self.error = None

        self.label = Gtk.Label()
        self.grid.attach(self.label, 0, 0, 3, 1)

        self.label.set_markup(_("<b>Queued actions are being proccessed.</b>"))

        self.progressbar = Gtk.ProgressBar()
        self.grid.attach(self.progressbar, 0, 1, 3, 1)

        self.timeout_id = GObject.timeout_add(50, self.on_timeout, None)
        self.thread = threading.Thread(target=self.do_it)

        self.set_resizable(False)
        self.show_all()
        self.thread.start()

    def start(self):
        """ Start the dialog
        """

        self.run()
        self.destroy()

        return (self.success, self.error)

    def end(self, error=None):
        """ End the thread
        """

        self.thread.join()

        if error:
            self.success = False
            self.error = error
            self.destroy()

        else:
            self.pulse = False
            self.progressbar.set_fraction(1)
            self.set_response_sensitive(Gtk.ResponseType.OK, True)
            self.success = True
            self.label.set_markup(_("<b>All queued actions have been processed.</b>"))

    def on_timeout(self, user_data):
        """ Timeout fuction for progressbar pulsing
        """

        if self.pulse:
            self.progressbar.pulse()
            return True

        else:
            return False

    def do_it(self):
        """ Run blivet.doIt()
        """

        try:
            self.blivet_gui.blivet_utils.blivet_do_it() #FIXME
            GObject.idle_add(self.end)

        except Exception as e: # pylint: disable=broad-except
            self.blivet_gui.blivet_utils.blivet_reset() #FIXME
            GObject.idle_add(self.end, e)
