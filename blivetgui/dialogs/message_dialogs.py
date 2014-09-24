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

from gi.repository import Gtk

#------------------------------------------------------------------------------#

APP_NAME = "blivet-gui"

dirname, filename = os.path.split(os.path.abspath(__file__))

#t = gettext.translation('messages', dirname + '/i18n')
#_ = t.gettext

gettext.bindtextdomain('blivetgui', dirname + '/i18n')
gettext.textdomain('blivetgui')
_ = gettext.gettext

#------------------------------------------------------------------------------#

class WarningDialog(Gtk.MessageDialog):
    """ Custom warning dialog
    """

    def __init__(self, parent_window, title, msg):

        self.parent_window = parent_window
        self.title = title
        self.msg = msg

        Gtk.MessageDialog.__init__(self, None, 0,
            Gtk.MessageType.WARNING,
            Gtk.ButtonsType.OK,
            self.title)

        self.format_secondary_text(self.msg)

        self.set_transient_for(self.parent_window)
        self.show_all()

        self.connect("delete-event", Gtk.main_quit)
        self.run()
        self.destroy()

class ErrorDialog(Gtk.MessageDialog):
    """ Custom error dialog
    """

    def __init__(self, parent_window, title, msg):

        self.parent_window = parent_window
        self.title = title
        self.msg = msg

        Gtk.MessageDialog.__init__(self, None, 0,
            Gtk.MessageType.ERROR,
            Gtk.ButtonsType.OK,
            self.title)

        self.format_secondary_text(self.msg)

        self.set_transient_for(self.parent_window)
        self.show_all()

        self.connect("delete-event", Gtk.main_quit)
        self.run()
        self.destroy()

class ExceptionDialog():

    def __init__(self, parent_window, msg, traceback):

        builder = Gtk.Builder()
        builder.add_from_file(dirname + '/../data/ui/exception_dialog.ui')
        dialog = builder.get_object("exception_dialog")

        dialog.set_transient_for(parent_window)
        dialog.format_secondary_text(msg)

        exception_label = builder.get_object("exception_label")
        exception_label.set_text(traceback)

        dialog.show_all()
        dialog.run()
        dialog.destroy()

class ConfirmDialog(Gtk.Dialog):
    """ General confirmation dialog
    """

    def __init__(self, parent_window, title, msg):
        """

            :param parent_window: parent window
            :type parent_window: Gtk.Window
            :param device_name: name of partition (device) to delete
            :type device_name: str

        """

        self.parent_window = parent_window
        self.title = title
        self.msg = msg

        Gtk.Dialog.__init__(self, self.title, None, 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_transient_for(self.parent_window)

        self.set_default_size(175, 110)

        label = Gtk.Label(self.msg)

        box = self.get_content_area()
        box.add(label)
        self.show_all()
