# -*- coding: utf-8 -*-
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
#------------------------------------------------------------------------------#

import gettext

from gi.repository import Gtk, GdkPixbuf

from dialogs import *

import os, subprocess

#------------------------------------------------------------------------------#

APP_NAME = "blivet-gui"

dirname, filename = os.path.split(os.path.abspath(__file__))

gettext.bindtextdomain('blivetgui', dirname + '/i18n')
gettext.textdomain('blivetgui')
_ = gettext.gettext

#------------------------------------------------------------------------------#

class main_menu():
	""" Main menu for blivet-gui
	"""

	def __init__(self,main_window,list_partitions,list_devices):
		"""
		
			:param main_window: main window instance
			:type main_window: Gtk.Window
			:list_partitions: list partitions instance
			:type list_partitions: ListPartitions
			
		"""
		
		self.list_partitions = list_partitions
		self.list_devices = list_devices
		self.main_window = main_window
		
		self.menu_bar = Gtk.MenuBar()
		
		self.icon_theme = Gtk.IconTheme.get_default()
		
		self.agr = Gtk.AccelGroup()
		self.main_window.add_accel_group(self.agr)
		
		self.menu_items = {}
		
		self.menu_bar.add(self.add_file_menu())
		self.menu_bar.add(self.add_edit_menu())
		self.menu_bar.add(self.add_partition_menu())
		#self.menu_bar.add(self.add_lvm_menu())
		self.menu_bar.add(self.add_help_menu())
	
	def add_file_menu(self):
		""" Menu item 'File'
		"""
		
		file_menu_item = Gtk.MenuItem(label=_("File"))
		
		file_menu = Gtk.Menu()
		file_menu_item.set_submenu(file_menu)
		
		quit_item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_QUIT, self.agr)
		quit_item.set_label(_("Quit"))
		key, mod = Gtk.accelerator_parse("<Control>Q")
		quit_item.add_accelerator("activate", self.agr,
											key, mod, Gtk.AccelFlags.VISIBLE)
		
		quit_item.connect("activate", self.on_quit_item)
		
		
		file_menu.add(quit_item)
		
		return file_menu_item
	
	def add_edit_menu(self):
		""" Menu item 'Edit'
		"""
		
		edit_menu_item = Gtk.MenuItem(_("Edit"))
		edit_menu = Gtk.Menu()
		edit_menu_item.set_submenu(edit_menu)
		
		undo_item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_UNDO, self.agr)
		undo_item.set_label(_("Undo Last Action"))
		key, mod = Gtk.accelerator_parse("<Control>Z")
		undo_item.add_accelerator("activate", self.agr,
											key, mod, Gtk.AccelFlags.VISIBLE)
		
		undo_item.connect("activate", self.on_undo_item)
		undo_item.set_sensitive(False)
		edit_menu.add(undo_item)
		
		self.menu_items["undo"] = undo_item
		
		redo_item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_REDO, self.agr)
		redo_item.set_label(_("Redo Last Action"))
		key, mod = Gtk.accelerator_parse("<Control><Shift>Z")
		redo_item.add_accelerator("activate", self.agr,
											key, mod, Gtk.AccelFlags.VISIBLE)
		
		redo_item.connect("activate", self.on_redo_item)
		redo_item.set_sensitive(False)
		edit_menu.add(redo_item)
		
		self.menu_items["redo"] = redo_item
		
		clear_item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_CLEAR, self.agr)
		clear_item.set_label(_("Clear Queued Actions"))
		
		clear_item.connect("activate", self.on_clear_item)
		clear_item.set_sensitive(False)
		edit_menu.add(clear_item)
		
		self.menu_items["clear"] = clear_item
		
		apply_item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_APPLY, self.agr)
		apply_item.set_label(_("Apply Queued Actions"))
		key, mod = Gtk.accelerator_parse("<Control>A")
		apply_item.add_accelerator("activate", self.agr,
											key, mod, Gtk.AccelFlags.VISIBLE)
		
		apply_item.connect("activate", self.on_apply_item)
		apply_item.set_sensitive(False)
		edit_menu.add(apply_item)
		
		self.menu_items["apply"] = apply_item
		
		return edit_menu_item
	
	def add_partition_menu(self):
		""" Menu item 'Partition' #FIXME: 'device' menu now
		"""
		
		partition_menu_item = Gtk.MenuItem(_("Device"))
		partition_menu = Gtk.Menu()
		partition_menu_item.set_submenu(partition_menu)
		
		add_item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_ADD, self.agr)
		add_item.set_label(_("New"))
		key, mod = Gtk.accelerator_parse("Insert")
		add_item.add_accelerator("activate", self.agr,
											key, mod, Gtk.AccelFlags.VISIBLE)
		
		add_item.connect("activate", self.on_add_item)
		add_item.set_sensitive(False)
		partition_menu.add(add_item)
		
		self.menu_items["add"] = add_item
		
		delete_item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_DELETE, self.agr)
		delete_item.set_label(_("Delete"))
		key, mod = Gtk.accelerator_parse("Delete")
		delete_item.add_accelerator("activate", self.agr,
											key, mod, Gtk.AccelFlags.VISIBLE)
		
		delete_item.connect("activate", self.on_delete_item)
		delete_item.set_sensitive(False)
		partition_menu.add(delete_item)
		
		self.menu_items["delete"] = delete_item
		
		edit_item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_EDIT, self.agr)
		edit_item.set_label(_("Edit"))
		
		edit_item.connect("activate", self.on_edit_item)
		edit_item.set_sensitive(False)
		partition_menu.add(edit_item)
		
		self.menu_items["edit"] = edit_item
		
		partition_menu.append(Gtk.SeparatorMenuItem())
		
		umount_item = Gtk.MenuItem()
		umount_item.set_label(_("Unmount"))
		
		umount_item.connect("activate", self.on_umount_item)
		umount_item.set_sensitive(False)
		partition_menu.add(umount_item)
		
		self.menu_items["unmount"] = umount_item
		
		decrypt_item = Gtk.MenuItem()
		decrypt_item.set_label(_("Decrypt"))
		
		decrypt_item.connect("activate", self.on_decrypt_item)
		decrypt_item.set_sensitive(False)
		partition_menu.add(decrypt_item)
		
		self.menu_items["decrypt"] = decrypt_item
		
		return partition_menu_item
	
	def add_lvm_menu(self):
		""" Menu item 'LVM'
		"""
		
		lvm_menu_item = Gtk.MenuItem(_("LVM"))
		lvm_menu = Gtk.Menu()
		lvm_menu_item.set_submenu(lvm_menu)
		
		pv_item = Gtk.ImageMenuItem()
		pv_item.set_label(_("Create LVM Physical Volume"))
		
		pv_item.connect("activate", self.on_pv_item)
		pv_item.set_sensitive(True)
		lvm_menu.add(pv_item)
		
		vg_item = Gtk.ImageMenuItem()
		vg_item.set_label(_("Create LVM Volume Group"))
		
		vg_item.connect("activate", self.on_vg_item)
		vg_item.set_sensitive(True)
		lvm_menu.add(vg_item)
		
		return lvm_menu_item

	def add_help_menu(self):
		""" Menu item 'Help'
		"""
		
		help_menu_item = Gtk.MenuItem(_("Help"))
		help_menu = Gtk.Menu()
		help_menu_item.set_submenu(help_menu)
		
		help_item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_HELP, self.agr)
		help_item.set_label(_("Contents"))
		key, mod = Gtk.accelerator_parse("F1")
		help_item.add_accelerator("activate", self.agr,
											key, mod, Gtk.AccelFlags.VISIBLE)
		
		help_item.connect("activate", self.on_help_item)
		help_menu.add(help_item)
		
		about_item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_ABOUT, self.agr)
		about_item.set_label(_("About"))
		
		about_item.connect("activate", self.on_about_item)
		help_menu.add(about_item)
		
		
		return help_menu_item

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
			self.menu_items[item].set_sensitive(False)
			
	def deactivate_all(self):
		""" Deactivate all partition based buttons
        """
        
		for item in self.menu_items:
			if item not in ["apply", "clear", "undo", "redo"]:
				self.menu_items[item].set_sensitive(False)
	
	def on_about_item(self, event):
		""" Onselect action for 'About'
		"""
		
		dialog = AboutDialog(self.main_window)
		
		dialog.run()
	
	def on_help_item(self, event):
		""" Onselect action for 'Help'
		"""
		
		try:
			FNULL = open(os.devnull, "w")
			subprocess.Popen(["yelp", dirname + "/help/C/index.page"],stdout=FNULL, stderr=subprocess.STDOUT)
		
		except Exception as e:
			BlivetError("You need \"Yelp\" to see the documentation.\n" + str(e) + "\n\nOnline version of documentation is available at http://vojtechtrefny.github.io/")
	
	def on_undo_item(self, event):
		""" Onselect action for 'Undo Last Action'
		"""
		
		self.list_partitions.actions_undo()
	
	def on_redo_item(self, event):
		""" Onselect action for 'Redo Last Action'
		"""
		
		self.list_partitions.actions_redo()
		
	def on_clear_item(self, event):
		""" Onselect action for 'Clear Queued Actions'
		"""
		
		self.list_partitions.clear_actions()
		self.list_partitions.clear_actions_view()
	
	def on_apply_item(self, event):
		""" Onselect action for 'Apply Queued Actions'
		"""
		
		self.list_partitions.apply_event()
	
	def on_add_item(self, event):
		""" Onselect action for 'New'
		"""
		
		self.list_partitions.add_partition()
	
	def on_delete_item(self, event):
		""" Onselect action for 'Delete'
		"""
		
		self.list_partitions.delete_selected_partition()
	
	def on_edit_item(self, event):
		""" Onselect action for 'Edit'
		"""
		
		self.list_partitions.edit_partition()
	
	def on_umount_item(self, event):
		""" Onselect action for 'Unmount'
		"""
		
		self.list_partitions.umount_partition()
	
	def on_decrypt_item(self, event):
		""" Onselect action for 'Decrypt'
		"""
		
		self.list_partitions.decrypt_device()
	
	def on_quit_item(self, event):
		""" Onselect action for 'Quit'
		"""
		
		self.list_partitions.quit()
		
	def on_pv_item(self, event):
		
		self.list_devices.add_pv()
	
	def on_vg_item(self, event):
		pass
		
	@property
	def get_main_menu(self):
		return self.menu_bar