# -*- coding: utf-8 -*-
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
#------------------------------------------------------------------------------#

import sys, os, signal

from gi.repository import Gtk, GdkPixbuf, Gdk, GLib

import blivet

import gettext

import cairo

from utils import *

from dialogs import *

from actions_toolbar import *

from actions_menu import *

from main_menu import *

from processing_window import *

#------------------------------------------------------------------------------#

APP_NAME = "blivet-gui"

dirname, filename = os.path.split(os.path.abspath(__file__))

gettext.bindtextdomain('blivetgui', dirname + '/i18n')
gettext.textdomain('blivetgui')
_ = gettext.gettext

#------------------------------------------------------------------------------#

class ListPartitions():
	
	def __init__(self,ListDevices,BlivetUtils,Builder,disk=None):
		
		GLib.threads_init()
		Gdk.threads_init()
		Gdk.threads_enter()
		
		self.list_devices = ListDevices
		self.b = BlivetUtils
		self.builder = Builder
		
		self.disk = disk
		
		# ListStores for partitions and actions
		self.partitions_list = Gtk.ListStore(str,str,str,str)
		self.actions_list = Gtk.ListStore(GdkPixbuf.Pixbuf,str)

		self.load_partitions()
		
		self.partitions_view = self.create_partitions_view()
		self.actions_view = self.create_actions_view()
		
		self.info_label = Gtk.Label("")
		self.builder.get_object("pv_viewport").add(self.info_label)
		
		self.darea = Gtk.DrawingArea()
		
		self.main_menu = main_menu(self.builder.get_object("MainWindow"),self,self.list_devices)		
		self.popup_menu = actions_menu(self)
		self.toolbar = actions_toolbar(self)
		
		self.select = self.partitions_view.get_selection()
		self.path = self.select.select_path("1")
		
		self.on_partition_selection_changed(self.select)
		self.selection_signal = self.select.connect("changed", self.on_partition_selection_changed)
		
		self.actions = 0
		self.actions_label = self.builder.get_object("actions_page")
		self.actions_label.set_text(_("Pending actions ({0})").format(self.actions))
		
		self.partitions_label = self.builder.get_object("partitions_page")
		self.partitions_label.set_text(_("Partitions").format(self.actions))
		
		self.selected_partition = None
	
	def load_partitions(self):
		""" Load children devices (partitions) for selected disk (root/group device)
        """
        
		self.partitions_list.clear()
		partitions = self.b.get_partitions(self.disk)
		
		for partition in partitions:
			if partition.name == _("free space"):
				self.partitions_list.append([partition.name,"--","--",
								 str(int(partition.size)) + " MB"])
			elif type(partition) == blivet.devices.PartitionDevice and partition.isExtended:
				self.partitions_list.append([partition.name,_("extended"),"--",
								 str(int(partition.size)) + " MB"])
			elif partition._type == "lvmvg":
				self.partitions_list.append([partition.name,_("lvmvg"),"--",
								 str(int(partition.size)) + " MB"])
			elif partition.format.mountable:
				self.partitions_list.append([partition.name,partition.format._type,
								 partition.format.mountpoint,str(int(partition.size)) + " MB"])
			else:
				self.partitions_list.append([partition.name,partition.format._type,"--",
								 str(int(partition.size)) + " MB"])
	
	def device_info(self):
		""" Basic information for selected device	
		"""
		
		device_type = self.b.get_device_type(self.disk)
		
		if device_type == "lvmvg":
			pvs = self.b.get_parent_pvs(self.disk)
		
			info_str = _("<b>LVM2 Volume group <i>{0}</i> occupying {1} Physical Volume(s):</b>\n\n").format(self.disk, len(pvs))
		
			for pv in pvs:
				info_str += _("\t• PV <i>{0}</i>, size: {1} MB on <i>{2}</i> disk.\n").format(pv.name, pv.size, pv.disks[0].name)
		
		elif device_type in ["lvmpv", "luks/dm-crypt"]:
			blivet_device = self.b.get_blivet_device(self.disk)
			
			if blivet_device.format._type == "lvmpv":
				info_str = _("<b>LVM2 Physical Volume</b>").format()
			
			else:
				info_str = ""
		
		elif device_type == "disk":
			
			blivet_disk = self.b.get_blivet_device(self.disk)
			
			info_str = _("<b>Hard disk</b> <i>{0}</i>\n\n\t• Size: <i>{1} MB</i>\n\t• Model: <i>{2}</i>\n").format(blivet_disk.path, blivet_disk.size, blivet_disk.model)

		else:
			info_str = ""
		
		self.info_label.set_markup(info_str)
		
		return		
	
	def update_partitions_view(self,device_name):
		""" Update partition view with selected disc children (partitions)
		
			:param device_name: name of selected device 
			:type device_name: str
			
        """
		
		self.disk = device_name
		
		self.device_info()
		
		self.partitions_list.clear()
		partitions = self.b.get_partitions(self.disk)
		
		for partition in partitions:
			
			if partition.name == _("free space"):
				self.partitions_list.append([partition.name,"--","--",
								 str(int(partition.size)) + " MB"])
			elif type(partition) == blivet.devices.PartitionDevice and partition.isExtended:
				self.partitions_list.append([partition.name,_("extended"),"--",
								 str(int(partition.size)) + " MB"])
			elif partition._type == "lvmvg":
				self.partitions_list.append([partition.name,_("lvmvg"),"--",
								 str(int(partition.size)) + " MB"])
			elif partition.format.mountable:
				self.partitions_list.append([partition.name,partition.format._type,
								 partition_mounted(partition.path),str(int(partition.size)) + " MB"])
			else:
				self.partitions_list.append([partition.name,partition.format._type,"--",
								 str(int(partition.size)) + " MB"])
		
		# select first line in partitions view
		self.select = self.partitions_view.get_selection()
		self.path = self.select.select_path("0")

	def create_partitions_view(self):
		""" Create Gtk.TreeView for device children (partitions)
        """
        
		if self.disk == None:
			partitions = self.partitions_list
		
		else:
			self.load_partitions()
			partitions = self.partitions_list
			
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
		
		treeview.connect("button-release-event" , self.on_right_click_event)
		
		return treeview
	
	def on_right_click_event(self,treeview, event):
		""" Right click event on partition treeview
		"""
		
		if event.button == 3:
			
			selection = treeview.get_path_at_pos(int(event.x), int(event.y))
			
			if selection == None:
				return False
			
			path = selection[0]
			treemodel = treeview.get_model()
			treeiter = treemodel.get_iter(path)
			
			self.popup_menu.get_menu.popup(None, None, None, None, event.button, event.time)
			
			return True
	
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
				pass
			
			else:
				total_size += int(partition[3].split()[0])
				num_parts += 1	
		
		# Colors for partitions
		colors = [[0.451,0.824,0.086],
			[0.961,0.474,0],
			[0.204,0.396,0.643]]
		
		i = 0
		
		shrink = 0
		x = 0
		y = 0
		
		for partition in partitions:
			
			if extended:
				shrink = 5
				x += 5
				y = 5
				
			
			if partition[1] == _("extended"):
				# Teal color for extend partition
				cairo_ctx.set_source_rgb(0,1,1)
				
				extended = True
			
			elif partition[0] == _("free space"):
				cairo_ctx.set_source_rgb(0.75, 0.75, 0.75)
				# Grey color for unallocated space
				
				extended = False
			
			else:
				cairo_ctx.set_source_rgb(colors[i % 3][0] , colors[i % 3][1], colors[i % 3][2])
				# Colors for other partitions/devices
				
				extended = False
			
			part_width = int(partition[3].split()[0])*(width - 2*shrink)/total_size
			
			#print part_width, partition[0]
			
			# Every partition need some minimum size in the drawing area
			# Minimum size = number of partitions*2 / width of draving area
			if extended:
				pass
			
			elif part_width < (width - 2*shrink) / (num_parts*2):
				part_width = (width - 2*shrink) / (num_parts*2)
			
			elif part_width > (width - 2*shrink) - ((num_parts-1)* ((width - 2*shrink) / (num_parts*2))):
				part_width = (width - 2*shrink) - (num_parts-1) * ((width - 2*shrink) / (num_parts*2))
			
			elif x + part_width > width and not extended:
				part_width = (width - x - shrink)

			cairo_ctx.rectangle(x, shrink, part_width, height - 2*shrink)
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
			
			if not extended:
				x += part_width
			i += 1
		
		return True
	
	def button_press_event(self, da, event):
		""" Button press event for partition image
		"""
		
		#print "clicked on", event.x, "|", event.y
		
		return True
	
	def create_partitions_image(self):
		""" Create drawing area
		
			:returns: drawing area
			:rtype: Gtk.DrawingArea
			
        """
		
		partitions = self.partitions_list
		
		self.darea.connect('draw', self.draw_event, partitions)
		self.darea.connect('button-press-event', self.button_press_event)
		
		# Ask to receive events the drawing area doesn't normally
		# subscribe to
		self.darea.set_events(self.darea.get_events()
				| Gdk.EventMask.LEAVE_NOTIFY_MASK
				| Gdk.EventMask.BUTTON_PRESS_MASK
				| Gdk.EventMask.POINTER_MOTION_MASK
				| Gdk.EventMask.POINTER_MOTION_HINT_MASK)
		
		return self.darea
	
	def update_partitions_image(self,device):
		""" Update drawing area for newly selected device
		
			:param device: selected device
			:param type: str
			
        """
		
		self.disk = device
		partitions = self.partitions_list
		
		self.darea.queue_draw()
		
	def create_actions_view(self):
		""" Create treeview for actions
		
			:returns: treeview
			:rtype: Gtk.TreeView
			
        """
			
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
		self.actions_list.clear()
		
		self.toolbar.deactivate_buttons(["apply", "clear"])
		self.main_menu.deactivate_menu_items(["apply", "clear"])
		
		self.update_partitions_view(self.disk)
		self.update_partitions_image(self.disk)
	
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
		
		self.toolbar.activate_buttons(["apply", "clear"])
		self.main_menu.activate_menu_items(["apply", "clear"])
	
	def activate_action_buttons(self,selected_partition):
		""" Activate buttons in toolbar based on selected partition
		
			:param selected_partition: Selected partition
			:type selected_partition: Gtk.TreeModelRow
			
        """
		
		partition_device = self.b.storage.devicetree.getDeviceByName(selected_partition[0])
		
		if selected_partition == None or (partition_device == None and selected_partition[0] != _("free space")):
			self.toolbar.deactivate_all()
			self.main_menu.deactivate_all()
			self.popup_menu.deactivate_all()
			return
		
		if selected_partition[0] == _("free space"):			
			self.toolbar.deactivate_all()
			self.toolbar.activate_buttons(["add"])
			
			self.main_menu.deactivate_all()
			self.main_menu.activate_menu_items(["add"])
			
			self.popup_menu.deactivate_all()
			self.popup_menu.activate_menu_items(["add"])
		
		elif selected_partition[1] == _("extended") and partition_device.isleaf:
			self.toolbar.deactivate_all()
			self.toolbar.activate_buttons(["delete"])
			
			self.main_menu.deactivate_all()
			self.main_menu.activate_menu_items(["delete"])
			
			self.popup_menu.deactivate_all()
			self.popup_menu.activate_menu_items(["delete"])
		
		elif selected_partition[1] == _("lvmvg") and partition_device.isleaf:
			self.toolbar.deactivate_all()
			self.toolbar.activate_buttons(["delete"])
			
			self.main_menu.deactivate_all()
			self.main_menu.activate_menu_items(["delete"])
			
			self.popup_menu.deactivate_all()
			self.popup_menu.activate_menu_items(["delete"])
			
		elif selected_partition[1] == _("lvmpv") and partition_device.isleaf:
			self.toolbar.deactivate_all()
			self.toolbar.activate_buttons(["delete"])
			
			self.main_menu.deactivate_all()
			self.main_menu.activate_menu_items(["delete"])
			
			self.popup_menu.deactivate_all()
			self.popup_menu.activate_menu_items(["delete"])
		
		else:
			self.toolbar.deactivate_all()
			self.main_menu.deactivate_all()
			self.popup_menu.deactivate_all()
			
			if partition_device.format.mountable and partition_mounted(partition_device.path) == None:
				self.toolbar.activate_buttons(["delete"])
				self.main_menu.activate_menu_items(["delete"])
				self.popup_menu.activate_menu_items(["delete"])
			
			if partition_device._type != "lvmvg" and partition_device.format.type == None:
				self.toolbar.activate_buttons(["delete"])
				self.main_menu.activate_menu_items(["delete"])
				self.popup_menu.activate_menu_items(["delete"])
				
			if partition_device.format.mountable and partition_mounted(partition_device.path) != None:
				self.toolbar.activate_buttons(["umount"])
				self.main_menu.activate_menu_items(["umount"])
				self.popup_menu.activate_menu_items(["umount"])
				
			if partition_device.format.mountable and partition_mounted(partition_device.path) == None:
				self.toolbar.activate_buttons(["edit"])
				self.main_menu.activate_menu_items(["edit"])
				self.popup_menu.activate_menu_items(["edit"])
	
	def delete_selected_partition(self):
		""" Delete selected partition
		"""
		
		deleted_device = self.selected_partition[0]
		
		dialog = ConfirmDeleteDialog(self.selected_partition[0])
		response = dialog.run()

		if response == Gtk.ResponseType.OK:
            
			self.b.delete_device(self.selected_partition[0])
			
			self.update_actions_view("delete",_("delete partition {0}").format(self.selected_partition[0]))
			
			self.selected_partition = None
			
		elif response == Gtk.ResponseType.CANCEL:
			pass

		dialog.destroy()
        
		self.update_partitions_view(self.disk)
		self.update_partitions_image(self.disk)
		
		self.list_devices.update_devices_view("delete", self.disk, deleted_device)
	
	def add_partition(self):
		""" Add new partition
		"""
		
		free_size = int(self.selected_partition[3].split()[0])
		
		device_type = self.b.get_device_type(self.disk)
		
		if device_type == "disk" and self.b.has_disklabel(self.disk) != True:
			
			dialog = AddLabelDialog(self.disk)
			
			response = dialog.run()
			
			if response == Gtk.ResponseType.OK:
				
				selection = dialog.get_selection()
				
				self.b.create_disk_label(self.disk)
				self.update_actions_view("add","create new disklabel on " + str(self.disk) + " device")
				
				dialog.destroy()
			
			elif response == Gtk.ResponseType.CANCEL:		
			
				dialog.destroy()
			
				return
			
			return
		
		dialog = AddDialog(device_type, self.disk ,self.selected_partition[0],
					 free_size, self.b.get_free_pvs_info())
		
		response = dialog.run()
		
		selection = dialog.get_selection()
		
		if response == Gtk.ResponseType.OK:
			
			if selection[2] == None and selection[0] not in ["LVM2 Physical Volume",
													"LVM2 Volume Group", "LVM2 Storage"]:
				# If fs is not selected, show error window and re-run add dialog
				AddErrorDialog()
				dialog.destroy()
				self.add_partition()
			
			elif selection[0] == "LVM2 Volume Group":
				user_input = dialog.get_selection()
				
				ret = self.b.add_device(parent_names=user_input[5], device_type=user_input[0],
							fs_type=user_input[2], target_size=user_input[1], name=user_input[3],
							label=user_input[4])
				
				if ret != None:
					
					self.update_actions_view("add","add " + str(user_input[1]) + " MB " + user_input[0] + " device")
					self.list_devices.update_devices_view("add", self.disk, ret)
						
					self.update_partitions_view(self.disk)
					self.update_partitions_image(self.disk)
				
				else:
					self.update_partitions_view(self.disk)
					self.update_partitions_image(self.disk)
				
				dialog.destroy()
			
			elif selection[0] == "LVM2 Storage":
				user_input = dialog.get_selection()
				
				ret1 = self.b.add_device(parent_names=[self.disk], device_type="LVM2 Physical Volume",
							 fs_type=user_input[2], target_size=user_input[1], name=user_input[3],
							 label=user_input[4])
				
				if ret1 != None:
					
					if user_input[2] == None:
						self.list_devices.update_devices_view("add", self.disk, ret1)
					
				ret2 = self.b.add_device(parent_names=[ret1], device_type="LVM2 Volume Group",
							 fs_type=user_input[2], target_size=user_input[1], name=user_input[3],
							 label=user_input[4])
				
				if ret2 != None:
					
					if user_input[2] == None:
						self.update_actions_view("add","add " + str(user_input[1]) + " MB " + user_input[0] + " device")
						self.list_devices.update_devices_view("add", self.disk, ret2)
						
					self.update_partitions_view(self.disk)
					self.update_partitions_image(self.disk)
				
				else:
					self.update_partitions_view(self.disk)
					self.update_partitions_image(self.disk)
				
				dialog.destroy()
		
			else:
				user_input = dialog.get_selection()
				
				# user_input = [device, size, fs, name, label]
				ret = self.b.add_device(parent_names=[self.disk], device_type=user_input[0],
							fs_type=user_input[2], target_size=user_input[1], name=user_input[3],
							label=user_input[4])
				
				if ret != None:
					
					if user_input[2] == None:
						self.update_actions_view("add","add " + str(user_input[1]) + " MB " + user_input[0] + " device")
						self.list_devices.update_devices_view("add", self.disk, ret)
						
					else:
						self.update_actions_view("add","add " + str(user_input[1]) + " MB " + user_input[2] + " partition")
						
					self.update_partitions_view(self.disk)
					self.update_partitions_image(self.disk)
				
				else:
					self.update_partitions_view(self.disk)
					self.update_partitions_image(self.disk)
				
				dialog.destroy()
			
		elif response == Gtk.ResponseType.CANCEL:		
			
			dialog.destroy()
			
			return
		
	def perform_actions(self):
		""" Perform queued actions
		
		.. note::
				New window creates separate thread to run blivet.doIt()
				
		"""
		
		win = ProcessingActions(self)
		
		Gdk.threads_leave()
		
		self.clear_actions_view()
		
		self.update_partitions_view(self.disk)
		self.update_partitions_image(self.disk)
	
	def umount_partition(self):
		""" Unmount selected partition
		"""
		
		mountpoint = self.selected_partition[2]
		
		if os_umount_partition(mountpoint):
			self.update_partitions_view(self.disk)
			self.update_partitions_image(self.disk)
			
		else:
			UnmountErrorDialog(self.selected_partition[0])
	
	def edit_partition(self):
		""" Edit selected partition
		"""
		
		resizable = self.b.device_resizable(self.selected_partition[0])
		
		dialog = EditDialog(self.selected_partition[0], resizable)
		dialog.connect("delete-event", Gtk.main_quit)
		
		response = dialog.run()
		
		selection = dialog.get_selection()
		
		if response == Gtk.ResponseType.OK:
		
			user_input = dialog.get_selection()
			
			if user_input[0] == False and user_input[2] == None:
				dialog.destroy()
				
			else:
				
				ret = self.b.edit_partition_device(self.selected_partition[0], user_input)
			
				if ret:
					self.update_actions_view("edit","edit " + self.selected_partition[0] + " partition")
					self.update_partitions_view(self.disk)
					self.update_partitions_image(self.disk)
				
				else:
					self.update_partitions_view(self.disk)
					self.update_partitions_image(self.disk)
			
				dialog.destroy()
			
		elif response == Gtk.ResponseType.CANCEL:		
			
			dialog.destroy()
			
			return
	
	def clear_actions(self):
		""" Clear all scheduled actions
		"""
		
		self.b.blivet_reset()
		
		self.list_devices.update_devices_view("all",None,None)
		self.update_partitions_view(self.disk)
		self.update_partitions_image(self.disk)
	
	def on_partition_selection_changed(self,selection):
		""" On selected partition action
		"""
		
		model, treeiter = selection.get_selected()
		
		self.toolbar.deactivate_all()
		
		if treeiter != None:
			
			self.activate_action_buttons(model[treeiter])
			self.selected_partition = model[treeiter]
	
	def quit(self):
		""" Quit blivet-gui
		"""
		
		if self.actions != 0:
			# There are queued actions we don't want do quit now
			dialog = ConfirmQuitDialog(self.actions)
			response = dialog.run()

			if response == Gtk.ResponseType.OK:
				
				Gtk.main_quit()
				
			elif response == Gtk.ResponseType.CANCEL:
				pass

			dialog.destroy()
		
		else:
			Gtk.main_quit()			
	
	@property
	def get_partitions_list(self):
		return self.partitions_list
	
	@property
	def get_partitions_view(self):
		return self.partitions_view
	
	@property
	def get_actions_view(self):
		return self.actions_view
	
	@property
	def get_toolbar(self):
		return self.toolbar.get_toolbar
	
	@property
	def get_actions_label(self):
		return self.actions_label
	
	@property
	def get_actions_list(self):
		return self.actions_list
	
	@property
	def get_main_menu(self):
		return self.main_menu.get_main_menu