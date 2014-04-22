# list_partitions.py
# Load and display partitions for selected device
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

from actions_toolbar import *

APP_NAME = "blivet-gui"

gettext.bindtextdomain(APP_NAME, 'po')
gettext.textdomain(APP_NAME)
_ = gettext.gettext


class ListPartitions():
	
	def __init__(self,BlivetUtils,disk=None):
		
		self.b = BlivetUtils
		
		self.disk = disk
		
		self.PartitionsList = Gtk.ListStore(str,str,str,str)

		self.LoadPartitions()
		
		self.partitions_view = self.CreatePartitionView()
		
		self.darea = Gtk.DrawingArea()
		
		self.toolbar = actions_toolbar(self)
		
		self.select = self.partitions_view.get_selection()
		self.path = self.select.select_path("1")
		
		self.on_partition_selection_changed(self.select)
		self.selection_signal = self.select.connect("changed", self.on_partition_selection_changed)
	
	def LoadPartitions(self):
		self.PartitionsList.clear()
		partitions = self.b.GetPartitions(self.disk)
		
		for partition in partitions:
			if partition.name == _("unallocated"):
				self.PartitionsList.append([partition.name,"--","--",str(int(partition.size)) + " MB"])
			elif partition.format.mountable:
				self.PartitionsList.append([partition.format.device,partition.format._type,partition.format.mountpoint,str(int(partition.size)) + " MB"])
			else:
				self.PartitionsList.append([partition.format.device,partition.format._type,"",str(int(partition.size)) + " MB"])
	
	def UpdatePartitionsView(self,disk):
		
		self.disk = disk
		
		self.PartitionsList.clear()
		partitions = self.b.GetPartitions(self.disk)
		
		for partition in partitions:
			if partition.name == _("unallocated"):
				self.PartitionsList.append([partition.name,"--","--",str(int(partition.size)) + " MB"])
			elif partition.format.mountable:
				self.PartitionsList.append([partition.format.device,partition.format._type,partition.format.mountpoint,str(int(partition.size)) + " MB"])
			else:
				self.PartitionsList.append([partition.format.device,partition.format._type,"",str(int(partition.size)) + " MB"])

			
	def CreatePartitionView(self):
	
		if self.disk == None:
			partitions = self.PartitionsList
		
		else:
			self.LoadPartitions()
			partitions = self.PartitionsList
			
		treeview = Gtk.TreeView(model=partitions)
		treeview.set_vexpand(True)
		#treeview.set_hexpand(True)
		
		renderer_text = Gtk.CellRendererText()
		
		column_text1 = Gtk.TreeViewColumn(_("Partition"), renderer_text, text=0)
		column_text2 = Gtk.TreeViewColumn(_("Filesystem"), renderer_text, text=1)
		column_text3 = Gtk.TreeViewColumn(_("Mountpoint"), renderer_text, text=2)
		column_text4 = Gtk.TreeViewColumn(_("Size"), renderer_text, text=3)
		
		treeview.append_column(column_text1)
		treeview.append_column(column_text2)
		treeview.append_column(column_text3)
		treeview.append_column(column_text4)
		
		treeview.set_headers_visible(True)
		
		return treeview
	
	def draw_event(self, da, cairo_ctx, partitions):
		width = da.get_allocated_width()
		height = da.get_allocated_height()
		
		total_size = 0
		num_parts = 0
		
		for partition in partitions:
			total_size += int(partition[3].split()[0])
			num_parts += 1
		
		cairo_ctx.set_source_rgb(1,1,1)
		cairo_ctx.paint()
		
		
		x = 0
		
		colors = [[0.451,0.824,0.086],
			[0.961,0.474,0],
			[0.204,0.396,0.643]]
		
		i = 0
		
		for partition in partitions:
			
			if partition[0] == _("unallocated"):
				cairo_ctx.set_source_rgb(0.75, 0.75, 0.75)
				# Grey color for unallocated space
			
			else:
				cairo_ctx.set_source_rgb(colors[i % 3][0] , colors[i % 3][1], colors[i % 3][2])
				# Colors for other partitions/devices
			
			part_width = int(partition[3].split()[0])*width/total_size
			
			# Every partition need some minimum size in the drawing area
			# Minimum size = number of partitions*2 / width of draving area
			if part_width < width / (num_parts*2):
				part_width = width / (num_parts*2)
			
			if part_width > width - ((num_parts-1)* (width / (num_parts*2))):
				part_width = width - (num_parts-1) * (width / (num_parts*2))

			cairo_ctx.rectangle(x, 0, part_width, height)
			cairo_ctx.fill()
			
			cairo_ctx.set_source_rgb(0, 0, 0)
			cairo_ctx.select_font_face ("Sans",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_NORMAL);
			cairo_ctx.set_font_size(10)
			
			# Print name of partition
			cairo_ctx.move_to(x + 12, height/2)
			cairo_ctx.show_text(partition[0])
			
			# Print size of partition
			cairo_ctx.move_to(x + 12 , height/2 + 12)
			cairo_ctx.show_text(partition[3])
			
			
			x += part_width
			i += 1
		
		return True
	
	def CreatePartitionImage(self):
		
		partitions = self.PartitionsList
		
		self.darea.connect('draw', self.draw_event, partitions)
		
		return self.darea
	
	def UpdatePartitionsImage(self,disk):
		
		self.disk = disk
		
		partitions = self.PartitionsList
		
		self.darea.queue_draw()
	
	def activate_action_buttons(self,selected_partition):
		
		if selected_partition == _("unallocated"):
			self.toolbar.deactivate_all()
			self.toolbar.activate_buttons(["new"])
		
		else:
			#FIXME detect mounted/resizable
			self.toolbar.deactivate_all()
			self.toolbar.activate_buttons(["delete","edit"])
		
	
	def on_partition_selection_changed(self,selection):
		
		global last
		
		model, treeiter = selection.get_selected()
		
		self.toolbar.deactivate_all()
		
		if treeiter != None:
			
			#FIXME -- need to pass more details if unallocated #TODO possibly add ID for unallocated
			self.activate_action_buttons(model[treeiter][0])
			
	
	def ReturnPartitionsList(self):
		return self.PartitionsList
	
	def get_partitions_view(self):
		return self.partitions_view
	
	def get_toolbar(self):
		return self.toolbar.get_toolbar()

#-----------------------------------------------------#