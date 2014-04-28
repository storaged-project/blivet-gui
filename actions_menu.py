# actions_menu.py
# Toolbar class
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

from gi.repository import Gtk, GdkPixbuf

import blivet

import gettext

import cairo

from utils import *

from dialogs import *

APP_NAME = "blivet-gui"

gettext.bindtextdomain(APP_NAME, 'po')
gettext.textdomain(APP_NAME)
_ = gettext.gettext

class actions_menu():
	def __init__(self,list_partitions):
		self.list_partitions = list_partitions
		self.menu = Gtk.Menu()
		
		# Dict to translate menu item names (str) to menu items (Gtk.MenuItem)
		self.items = {}
		
		self.create_menu_items()
	
	def create_menu_items(self):
		self.add_menu_item(None,"aaa")
	
	def add_menu_item(self, command, title):
		aMenuitem = Gtk.MenuItem()
		aMenuitem.set_label(title)
		#aMenuitem.connect("activate", command)

		self.menu.append(aMenuitem)
		self.menu.show_all()
	
	@property
	def get_menu(self):
		return self.menu