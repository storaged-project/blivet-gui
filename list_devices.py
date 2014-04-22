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


import sys, os, signal

from gi.repository import Gtk, GdkPixbuf

import blivet

import gettext

import cairo

from utils import *

from dialogs import *

from list_partitions import *

APP_NAME = "blivet-gui"

gettext.bindtextdomain(APP_NAME, 'po')
gettext.textdomain(APP_NAME)
_ = gettext.gettext


class ListDevices():
	def __init__(self,BlivetUtils):
		
		self.b = BlivetUtils
		
		self.DeviceList = Gtk.ListStore(GdkPixbuf.Pixbuf, str)
		
		self.DeviceList.append([None,_("Disk Devices")])
		self.LoadDisks()
		
		self.DeviceList.append([None,_("Group Devices")])
		self.LoadGroupDevices()
		
		self.partions_list = ListPartitions(self.b)
		
		self.partitions_view = self.partions_list.get_partitions_view()
		self.partitions_image = self.partions_list.CreatePartitionImage()
		
		self.disks_view = self.CreateDeviceView()
		
		self.select = self.disks_view.get_selection()
		self.path = self.select.select_path("1")
		
		self.on_disk_selection_changed(self.select)
		self.selection_signal = self.select.connect("changed", self.on_disk_selection_changed)
	
	def LoadDisks(self):
		
		icon_theme = Gtk.IconTheme.get_default()
		icon_disk = Gtk.IconTheme.load_icon (icon_theme,"drive-harddisk",32, 0)
		icon_disk_usb = Gtk.IconTheme.load_icon (icon_theme,"drive-removable-media",32, 0)
		
		disks = self.b.GetDisks()
		
		for disk in disks:
			if disk.removable:
				self.DeviceList.append([icon_disk_usb,str(disk.name + "\n" + disk.model)])
			else:
				self.DeviceList.append([icon_disk,str(disk.name + "\n" + disk.model)])
	
	def LoadGroupDevices(self):
		
		gdevices = self.b.GetGroupDevices()
		
		icon_theme = Gtk.IconTheme.get_default()
		icon_group = Gtk.IconTheme.load_icon (icon_theme,"drive-removable-media",32, 0)
		
		for device in gdevices:
			self.DeviceList.append([icon_group,str(device.name + "\n")])
	
	def LoadDevices(self):
		
		self.LoadDisks()
		self.LoadGroupDevices()
				
	def CreateDeviceView(self):
			
		treeview = Gtk.TreeView(model=self.DeviceList)
		#treeview.set_vexpand(True)
		#treeview.set_hexpand(True)
		
		renderer_pixbuf = Gtk.CellRendererPixbuf()
		column_pixbuf = Gtk.TreeViewColumn(None, renderer_pixbuf, pixbuf=0)
		treeview.append_column(column_pixbuf)
		
		renderer_text = Gtk.CellRendererText()
		column_text = Gtk.TreeViewColumn(None, renderer_text, text=1)
		treeview.append_column(column_text)
		
		treeview.set_headers_visible(False)
	
		return treeview
	
	def on_disk_selection_changed(self,selection):
		
		global last
		
		model, treeiter = selection.get_selected()
		
		if treeiter != None:
			
			if model[treeiter][1] == "Disk Devices" or model[treeiter][1] == "Group Devices":
				selection.handler_block(self.selection_signal)
				selection.unselect_iter(treeiter)
				selection.handler_unblock(self.selection_signal) 
				selection.select_iter(last)
				treeiter = last
			else:
				last = treeiter
			
			disk = model[treeiter][1].split('\n')[0]
			self.partions_list.UpdatePartitionsView(disk)
			self.partions_list.UpdatePartitionsImage(disk)
			
	
	def ReturnDeviceList(self):
		return self.DeviceList
	
	def return_partitions_view(self):
		return self.partitions_view
	
	def return_partitions_image(self):
		return self.partitions_image
	
	def get_disks_view(self):
		return self.disks_view
	
	def get_partions_list(self):
		return self.partions_list

