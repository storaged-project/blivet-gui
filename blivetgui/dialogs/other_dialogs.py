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

dirname, filename = os.path.split(os.path.abspath(__file__)) #FIXME

#------------------------------------------------------------------------------#

class AboutDialog():
    """ Standard 'about application' dialog
    """

    def __init__(self, parent_window):

        builder = Gtk.Builder()
        builder.add_from_file(dirname + '/../data/ui/about_dialog.ui')
        dialog = builder.get_object("about_dialog")

        dialog.set_transient_for(parent_window)

        dialog.show_all()
        dialog.run( )
        dialog.destroy()


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

        builder = Gtk.Builder()
        builder.add_from_file(dirname + '/../data/ui/luks_passphrase_dialog.ui')
        self.dialog = builder.get_object("dialog")

        self.dialog.set_transient_for(parent_window)

        self.entry_passphrase = builder.get_object("entry_passphrase")
        self.dialog.show_all()

    def run(self):

        response = self.dialog.run()

        if response == Gtk.ResponseType.OK:
            return self.entry_passphrase.get_text()

        else:
            return None

        self.dialog.destroy()
