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

import sys, os, signal
import threading, time

import gettext

from gi.repository import Gtk, GdkPixbuf, Gdk, GLib, GObject

#------------------------------------------------------------------------------#

APP_NAME = "blivet-gui"

dirname, filename = os.path.split(os.path.abspath(__file__))

gettext.bindtextdomain('blivetgui', dirname + '/i18n')
gettext.textdomain('blivetgui')
_ = gettext.gettext

#------------------------------------------------------------------------------#

class ProcessingActions(Gtk.Dialog):
	
	def __init__(self, list_partitions, parent_window):
		
		self.list_partitions = list_partitions
		self.parent_window = parent_window
		
		Gtk.Dialog.__init__(self, _("Proccessing"), None, 0,
			None)
		
		self.set_transient_for(self.parent_window)
		
		self.set_border_width(8)
		self.set_position(Gtk.WindowPosition.CENTER)
		
		self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10, column_spacing=5)
		
		box = self.get_content_area()
		box.add(self.grid)
		
		self.pulse = True
		
		self.label = Gtk.Label()
		self.grid.attach(self.label, 0, 0, 2, 1)

		self.label.set_markup(_("<b>Queued actions are being proccessed.</b>"))
		
		self.progressbar = Gtk.ProgressBar()
		self.grid.attach(self.progressbar, 0, 1, 2, 1)
		
		self.button = Gtk.Button(stock=Gtk.STOCK_OK)
		self.button.connect("clicked", self.close_window)
		self.button.set_sensitive(False)
		
		self.grid.attach(self.button, 1, 2, 1, 1)
		
		self.timeout_id = GObject.timeout_add(50, self.on_timeout, None)
			
		self.thread = threading.Thread(target=self.do_it)
		
		self.show_all()
		self.thread.start()

	def close_window(self, event):
		self.destroy()
	
	def end(self, error=None):
		self.thread.join()
		self.pulse = False
		self.progressbar.set_fraction(1)
		self.button.set_sensitive(True)

		if error:
			self.label.set_markup(_("<b>Queued actions couldn't be finished due to an unexpected error.</b>\n\n%(error)s." % locals()))	
		
		else:
			self.label.set_markup(_("<b>All queued actions have been processed.</b>"))
	
	def on_timeout(self, user_data):
		
		if self.pulse:
			self.progressbar.pulse()
			return True
		
		else:
			return False
		
	def do_it(self):
		try:
			self.list_partitions.b.blivet_do_it()
			GObject.idle_add(self.end)

		except Exception as e:
			self.list_partitions.b.blivet_reset()
			GObject.idle_add(self.end(error=e))