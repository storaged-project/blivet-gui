#!/usr/bin/python2

import sys, os, signal

from gi.repository import Gtk, GdkPixbuf

import blivet

import gettext

from utils import *

APP_NAME = "blivet-gui"

#TODO
#onclick na disk musim nacist partitiony k danemu disku a ty potom zobrazit v notebooku (resp. pridat do view a to zobrazit

#-----------------------------------------------------#

class ListDiskDevices:
	def __init__(self):
		self.DiskList = Gtk.ListStore(str, str)
		
		self.LoadDisks()
	
	def LoadDisks(self):
		disks = GetDisks()
		
		for disk in disks:
			if disk.removable:
				self.DiskList.append([Gtk.STOCK_HARDDISK,str(disk.name + "\n" + disk.model)]) #FIXME
			else:
				self.DiskList.append([Gtk.STOCK_HARDDISK,str(disk.name + "\n" + disk.model)])
	
	def ReturnDiskList(self):
		return self.DiskList

#-----------------------------------------------------#

class ListPartitions:
	def __init__(self,disk):
		self.disk = disk
		
		self.PartitionsList = Gtk.ListStore(str, str, str, str)

		self.LoadPartitions()
	
	def LoadPartitions(self):
		partitions = GetPartitions(disk)
		
		for partition in partitions:
			self.DiskList.append([Gtk.STOCK_HARDDISK,str(disk.name + "\n" + disk.model)])
	
	def ReturnPartitionsList(self):
		return self.PartitionsList

#-----------------------------------------------------#

class RootTestDialog(Gtk.MessageDialog):
	
	def __init__(self,parent):
		Gtk.MessageDialog.__init__(self, parent, 0, Gtk.MessageType.ERROR,Gtk.ButtonsType.CANCEL, _("Root privileges required"))
		format_secondary_text = _("Root privileges are required for running blivet-gui.")
		
		self.connect("delete-event", Gtk.main_quit)
		self.run()
		self.destroy()

#-----------------------------------------------------#

class MainViewWindow(Gtk.Window):
	
	def __init__(self):
		Gtk.Window.__init__(self, title=APP_NAME)
		
		self.set_default_size(600, 500)
		self.grid = Gtk.Grid(column_homogeneous=False)
		self.add(self.grid)
		
		self.CreateToolbar()
		self.CreateDiskColumn()
		self.CreateTabbedView()
	
	def CreateToolbar(self):
		toolbar = Gtk.Toolbar()
		self.grid.attach(toolbar, 0, 0, 3, 1) #left-top-width-height
		
		ButtonNew = Gtk.ToolButton.new_from_stock(Gtk.STOCK_ADD)
		ButtonNew.set_sensitive(False)
		toolbar.insert(ButtonNew, 0)
		
		ButtonDelete = Gtk.ToolButton.new_from_stock(Gtk.STOCK_DELETE)
		ButtonDelete.set_sensitive(False)
		toolbar.insert(ButtonDelete, 1)
		
		toolbar.insert(Gtk.SeparatorToolItem(), 2)
		
		ButtonEdit = Gtk.ToolButton.new_from_stock(Gtk.STOCK_EDIT)
		ButtonEdit.set_sensitive(False)
		toolbar.insert(ButtonEdit, 3)
		
	
	def CreateDiskView(self):
		
		disks = ListDiskDevices().ReturnDiskList()
		
		treeview = Gtk.TreeView(model=disks)
		treeview.set_vexpand(True)
		#treeview.set_hexpand(True)
		
		renderer_pixbuf = Gtk.CellRendererPixbuf()
		column_pixbuf = Gtk.TreeViewColumn(None, renderer_pixbuf, stock_id=0)
		treeview.append_column(column_pixbuf)
		
		renderer_text = Gtk.CellRendererText()
		column_text = Gtk.TreeViewColumn(None, renderer_text, text=1)
		treeview.append_column(column_text)
		
		treeview.set_headers_visible(False)
		
		return treeview
	
	def CreateDiskColumn(self):
		diskbox = Gtk.ScrolledWindow()
		diskview = Gtk.Viewport()
		
		diskbox.add(diskview)
		disklist = self.CreateDiskView()
		diskview.add(disklist)
		self.grid.attach(diskbox, 0, 1, 1, 2)
		
	def CreatePartitionView(self, disk_name):
		
		partitions = ListPartitions().ReturnPartitionsList()
		
		treeview = Gtk.TreeView(model=diskpartitions)
		treeview.set_vexpand(True)
		treeview.set_hexpand(True)
		
		renderer_partition = Gtk.CellRendererText()
		column_partition = Gtk.TreeViewColumn(None, renderer_partition, text=0)
		treeview.append_column(column_partition)
		
		renderer_pixbuf = Gtk.CellRendererPixbuf()
		column_pixbuf = Gtk.TreeViewColumn(None, renderer_pixbuf, stock_id=1)
		treeview.append_column(column_pixbuf)
		
		renderer_fs = Gtk.CellRendererText()
		column_fs = Gtk.TreeViewColumn(None, renderer_fs, text=2)
		treeview.append_column(column_fs)
		
		treeview.set_headers_visible(True)
		
		return treeview
		
	def CreateTabbedView(self):
		notebook = Gtk.Notebook()
		notebook.set_tab_pos(Gtk.PositionType.TOP)
		notebook.set_show_tabs(True)
		
		label_parts = Gtk.Label(_("Partitions"))
		label_actions = Gtk.Label(_("Pending Actions"))
		
		scrolled_window1 = Gtk.ScrolledWindow()
		scrolled_window2 = Gtk.ScrolledWindow()
		
		#scrolled_window1.add(CreatePartitionView(self, "sda"))
		
		notebook.append_page(scrolled_window1, label_parts)
		notebook.append_page(scrolled_window2, label_actions)
		
		self.grid.attach(notebook, 1, 2, 2, 1)
		
		

#-----------------------------------------------------#



gettext.bindtextdomain(APP_NAME, 'po')
gettext.textdomain(APP_NAME)
_ = gettext.gettext


#class Handler:
    #def gtk_main_quit(self, *args):
        #Gtk.main_quit(*args)

#builder = Gtk.Builder()
#builder.add_from_file("blivet-gui.glade")
#builder.connect_signals(Handler())

signal.signal(signal.SIGINT, signal.SIG_DFL)

MainWindow = MainViewWindow()
MainWindow.connect("delete-event", Gtk.main_quit)

if os.geteuid() != 0:
	RootTestDialog(MainWindow)

else:
	MainWindow.show_all()
	Gtk.main()
