# -*- coding: utf-8 -*-
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
#------------------------------------------------------------------------------#

from gi.repository import Gtk, GdkPixbuf

import gettext

import os

from utils import *

from dialogs import *

#------------------------------------------------------------------------------#

APP_NAME = "blivet-gui"

dirname, filename = os.path.split(os.path.abspath(__file__))

gettext.bindtextdomain('blivetgui', dirname + '/i18n')
gettext.textdomain('blivetgui')
_ = gettext.gettext

#------------------------------------------------------------------------------#

class actions_menu():
	def __init__(self,list_partitions):
		self.list_partitions = list_partitions
		self.menu = Gtk.Menu()
		
		# Dict to translate menu item names (str) to menu items (Gtk.MenuItem)
		self.menu_items = {}
		
		self.create_menu()
	
	def create_menu(self):
		""" Create popup menu
		"""
		
		add_item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_ADD, None)
		add_item.set_label(_("New"))
		
		add_item.connect("activate", self.on_add_item)
		add_item.set_sensitive(False)
		self.menu.add(add_item)

		self.menu_items["add"] = add_item
		
		delete_item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_DELETE, None)
		delete_item.set_label(_("Delete"))
		
		delete_item.connect("activate", self.on_delete_item)
		delete_item.set_sensitive(False)
		self.menu.add(delete_item)
		
		self.menu_items["delete"] = delete_item
		
		edit_item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_EDIT, None)
		edit_item.set_label(_("Edit"))
		
		edit_item.connect("activate", self.on_edit_item)
		edit_item.set_sensitive(False)
		self.menu.add(edit_item)
		
		self.menu_items["edit"] = edit_item
		
		self.menu.append(Gtk.SeparatorMenuItem())
		
		umount_item = Gtk.MenuItem()
		umount_item.set_label(_("Unmount"))
		
		umount_item.connect("activate", self.on_umount_item)
		umount_item.set_sensitive(False)
		self.menu.add(umount_item)
		
		self.menu_items["umount"] = umount_item
		
		self.menu.show_all()

	def activate_menu_items(self,menu_item_names):
		""" Activate selected menu items
		
			:param menu_item_names: names of menu items to activate
			:type button_names: list of str
			
        """
		
		for item in menu_item_names:
			self.menu_items[item].set_sensitive(True)
		
	def deactivate_menu_items(self,menu_item_names):
		""" Deactivate selected buttons
		
			:param menu_item_names: names of menu items to activate
			:type button_names: list of str
			
        """
		
		for item in menu_item_names:
			self.menu_items[item].set_sensitive(True)
			
	def deactivate_all(self):
		""" Deactivate all partition based buttons
        """
        
		for item in self.menu_items:
			self.menu_items[item].set_sensitive(False)
	
	def on_add_item(self, event):
		""" Onselect action for add item
		"""
		self.list_partitions.add_partition()
	
	def on_delete_item(self, event):
		""" Onselect action for delete item
		"""
		self.list_partitions.delete_selected_partition()
	
	def on_edit_item(self, event):
		""" Onselect action for edit item
		"""
		self.list_partitions.edit_partition()
	
	def on_umount_item(self, event):
		""" Onselect action for umount item
		"""
		self.list_partitions.umount_partition()
	
	@property
	def get_menu(self):
		return self.menu