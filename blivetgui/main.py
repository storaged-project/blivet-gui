# -*- coding: utf-8 -*-
# main.py
# Main
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

from __future__ import print_function

import sys, optparse

import gettext

from gi.repository import GObject

from dialogs import message_dialogs

from main_window import *

from udisks_loop import udisks_thread

#------------------------------------------------------------------------------#

APP_NAME = "blivet-gui"
APP_VERSION = "0.1.0"

#------------------------------------------------------------------------------#

_ = lambda x: gettext.ldgettext("blivet-gui", x)

#------------------------------------------------------------------------------#

def parse_options():
    """
    Parses command-line arguments passed to blivet_gui
    """
    parser = optparse.OptionParser()
    parser.add_option("-v", "--version", action="store_true", dest="version",
                   default=False, help=_("show version information"))
    parser.add_option("-e", "--embeded", action="store_true", dest="embeded",
                   default=False, help=_("embed this application"))
    parser.add_option("-k", "--kickstart", action="store_true", dest="kickstart",
                   default=False, help=_("run blivet-gui in kickstart mode"))

    (options, args) = parser.parse_args()

    return options

def main(options=None):

    if options == None:
        options = parse_options()

    if options.version:
        print(APP_NAME, "version", APP_VERSION)
        sys.exit(0)

    elif os.geteuid() != 0:
        # root privileges are required for blivet

        msg = _("Root privileges are required for running blivet-gui.")
        message_dialogs.ErrorDialog(None, msg)
        sys.exit(0)

    else:

        if options.embeded:
            if options.kickstart:
                MainWindow = embeded_window(kickstart=True)
            else:
                MainWindow = embeded_window()
            MainWindow.show_all()

        elif options.kickstart:
            MainWindow = main_window(kickstart=True)
            MainWindow.set_position(Gtk.WindowPosition.CENTER)
            MainWindow.show_all()

        else:
            MainWindow = main_window()
            MainWindow.set_position(Gtk.WindowPosition.CENTER)
            MainWindow.show_all()

        Gtk.main()

if  __name__ == '__main__': main()
