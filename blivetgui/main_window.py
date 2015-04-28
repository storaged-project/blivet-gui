# -*- coding: utf-8 -*-
# main_window.py
# blivet-gui Main Window
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

import os, signal

from gi.repository import Gtk

import gettext

#------------------------------------------------------------------------------#

_ = lambda x: gettext.translation("blivet-gui", fallback=True).gettext(x) if x != "" else ""

#------------------------------------------------------------------------------#

class MainWindow(object):

    def __init__(self, blivet_gui):

        self.blivet_gui = blivet_gui

        if self.blivet_gui.embedded_socket:
            self.window = self.embedded_window(blivet_gui.kickstart_mode, blivet_gui.embedded_socket)

        else:
            self.window = self.main_window(blivet_gui.kickstart_mode)
            self.window.connect("delete-event", self.blivet_gui.quit)

    def main_window(self, kickstart=False):
        """ Create main window from Glade UI file
        """

        return self.blivet_gui.builder.get_object("main_window")

    def embedded_window(self, kickstart=False, socket_id=0):
        """ Create Gtk.Plug widget
        """

        plug = Gtk.Plug.new(socket_id)
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        vbox = self.blivet_gui.builder.get_object("vbox")
        vbox.reparent(plug)

        return plug
