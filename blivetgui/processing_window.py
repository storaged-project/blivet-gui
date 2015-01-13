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

    def __init__(self, list_partitions, parent_window):

        self.list_partitions = list_partitions
        self.parent_window = parent_window

        Gtk.Dialog.__init__(self, _("Proccessing"), None, 0, (Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_transient_for(self.parent_window)

        self.set_border_width(8)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_response_sensitive(Gtk.ResponseType.OK, False)

        self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10, column_spacing=5)
        self.grid.set_margin_bottom(12)

        box = self.get_content_area()
        box.add(self.grid)

        self.pulse = True
        self.success = False

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

        return self.success

    def end(self, error=None, traceback_msg=None):
        """ End the thread
        """

        self.thread.join()
        self.pulse = False
        self.progressbar.set_fraction(1)
        self.set_response_sensitive(Gtk.ResponseType.OK, True)

        if error:
            self.label.set_markup(_("<b>Queued actions couldn't be finished due to an unexpected " \
                                    "error.</b>\n\n%(error)s." % locals()))

            expander = Gtk.Expander(label=_("Show traceback"))
            self.grid.attach(expander, 0, 2, 3, 1)
            expander.add(Gtk.Label(label=traceback_msg))
            self.show_all()

            self.success = False

        else:
            self.label.set_markup(_("<b>All queued actions have been processed.</b>"))

            self.success = True

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
            self.list_partitions.b.blivet_do_it()
            GObject.idle_add(self.end)

        except Exception as e:
            self.list_partitions.b.blivet_reset()
            GObject.idle_add(self.end, e, traceback.format_exc())
