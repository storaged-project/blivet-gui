# main_menu.py
# Main menu
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
 
import sys, os, signal

import gettext

from gi.repository import Gtk, GdkPixbuf

from dialogs import *

APP_NAME = "blivet-gui"

gettext.bindtextdomain(APP_NAME, 'po')
gettext.textdomain(APP_NAME)
_ = gettext.gettext

class main_menu():

	def __init__(self,main_window,list_partitions):
		
		self.list_partitions = list_partitions
		
		self.menu_bar = Gtk.MenuBar()
		
		self.icon_theme = Gtk.IconTheme.get_default()
		
		self.agr = Gtk.AccelGroup()
		main_window.add_accel_group(self.agr)
		
		self.menu_bar.add(self.add_file_menu())
		self.menu_bar.add(self.add_help_menu())
	
	def add_file_menu(self):
		
		file_menu_item = Gtk.MenuItem(label=_("File"))
		
		file_menu = Gtk.Menu()
		file_menu_item.set_submenu(file_menu)
		
		quit_item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_QUIT, self.agr)
		key, mod = Gtk.accelerator_parse("<Control>Q")
		quit_item.add_accelerator("activate", self.agr,
											key, mod, Gtk.AccelFlags.VISIBLE)
		
		quit_item.connect("activate", self.on_quit_item)
		
		
		file_menu.add(quit_item)
		
		return file_menu_item
		
	
	def add_help_menu(self):
		
		help_menu_item = Gtk.MenuItem(_("Help"))
		help_menu = Gtk.Menu()
		help_menu_item.set_submenu(help_menu)
		
		help_item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_HELP, self.agr)
		key, mod = Gtk.accelerator_parse("F1")
		help_item.add_accelerator("activate", self.agr,
											key, mod, Gtk.AccelFlags.VISIBLE)
		
		help_item.connect("activate", self.on_help_item)
		help_menu.add(help_item)
		
		about_item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_ABOUT, self.agr)
		
		about_item.connect("activate", self.on_about_item)	
		help_menu.add(about_item)
		
		return help_menu_item
		
	
	def on_about_item(self, event):
		
		dialog = AboutDialog()
		
		dialog.run()
	
	def on_help_item(self, event):
		
		print "sorry no help available" #FIXME
	
	def on_quit_item(self, event):
		
		self.list_partitions.quit()
		
	@property
	def get_main_menu(self):
		return self.menu_bar