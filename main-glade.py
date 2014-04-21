#!/usr/bin/python2

import sys, os, signal

from gi.repository import Gtk, GdkPixbuf

import blivet

import gettext

import cairo

from utils import *

from dialogs import *

APP_NAME = "blivet-gui"

#-----------------------------------------------------#

class ListDevices():
	def __init__(self,BlivetUtils):
		
		self.b = BlivetUtils
		
		self.DeviceList = Gtk.ListStore(GdkPixbuf.Pixbuf, str)
		
		self.DeviceList.append([None,_("Disk Devices")])
		self.LoadDisks()
		
		self.DeviceList.append([None,_("Group Devices")])
		self.LoadGroupDevices()
	
	def LoadDisks(self):
		
		icon_theme = Gtk.IconTheme.get_default()
		icon_disk = Gtk.IconTheme.load_icon (icon_theme,"drive-harddisk",32, 0)
		icon_disk_usb = Gtk.IconTheme.load_icon (icon_theme,"drive-removable-media",32, 0)
		
		disks = b.GetDisks()
		
		for disk in disks:
			if disk.removable:
				self.DeviceList.append([icon_disk_usb,str(disk.name + "\n" + disk.model)])
			else:
				self.DeviceList.append([icon_disk,str(disk.name + "\n" + disk.model)])
	
	def LoadGroupDevices(self):
		gdevices = b.GetGroupDevices()
		
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
	
	def ReturnDeviceList(self):
		return self.DeviceList

#-----------------------------------------------------#

class ListPartitions():
	
	def __init__(self,BlivetUtils,disk=None):
		
		self.b = BlivetUtils
		
		self.disk = disk
		
		self.PartitionsList = Gtk.ListStore(str,str,str,str)

		self.LoadPartitions()
		
		self.darea = Gtk.DrawingArea()
	
	def LoadPartitions(self):
		self.PartitionsList.clear()
		partitions = b.GetPartitions(self.disk)
		
		for partition in partitions:
			if partition.name == _("unallocated"):
				self.PartitionsList.append([partition.name,"--","--",str(int(partition.size)) + " MB"])
			elif partition.format.mountable:
				self.PartitionsList.append([partition.format.device,partition.format._type,partition.format.mountpoint,str(int(partition.size)) + " MB"])
			else:
				self.PartitionsList.append([partition.format.device,partition.format._type,"",str(int(partition.size)) + " MB"])
	
	def UpdatePartitionsView(self):
		self.PartitionsList.clear()
		partitions = b.GetPartitions(self.disk)
		
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
	
	def create_basic_image(self):
		img = cairo.ImageSurface(cairo.FORMAT_ARGB32, 24, 24)
		c = cairo.Context(img)
		c.set_line_width(4)
		c.arc(12, 12, 8, 0, 2 * math.pi)
		c.set_source_rgb(1, 0, 0)
		c.stroke_preserve()
		c.set_source_rgb(1, 1, 1)
		c.fill()
		return img
	
	def on_draw(self,widget, event, img):
		#print darea.get_allocation().width, darea.get_allocation().height
		
		#ctx.set_source_rgb(0, 0, 0)
		#ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL,
			#cairo.FONT_WEIGHT_NORMAL)
		#ctx.set_font_size(20)
		#ctx.move_to(10, 20)
		#ctx.show_text("Text...")
		
		cr = widget.window.cairo_create()
		for i in range(10):
			cr.set_source_surface(img, x[i], y[i])        
			cr.paint()
	
	def checkerboard_draw_event(self, da, cairo_ctx, partitions):

		# At the start of a draw handler, a clip region has been set on
		# the Cairo context, and the contents have been cleared to the
		# widget's background color. The docs for
		# gdk_window_begin_paint_region() give more details on how this
		# works.
		#check_size = 10
		#spacing = 2
		
		#xcount = 0
		#i = spacing
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
		y = 0
		
		import random
		
		for partition in partitions:
			
			if partition[0] == _("unallocated"):
				cairo_ctx.set_source_rgb(0.75, 0.75, 0.75)
				# Grey color for unallocated space
			
			else:
				cairo_ctx.set_source_rgb(random.random() , random.random(), random.random()) #FIXME colors
			
			part_width = int(partition[3].split()[0])*width/total_size
			
			# Every partition need some minimum size in the drawing area
			# Minimum size = number of partitions*2 / width of draving area
			if part_width < width / (num_parts*2):
				part_width = width / (num_parts*2)
			
			if part_width > width - ((num_parts-1)* (width / (num_parts*2))):
				part_width = width - (num_parts-1) * (width / (num_parts*2))

			cairo_ctx.rectangle(x, y, part_width, height)
			cairo_ctx.fill()

			x += part_width			
			
			#FIXME disk name and size
		
		return True

	def clear(self, da, cairo_ctx):
		cairo_ctx.set_source_rgb(1,1,1)
		cairo_ctx.paint()
		
		return True
	
	def CreatePartitionImage(self):
		
		partitions = self.PartitionsList
		
		self.darea.connect('draw', self.checkerboard_draw_event, partitions)
		
		return self.darea
	
	def UpdatePartitionsImage(self):
		
		partitions = self.PartitionsList
		
		self.darea.queue_draw()
	
	def on_tree_selection_changed(self,selection):
		
		global last
		
		model, treeiter = selection.get_selected()
		
		if treeiter != None:
			
			if model[treeiter][1] == "Disk Devices" or model[treeiter][1] == "Group Devices":
				selection.handler_block(selection_signal)
				selection.unselect_iter(treeiter)
				selection.handler_unblock(selection_signal) 
				selection.select_iter(last)
				treeiter = last
			else:
				last = treeiter
			
			self.disk = model[treeiter][1].split('\n')[0]
			self.UpdatePartitionsView()
			self.UpdatePartitionsImage()
			
	
	def ReturnPartitionsList(self):
		return self.PartitionsList

#-----------------------------------------------------#


#-----------------------------------------------------#

gettext.bindtextdomain(APP_NAME, 'po')
gettext.textdomain(APP_NAME)
_ = gettext.gettext

builder = Gtk.Builder()
builder.add_from_file("blivet-gui.glade")

signal.signal(signal.SIGINT, signal.SIG_DFL)

MainWindow = builder.get_object("MainWindow")
MainWindow.connect("delete-event", Gtk.main_quit)

#-----------------------------------------------------#

b = BlivetUtils()

dlist = ListDevices(b)
dview = dlist.CreateDeviceView()
select = dview.get_selection()
path = select.select_path("1")

builder.get_object("disks_viewport").add(dview)

plist = ListPartitions(b)
plist.on_tree_selection_changed(select)
selection_signal = select.connect("changed", plist.on_tree_selection_changed)
builder.get_object("partitions_viewport").add(plist.CreatePartitionView())

builder.get_object("image_window").add(plist.CreatePartitionImage())

#-----------------------------------------------------#


if os.geteuid() != 0:
	RootTestDialog(MainWindow)
	sys.exit(0)

else:
	MainWindow.show_all()
	Gtk.main()

