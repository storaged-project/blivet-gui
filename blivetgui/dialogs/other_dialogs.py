# -*- coding: utf-8 -*-
# other_dialogs.py
# misc Gtk.Dialog classes
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

from gi.repository import Gtk

#------------------------------------------------------------------------------#

_ = lambda x: gettext.ldgettext("blivet-gui", x)

#------------------------------------------------------------------------------#

class AboutDialog(Gtk.AboutDialog):
    """ Standard 'about application' dialog
    """

    def __init__(self, parent_window):
        Gtk.AboutDialog.__init__(self)

        self.parent_window = parent_window

        self.set_transient_for(self.parent_window)

        authors = ["Vojtech Trefny <vtrefny@redhat.com>"]
        documenters = ["Vojtech Trefny <vtrefny@redhat.com>"]

        self.set_program_name(APP_NAME)
        self.set_copyright(_("Copyright \xc2\xa9 2014 Red Hat Inc."))
        self.set_authors(authors)
        self.set_documenters(documenters)
        self.set_website("https://github.com/vojtechtrefny/blivet-gui")
        self.set_website_label("blivet-gui Website")
        self.set_license_type(Gtk.License.GPL_3_0)

        self.set_title("")

        self.connect("response", self.on_close)

        self.show()

    def on_close(self, action, par):
        self.destroy()


class LuksPassphraseDialog(Gtk.Dialog):
    """ Dialog window allowing user to enter passphrase to decrypt
    """

    def __init__(self, parent_window, device_name):
        """

            :param parent_window: parent window
            :type parent_window: Gtk.Window
            :param device_name: name of device to decrypt
            :type device_name: str

        """

        self.parent_window = parent_window
        self.device_name = device_name

        Gtk.Dialog.__init__(self, _("Enter passphrase to decrypt {0}").format(self.device_name),
            None, 0, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_transient_for(self.parent_window)

        self.set_default_size(250, 100)
        self.set_border_width(10)

        self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10,
            column_spacing=5)

        box = self.get_content_area()
        box.add(self.grid)

        self.pass_label = Gtk.Label()
        self.pass_label.set_markup(_("Passphrase:"))

        self.grid.attach(self.pass_label, 0, 0, 1, 1) #left-top-width-height

        self.pass_entry = Gtk.Entry()
        self.pass_entry.set_visibility(False)
        self.pass_entry.set_property("caps-lock-warning", True)

        self.grid.attach(self.pass_entry, 1, 0, 2, 1)

        self.show_all()

    def get_selection(self):

        return self.pass_entry.get_text()
