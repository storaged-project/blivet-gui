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

import sys, os, signal, logging

from gi.repository import Gtk, GdkPixbuf

import gettext

from list_devices import ListDevices

from udisks_loop import udisks_thread

#------------------------------------------------------------------------------#

APP_NAME = "blivet-gui"

dirname, filename = os.path.split(os.path.abspath(__file__))

gettext.bindtextdomain('blivetgui', dirname + '/i18n')
gettext.textdomain('blivetgui')
_ = gettext.gettext

#------------------------------------------------------------------------------#

def main_window(kickstart = False):
	""" Create main window from Glade UI file
	"""
	
	builder = Gtk.Builder()
	builder.add_from_file(dirname + '/data/ui/blivet-gui.ui')

	signal.signal(signal.SIGINT, signal.SIG_DFL)

	MainWindow = builder.get_object("MainWindow")
	MainWindow.connect("delete-event", Gtk.main_quit)

	l = ListDevices(MainWindow, builder, kickstart)

	u = udisks_thread(l)
	u.start()
	
	return MainWindow

def embeded_window(kickstart=False):
	""" Create Gtk.Plug widget
	"""
	
	window_id = 0
	plug = Gtk.Plug(window_id)
	
	#FIXME
	print plug.get_id()
	
	builder = Gtk.Builder()
	builder.add_from_file(dirname + '/data/ui/blivet-gui.ui')

	signal.signal(signal.SIGINT, signal.SIG_DFL)

	vbox = builder.get_object("vbox")
	vbox.reparent(plug)

	ListDevices(plug, builder, kickstart)
	
	return plug