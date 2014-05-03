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

import sys, os, signal, logging

from gi.repository import Gtk, GdkPixbuf

import blivet

import gettext

import cairo

from utils import *

from dialogs import *

from list_devices import *

APP_NAME = "blivet-gui"

#-----------------------------------------------------#

gettext.bindtextdomain(APP_NAME, 'po')
gettext.textdomain(APP_NAME)
_ = gettext.gettext

#-----------------------------------------------------#

#TODO
"""

1. Edit VG -- pridani noveho pv
3. Embedovani
6. dokumentace
7. mozna device-info
"""




def start(): #FIXME to new file/class
	
	window_id = 0
	plug = Gtk.Plug(window_id)
	
	print plug.get_id()
	
	builder = Gtk.Builder()
	builder.add_from_file("blivet-gui.glade")

	signal.signal(signal.SIGINT, signal.SIG_DFL)

	MainWindow = builder.get_object("MainWindow")
	MainWindow.connect("delete-event", Gtk.main_quit)

	dlist = ListDevices(builder)

	builder.get_object("disks_viewport").add(dlist.get_disks_view())

	builder.get_object("partitions_viewport").add(dlist.return_partitions_view())

	builder.get_object("actions_viewport").add(dlist.return_actions_view())

	builder.get_object("image_window").add(dlist.return_partitions_image())

	builder.get_object("vbox").add(dlist.get_partions_list().get_main_menu)
	builder.get_object("vbox").add(dlist.get_partions_list().get_toolbar)
	
	return MainWindow

#-----------------------------------------------------#


def main():	
	if os.geteuid() != 0:
		# root privileges are required for blivet
		RootTestDialog()
		sys.exit(0)
	
	else:
		MainWindow = start()
		MainWindow.show_all()
		Gtk.main()

if  __name__ =='__main__':main()

