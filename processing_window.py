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

import sys, os, signal
import threading, time

import gettext

from gi.repository import Gtk, GdkPixbuf, Gdk, GLib, GObject

#------------------------------------------------------------------------------#

APP_NAME = "blivet-gui"

gettext.bindtextdomain(APP_NAME, 'po')
gettext.textdomain(APP_NAME)
_ = gettext.gettext

#------------------------------------------------------------------------------#

class ProcessingActions(Gtk.Window):
	def __init__(self, list_partitions):
		self.list_partitions = list_partitions
		
		self.window = Gtk.Window(title=_("Proccessing"))

		self.window.set_border_width(8)
		self.window.set_position(Gtk.WindowPosition.CENTER)

		self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10, column_spacing=5)
		
		self.window.add(self.grid)
		
		self.pulse = True
		
		self.label = Gtk.Label()
		self.grid.attach(self.label, 0, 0, 2, 1)
		
		self.progressbar = Gtk.ProgressBar()
		self.grid.attach(self.progressbar, 0, 1, 2, 1)
		
		self.button = Gtk.Button(stock=Gtk.STOCK_OK)
		self.button.connect("clicked", self.close_window)
		self.button.set_sensitive(False)
		
		self.grid.attach(self.button, 1, 2, 1, 1)
		
		self.timeout_id = GObject.timeout_add(50, self.on_timeout, None)
			
		threading.Thread(target=do_it, args=[self, self.list_partitions]).start()
		
		self.window.show_all()
		self.start()

	def close_window(self, event):
		self.window.destroy()
	
	def start(self):
		self.progressbar.pulse()
		self.label.set_markup(_("<b>Queued actions are being proccessed.</b>"))
	
	def end(self):
		self.pulse = False
		self.progressbar.set_fraction(1)
		self.label.set_markup(_("<b>All queued actions have been processed.</b>"))
		self.button.set_sensitive(True)
	
	def on_timeout(self, user_data):
		
		if self.pulse:
			self.progressbar.pulse()
			return True
		
		else:
			return False

def do_it(window,list_partitions):
	list_partitions.b.blivet_do_it()
	window.end()