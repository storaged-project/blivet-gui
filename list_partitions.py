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
	
	def __init__(self,BlivetUtils,Builder,disk=None):
		
		self.b = BlivetUtils
		self.builder = Builder
		
		self.disk = disk
		
		self.PartitionsList = Gtk.ListStore(str,str,str,str)
		self.actions_list = Gtk.ListStore(GdkPixbuf.Pixbuf,str)

		self.LoadPartitions()
		
		self.partitions_view = self.CreatePartitionView()
		self.actions_view = self.create_actions_view()
		
		self.darea = Gtk.DrawingArea()
		
		self.toolbar = actions_toolbar(self)
		
		self.select = self.partitions_view.get_selection()
		self.path = self.select.select_path("1")
		
		self.on_partition_selection_changed(self.select)
		self.selection_signal = self.select.connect("changed", self.on_partition_selection_changed)
		
		self.actions = 0
		self.actions_label = self.builder.get_object("actions_page")
		self.actions_label.set_text(_("Pending actions ({0})").format(self.actions))
		
		self.selected_partition = None
	
	def LoadPartitions(self):
		self.PartitionsList.clear()
		partitions = self.b.GetPartitions(self.disk)
		
		for partition in partitions:
			if partition.name == _("unallocated"):
				self.PartitionsList.append([partition.name,"--","--",str(int(partition.size)) + " MB"])
			elif type(partition) == blivet.devices.PartitionDevice and partition.isExtended:
				self.PartitionsList.append([partition.name,_("extended"),"--",str(int(partition.size)) + " MB"])
			elif partition.format.mountable:
				self.PartitionsList.append([partition.name,partition.format._type,partition.format.mountpoint,str(int(partition.size)) + " MB"])
			else:
				self.PartitionsList.append([partition.name,partition.format._type,"--",str(int(partition.size)) + " MB"])
	
	def UpdatePartitionsView(self,disk):
		
		self.disk = disk
		
		self.PartitionsList.clear()
		partitions = self.b.GetPartitions(self.disk)
		
		for partition in partitions:
			if partition.name == _("unallocated"):
				self.PartitionsList.append([partition.name,"--","--",str(int(partition.size)) + " MB"])
			elif type(partition) == blivet.devices.PartitionDevice and partition.isExtended:
				self.PartitionsList.append([partition.name,_("extended"),"--",str(int(partition.size)) + " MB"])
			elif partition.format.mountable:
				self.PartitionsList.append([partition.name,partition.format._type,partition.format.mountpoint,str(int(partition.size)) + " MB"])
			else:
				self.PartitionsList.append([partition.name,partition.format._type,"--",str(int(partition.size)) + " MB"])

			
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
		""" Drawing event for partition visualisation
			:param da: drawing area
			:type da: Gtk.DrawingArea
            :param cairo_ctx: Cairo context
            :type cairo_ctx: Cairo.Context
            :param partitions: list of partitions to paint
            :type partitions: Gtk.ListStore
        """
		width = da.get_allocated_width()
		height = da.get_allocated_height()
		
		total_size = 0
		num_parts = 0
		
		cairo_ctx.set_source_rgb(1,1,1)
		cairo_ctx.paint()
		
		extended = False
		
		for partition in partitions:
			
			if partition[1] == _("extended"):
				cairo_ctx.set_source_rgb(0,1,1)
				# Teal color for extend partition
				
				cairo_ctx.rectangle(0, 0, width, height)
				cairo_ctx.fill()
				extended = True
			
			else:
				total_size += int(partition[3].split()[0])
				num_parts += 1		
		
		# Safe space for extended partition borders
		if extended:
			x = 5
			y = 5
		
		else:
			x = 0
			y = 0
		
		# Colors for partitions
		colors = [[0.451,0.824,0.086],
			[0.961,0.474,0],
			[0.204,0.396,0.643]]
		
		i = 0
		
		for partition in partitions:
			
			if partition[1] == _("extended"):
				continue
			
			if partition[0] == _("unallocated"):
				cairo_ctx.set_source_rgb(0.75, 0.75, 0.75)
				# Grey color for unallocated space
			
			else:
				cairo_ctx.set_source_rgb(colors[i % 3][0] , colors[i % 3][1], colors[i % 3][2])
				# Colors for other partitions/devices
			
			part_width = int(partition[3].split()[0])*(width - 2*y)/total_size
			
			# Every partition need some minimum size in the drawing area
			# Minimum size = number of partitions*2 / width of draving area
			if part_width < (width - 2*y) / (num_parts*2):
				part_width = (width - 2*y) / (num_parts*2)
			
			if part_width > (width - 2*y) - ((num_parts-1)* ((width - 2*y) / (num_parts*2))):
				part_width = (width - 2*y) - (num_parts-1) * ((width - 2*y) / (num_parts*2))

			cairo_ctx.rectangle(x, y, part_width, height - 2*y)
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
	
	def create_partitions_image(self):
		""" Create drawing area
			:returns: drawing area
			:rtype: Gtk.DrawingArea
        """
		
		partitions = self.PartitionsList
		
		self.darea.connect('draw', self.draw_event, partitions)
		
		return self.darea
	
	def update_partitions_image(self,device):
		""" Update drawing area for newly selected device
			:param device: selected device
			:param type: str
        """
		
		self.disk = device
		partitions = self.PartitionsList
		
		self.darea.queue_draw()
		
	def create_actions_view(self):
			
		treeview = Gtk.TreeView(model=self.actions_list)
		treeview.set_vexpand(True)
		treeview.set_hexpand(True)
		
		renderer_pixbuf = Gtk.CellRendererPixbuf()
		column_pixbuf = Gtk.TreeViewColumn(None, renderer_pixbuf, pixbuf=0)
		treeview.append_column(column_pixbuf)
		
		renderer_text = Gtk.CellRendererText()
		column_text = Gtk.TreeViewColumn(None, renderer_text, text=1)
		treeview.append_column(column_text)
		
		treeview.set_headers_visible(False)
	
		return treeview
	
	def clear_actions_view(self):
		""" Delete all actions in actions view
        """
		
		self.actions = 0
		self.actions_label.set_text(_("Pending actions ({0})").format(self.actions))
		self.action_list.clear()
		
		self.toolbar.deactivate_buttons(["apply"])
	
	def update_actions_view(self,action_type=None,action_desc=None):
		""" Update list of scheduled actions
			:param action_type: type of action (delete/add/edit)
			:type action_type: str
            :param action_desc: description of scheduled action
            :type partition_name: str
        """
		
		icon_theme = Gtk.IconTheme.get_default()
		icon_add = Gtk.IconTheme.load_icon (icon_theme,"gtk-add",16, 0)
		icon_delete = Gtk.IconTheme.load_icon (icon_theme,"gtk-delete",16, 0)
		icon_edit = Gtk.IconTheme.load_icon (icon_theme,"gtk-edit",16, 0)
		
		action_icons = {"add" : icon_add, "delete" : icon_delete, "edit" : icon_edit}
		
		self.actions_list.append([action_icons[action_type], action_desc])
		
		# Update number of actions on actions card label
		self.actions += 1
		self.actions_label.set_text(_("Pending actions ({0})").format(self.actions))
		
		self.toolbar.activate_buttons(["apply"])
	
	def activate_action_buttons(self,selected_partition):
		""" Activate buttons in toolbar based on selected partition
			:param selected_partition: Selected partition
			:type selected_partition: Gtk.TreeModelRow
        """
		
		partition_device = self.b.storage.devicetree.getDeviceByName(selected_partition[0])
		
		if selected_partition == None or (partition_device == None and selected_partition[0] != _("unallocated")):
			self.toolbar.deactivate_all()
			return
		
		if selected_partition[0] == _("unallocated"):
			self.toolbar.deactivate_all()
			self.toolbar.activate_buttons(["add"])
		
		elif selected_partition[1] == _("extended"):
			self.toolbar.deactivate_all()
			self.toolbar.activate_buttons(["delete"])
		
		else:
			self.toolbar.deactivate_all()
			if partition_device.format.mountable and partition_device.format.mountpoint == None:
				self.toolbar.activate_buttons(["delete"])
			
			#FIXME detect resizable
			#self.toolbar.activate_buttons(["delete","edit"])
	
	def delete_selected_partition(self):
		
		dialog = ConfirmDeleteDialog(self.selected_partition[0])
		response = dialog.run()

		if response == Gtk.ResponseType.OK:
            
			self.b.delete_device(self.selected_partition[0])
			
			self.update_actions_view("delete",_("delete partition {0}").format(self.selected_partition[0]))
			
			self.selected_partition = None
			
		elif response == Gtk.ResponseType.CANCEL:
			pass

		dialog.destroy()
        
		self.UpdatePartitionsView(self.disk)
		self.update_partitions_image(self.disk)
		
	
	def on_partition_selection_changed(self,selection):
		
		model, treeiter = selection.get_selected()
		
		self.toolbar.deactivate_all()
		
		if treeiter != None:
			#FIXME -- need to pass more details if unallocated #TODO possibly add ID for unallocated
			self.activate_action_buttons(model[treeiter])
			self.selected_partition = model[treeiter]
			
	
	def ReturnPartitionsList(self):
		return self.PartitionsList
	
	@property
	def get_partitions_view(self):
		return self.partitions_view
	
	@property
	def get_actions_view(self):
		return self.actions_view
	
	@property
	def get_toolbar(self):
		return self.toolbar.get_toolbar()
	
	@property
	def get_actions_label(self):
		return self.actions_label

#-----------------------------------------------------#