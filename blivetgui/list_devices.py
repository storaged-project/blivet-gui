# -*- coding: utf-8 -*-
# list_devices.py
# Load and display root and group devices
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

from gi.repository import Gtk, GdkPixbuf

import gettext

from utils import *

from dialogs import kickstart_dialogs, message_dialogs

from list_partitions import *

#------------------------------------------------------------------------------#

APP_NAME = "blivet-gui"

dirname, filename = os.path.split(os.path.abspath(__file__))

gettext.bindtextdomain('blivetgui', dirname + '/i18n')
gettext.textdomain('blivetgui')
_ = gettext.gettext

#------------------------------------------------------------------------------#

class ListDevices():
	def __init__(self, main_window, Builder, kickstart=False):
		"""
		
		:param main_window: main window instance
		:type main_window: Gtk.Window
		:param Builder: glade builder
		:type Builder: Gtk.Builder
		:param kickstart: use blivet-gui in kickstart mode
		:type kickstart: bool
		
		"""
		
		self.main_window = main_window
		
		self.b = BlivetUtils(self.main_window, kickstart)
		self.builder = Builder
		
		self.kickstart_mode = kickstart
		
		if self.kickstart_mode:

			disks = self.b.get_disks()

			if len(disks) == 0:
				msg = _("blivet-gui failed to find at least one storage device to work with.\
					\n\nPlease connect a storage device to your computer and re-run blivet-gui.")
				message_dialogs.WarningDialog(self.main_window, msg)
				sys.exit(0)

			dialog = kickstart_dialogs.KickstartSelectDevicesDialog(self.main_window, disks)
			response = dialog.run()
			
			if response == Gtk.ResponseType.OK:
				self.use_disks, self.install_bootloader, self.bootloader_device = dialog.get_selection()
				dialog.destroy()
				
				if self.install_bootloader and self.bootloader_device:
					self.b.set_bootloader_device(self.bootloader_device)
				
			else:
				dialog.destroy()
				sys.exit(0)
			
			self.b.kickstart_use_disks(self.use_disks)
			
			self.old_mountpoints = self.b.kickstart_mountpoints()
		
		self.device_list = Gtk.ListStore(object, GdkPixbuf.Pixbuf, str)
		num_devices = self.load_devices()

		
		if num_devices:

			self.partitions_list = ListPartitions(self.main_window, self, self.b,self.builder, kickstart_mode=self.kickstart_mode)
			self.disks_view = self.create_devices_view()

			self.select = self.disks_view.get_selection()
			self.path = self.select.select_path("1")

			self.on_disk_selection_changed(self.select)
			self.selection_signal = self.select.connect("changed", self.on_disk_selection_changed)

			self.builder.get_object("disks_viewport").add(self.disks_view)

		else:

			msg = _("blivet-gui failed to find at least one storage device to work with.\
				\n\nPlease connect a storage device to your computer and re-run blivet-gui.")
			message_dialogs.WarningDialog(self.main_window, msg)
			sys.exit(0)

	
	def load_disks(self):
		""" Load disks
		"""
		
		icon_theme = Gtk.IconTheme.get_default()
		icon_disk = Gtk.IconTheme.load_icon (icon_theme,"drive-harddisk",32, 0)
		icon_disk_usb = Gtk.IconTheme.load_icon (icon_theme,"drive-removable-media",32, 0)
		
		disks = self.b.get_disks()

		if disks:
			self.device_list.append([None,None,_("<b>Disks</b>")])
		
		for disk in disks:
			
			if disk.removable:
				self.device_list.append([disk,icon_disk_usb,str(disk.name +
											   "\n<i><small>" + disk.model + "</small></i>")])
			else:
				self.device_list.append([disk,icon_disk,str(disk.name +
										   "\n<i><small>" + disk.model + "</small></i>")])
		
		return len(disks)
				
	def load_lvm_physical_volumes(self):
		""" Load LVM2 PVs
		"""
		
		icon_theme = Gtk.IconTheme.get_default()
		icon_physical = Gtk.IconTheme.load_icon (icon_theme,"drive-removable-media",32, 0)
		
		pdevices = self.b.get_physical_devices()

		if pdevices:
			self.device_list.append([None,None,_("<b>LVM2 Physical Volumes</b>")])
		
		for device in pdevices:
			
			self.device_list.append([device,icon_physical,str(device.name +
											  "\n<i><small>LVM2 PV</small></i>")])
		
		return len(pdevices)

	def load_lvm_volume_groups(self):
		""" Load LVM2 VGs
		"""
		
		gdevices = self.b.get_group_devices()

		if gdevices:
			self.device_list.append([None,None,_("<b>LVM2 Volume Groups</b>")])
		
		icon_theme = Gtk.IconTheme.get_default()
		icon_group = Gtk.IconTheme.load_icon (icon_theme,"drive-removable-media",32, 0)
		
		for device in gdevices:
			self.device_list.append([device,icon_group,str(device.name +
										   "\n<i><small>LVM2 VG</small></i>")])
		
		return len(gdevices)

	def load_devices(self):
		""" Load all devices
		"""
		self.device_list.clear()
		
		devices = 0

		devices += self.load_disks()
		devices += self.load_lvm_physical_volumes()
		devices += self.load_lvm_volume_groups()

		return devices
	
	def update_devices_view(self):
		""" Update device view
		"""
		
		# remember previously selected device name
		selection = self.disks_view.get_selection()
		model, treeiter = selection.get_selected()
		if treeiter != None and model != None:
			selected_device = model[treeiter][0].name
		
		# reload devices
		self.load_devices()
		
		# if the device still exists, select it; else select first device in list
		i = 0
		selected = False
		
		for device in self.device_list:
			
			if device[0] != None and device[0].name == selected_device:
				self.disks_view.set_cursor(i)
				selected = True
			
			i += 1
			
		if not selected:
			self.disks_view.set_cursor(1)		
				
	def create_devices_view(self):
		""" Create view for devices
		"""
			
		treeview = Gtk.TreeView(model=self.device_list)
		
		renderer_pixbuf = Gtk.CellRendererPixbuf()
		column_pixbuf = Gtk.TreeViewColumn(None, renderer_pixbuf, pixbuf=1)
		treeview.append_column(column_pixbuf)
		
		renderer_text = Gtk.CellRendererText()
		column_text = Gtk.TreeViewColumn('Pango Markup', renderer_text, markup=2)
		treeview.append_column(column_text)
		
		treeview.set_headers_visible(False)
	
		return treeview
	
	def on_disk_selection_changed(self,selection):
		""" Onselect action for devices
		"""
		
		# Last selected device from list
		global last
		
		model, treeiter = selection.get_selected()
		
		if treeiter != None and model != None:
			
			# 'Disks', 'LVM2 Volume Groups' and 'LVM2 Physical Volumes' are just labels
			# If user select one of these, we need to unselect this and select previous choice
			if model[treeiter][0] == None:
				selection.handler_block(self.selection_signal)
				selection.unselect_iter(treeiter)
				selection.handler_unblock(self.selection_signal) 
				selection.select_iter(last)
				treeiter = last
			
			else:
				last = treeiter
			
			if self.device_list.iter_is_valid(treeiter):
				disk = model[treeiter][0]
			
				self.partitions_list.update_partitions_view(disk)
		
	def return_device_list(self):
		return self.device_list
	
	def get_disks_view(self):
		return self.disks_view
	
	def get_partions_list(self):
		return self.partitions_list