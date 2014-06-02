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

import blivet

import gettext

import cairo

from utils import *

from dialogs import *

from list_partitions import *

#------------------------------------------------------------------------------#

APP_NAME = "blivet-gui"

dirname, filename = os.path.split(os.path.abspath(__file__))

gettext.bindtextdomain('blivetgui', dirname + '/i18n')
gettext.textdomain('blivetgui')
_ = gettext.gettext

#------------------------------------------------------------------------------#

class ListDevices():
	def __init__(self, main_window, Builder):
		"""
		
		:param main_window: main window instance
		:type main_window: Gtk.Window
		:param Builder: glade builder
		:type Builder: Gtk.Builder
		
		"""
		
		self.main_window = main_window
		
		self.b = BlivetUtils(self.main_window)
		self.builder = Builder
		
		self.device_list = Gtk.ListStore(GdkPixbuf.Pixbuf, str)
		
		self.device_list.append([None,_("<b>Disks</b>")])
		self.load_disks()
		
		self.device_list.append([None,_("<b>LVM2 Physical Volumes</b>")])
		self.load_lvm_physical_volumes()
		
		self.device_list.append([None,_("<b>LVM2 Volume Groups</b>")])
		self.load_lvm_volume_groups()
		
		self.partitions_list = ListPartitions(self.main_window, self, self.b,self.builder)
		
		self.actions_view = self.partitions_list.get_actions_view
		self.partitions_view = self.partitions_list.get_partitions_view
		self.partitions_image = self.partitions_list.create_partitions_image()
		
		self.disks_view = self.create_devices_view()
		
		self.select = self.disks_view.get_selection()
		self.path = self.select.select_path("1")
		
		self.on_disk_selection_changed(self.select)
		self.selection_signal = self.select.connect("changed", self.on_disk_selection_changed)
	
	def load_disks(self):
		""" Load disks
		"""
		
		icon_theme = Gtk.IconTheme.get_default()
		icon_disk = Gtk.IconTheme.load_icon (icon_theme,"drive-harddisk",32, 0)
		icon_disk_usb = Gtk.IconTheme.load_icon (icon_theme,"drive-removable-media",32, 0)
		
		disks = self.b.get_disks()
		
		for disk in disks:
			if disk.removable:
				self.device_list.append([icon_disk_usb,str(disk.name +
											   "\n<i><small>" + disk.model + "</small></i>")])
			else:
				self.device_list.append([icon_disk,str(disk.name +
										   "\n<i><small>" + disk.model + "</small></i>")])
				
	def load_lvm_physical_volumes(self):
		""" Load LVM2 PVs
		"""
		
		icon_theme = Gtk.IconTheme.get_default()
		icon_physical = Gtk.IconTheme.load_icon (icon_theme,"drive-removable-media",32, 0)
		
		pdevices = self.b.get_physical_devices()
		
		for device in pdevices:
			self.device_list.append([icon_physical,str(device.name +
											  "\n<i><small>LVM2 PV</small></i>")])
	
	def load_lvm_volume_groups(self):
		""" Load LVM2 VGs
		"""
		
		gdevices = self.b.get_group_devices()
		
		icon_theme = Gtk.IconTheme.get_default()
		icon_group = Gtk.IconTheme.load_icon (icon_theme,"drive-removable-media",32, 0)
		
		for device in gdevices:
			self.device_list.append([icon_group,str(device.name +
										   "\n<i><small>LVM2 VG</small></i>")])
	
	def load_devices(self):
		""" Load all devices
		"""
		
		self.load_disks()
		self.load_lvm_physical_volumes()
		self.load_lvm_volume_groups()
	
	def update_devices_view(self, action, parent_device, changed_device):
		""" Update device view
		
			:param action: reason to update (delete/add/all)
			:type action: str
			:param parent_device: parent device for device to change
			:type parent device: str
			:param device_changed: added/deleted device
			:type device_changed: str
			
			.. note::

				After removing or adding VGs or PVs it is neccesary to add or remove
				these devices from device list.
				After removing all queud actions it is neccesary to go through list of
				devices and find if they are still in devicetree and also go through
				devicetree and find if those devices are in device list.
				This function will update the Gtk.ListStore.
				
		"""
		
		if action == "all":
			
			pdevices = self.b.get_physical_devices()
			gdevices = self.b.get_group_devices()
			
			for row in self.device_list:
				blivet_device = self.b.get_blivet_device(row[1].split("\n")[0])
				
				if blivet_device == None and row[0] != None:
					self.device_list.remove(row.iter)
					#FIXME need to delete non-existent devices!
				
			icon_theme = Gtk.IconTheme.get_default()
			icon_physical = Gtk.IconTheme.load_icon (icon_theme,"drive-removable-media",32, 0)
			
			for device in pdevices:
				device_is_in = False
				for row in self.device_list:
					if row[1].split("\n")[0] == device.name:
						device_is_in = True
						break
				if not device_is_in:
					row_to_find = _("<b>LVM2 Volume Groups</b>")
					new_row = ([icon_physical,str(device.name +
								   "\n<i><small>LVM2 PV</small></i>")])
				
					for row in self.device_list:
						if row[1] == row_to_find:
							row_to_add_after = row
			
					if row_to_add_after != None:
						self.device_list.insert_before(row_to_add_after.iter, new_row)
			
			for device in gdevices:
				device_is_in = False
				for row in self.device_list:
					if row[1].split("\n")[0] == device.name:
						device_is_in = True
						break
				if not device_is_in:
					self.device_list.append([icon_physical,str(device.name +
												"\n<i><small>LVM2 VG</small></i>")])
		
		elif action == "delete":
			
			row_to_remove = None
			row_to_select = None
			
			for row in self.device_list:
				if row[1].split("\n")[0] == changed_device:
					row_to_remove = row
				elif row[1].split("\n")[0] == parent_device:
					row_to_select = row
		
			if row_to_remove != None:
				self.device_list.remove(row_to_remove.iter)
		
			if row_to_select != None:
				self.select.select_iter(row_to_select.iter)

		elif action == "add":
			row_to_add_after = None
			row_to_select = None
			
			# I want to add new device to appropriate section -> looking for row
			# with section name and adding new row after it
			
			icon_theme = Gtk.IconTheme.get_default()
			icon_physical = Gtk.IconTheme.load_icon (icon_theme,"drive-removable-media",32, 0)

			changed_type = self.b.get_device_type(changed_device)
			
			if changed_type == "lvmvg":
				# new volume group is always last
				new_row = ([icon_physical,str(changed_device + "\n<i><small>LVM2 VG</small></i>")])
				self.device_list.append(new_row)
				
				for row in self.device_list:
					if row[1].split("\n")[0] == changed_device:
						row_to_select = row
			
				if row_to_select != None:
					self.select.select_iter(row_to_select.iter)
			
			elif changed_type == "lvmpv":
				# new physical volume comes before list of vgs
				row_to_find = _("<b>LVM2 Volume Groups</b>")
				new_row = ([icon_physical,str(changed_device + "\n<i><small>LVM2 PV</small></i>")])
			
				for row in self.device_list:
					if row[1] == row_to_find:
						row_to_add_after = row
					elif row[1].split("\n")[0] == changed_device:
						row_to_select = row
			
				if row_to_add_after != None:
					self.device_list.insert_before(row_to_add_after.iter, new_row)
			
				if row_to_select != None:
					self.select.select_iter(row_to_select.iter)
			
			return
				
	def create_devices_view(self):
		""" Create view for devices
		"""
			
		treeview = Gtk.TreeView(model=self.device_list)
		#treeview.set_vexpand(True)
		#treeview.set_hexpand(True)
		
		renderer_pixbuf = Gtk.CellRendererPixbuf()
		column_pixbuf = Gtk.TreeViewColumn(None, renderer_pixbuf, pixbuf=0)
		treeview.append_column(column_pixbuf)
		
		renderer_text = Gtk.CellRendererText()
		column_text = Gtk.TreeViewColumn('Pango Markup', renderer_text, markup=1)
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
			if model[treeiter][1] in ["<b>Disks</b>", "<b>LVM2 Volume Groups</b>",
							 "<b>LVM2 Physical Volumes</b>"]:
				selection.handler_block(self.selection_signal)
				selection.unselect_iter(treeiter)
				selection.handler_unblock(self.selection_signal) 
				selection.select_iter(last)
				treeiter = last
			
			else:
				last = treeiter
			
			disk = model[treeiter][1].split('\n')[0]
			
			self.partitions_list.update_partitions_view(disk)
			self.partitions_list.update_partitions_image(disk)

	def return_device_list(self):
		return self.device_list
	
	def return_actions_view(self):
		return self.actions_view
	
	def return_partitions_view(self):
		return self.partitions_view
	
	def return_partitions_image(self):
		return self.partitions_image
	
	def get_disks_view(self):
		return self.disks_view
	
	def get_partions_list(self):
		return self.partitions_list