# -*- coding: utf-8 -*-
# dialogs.py
# Gtk.MessageDialog classes for blivet-gui
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

import gettext

from gi.repository import Gtk, GdkPixbuf

#------------------------------------------------------------------------------#

APP_NAME = "blivet-gui"

dirname, filename = os.path.split(os.path.abspath(__file__))

t = gettext.translation('messages', dirname + '/i18n')
_ = t.gettext

#------------------------------------------------------------------------------#
 
class RootTestDialog(Gtk.MessageDialog):
	""" Dialog window informing user to run blivet-gui as root	
	"""
	
	def __init__(self):
		Gtk.MessageDialog.__init__(self, None, 0, 
			Gtk.MessageType.ERROR,
			Gtk.ButtonsType.CANCEL, 
			_("Root privileges required"))
		
		self.format_secondary_text = _("Root privileges are required for running blivet-gui.")
		
		self.show_all()
		
		self.connect("delete-event", Gtk.main_quit)
		self.run()
		self.destroy()
		
class AddErrorDialog(Gtk.MessageDialog):
	""" Dialog window informing user he/she need to specify fs type to create new partition
	"""
	
	def __init__(self):
		Gtk.MessageDialog.__init__(self, None, 0,
			Gtk.MessageType.ERROR,
			Gtk.ButtonsType.OK, 
			_("Error:\n\nFilesystem type must be specified when creating new partition."))
		
		self.show_all()
		
		self.connect("delete-event", Gtk.main_quit)
		self.run()
		self.destroy()

class BlivetError(Gtk.MessageDialog):
	""" Dialog window informing user about blivet error/exception
	"""
	
	def __init__(self, exception):
		"""
			:param exception: raised exception
			:type exception: str
		"""
		
		Gtk.MessageDialog.__init__(self, None, 0, 
			Gtk.MessageType.ERROR,
			Gtk.ButtonsType.OK, 
			_("Error:\n\nUnknown error appeared:\n\n%(exception)s." % locals()))
		
		self.show_all()
		
		self.connect("delete-event", Gtk.main_quit)
		self.run()
		self.destroy()	
		
class UnmountErrorDialog(Gtk.MessageDialog):
	""" Dialog window informing user about unsuccesfull unmount operation
	"""
	
	def __init__(self, device_name):
		"""
            :param device_name: name of partition (device) to unmount
            :type device_name: str
        """
        
		Gtk.MessageDialog.__init__(self, None, 0, 
			Gtk.MessageType.ERROR,
			Gtk.ButtonsType.OK, 
			_("Unmount failed.\n\nAre you sure \'%(device_name)s\' is not in use?" % locals()))
		
		self.show_all()
		
		self.connect("delete-event", Gtk.main_quit)
		self.run()
		self.destroy()

class ConfirmDeleteDialog(Gtk.Dialog):
	""" Confirmation dialog for device deletion
	"""
	
	def __init__(self,device_name):
		"""
            :param device_name: name of partition (device) to delete
            :type device_name: str
        """
        
		Gtk.Dialog.__init__(self, _("Confirm delete operation"), None, 0,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OK, Gtk.ResponseType.OK))

		self.set_default_size(175, 110)

		label = Gtk.Label(_("Are you sure you want to delete device %(device_name)s?" % locals()))

		box = self.get_content_area()
		box.add(label)
		self.show_all()

class ConfirmPerformActions(Gtk.Dialog):
	""" Confirmation dialog for device deletion
	"""
	
	def __init__(self):
		Gtk.Dialog.__init__(self, _("Confirm scheduled actions"), None, 0,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OK, Gtk.ResponseType.OK))

		self.set_default_size(175, 110)

		label = Gtk.Label(_("Are you sure you want to perform scheduled actions?"))
		
		box = self.get_content_area()
		box.add(label)
		
		self.show_all()

class ConfirmQuitDialog(Gtk.Dialog):
	""" Confirmation dialog for application quit
	"""
	
	def __init__(self,actions):
		"""
            :param actions: number of queued actions
            :type device_name: int
        """
        
		Gtk.Dialog.__init__(self, _("Are you sure you want to quit?"), None, 0,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OK, Gtk.ResponseType.OK))

		self.set_default_size(175, 110)

		label = Gtk.Label(_("There are unapplied queued actions. Are you sure you want to quit blivet-gui now?"))

		box = self.get_content_area()
		box.add(label)
		self.show_all()
		
class EditDialog(Gtk.Dialog):
	""" Dialog window allowing user to edit partition including selecting size, fs, label etc.
	"""
	
	def __init__(self,partition_name, resizable):
		"""
		
			:param partition_name: name of device
			:type partition_name: str
			:param resizable: is partition resizable, minSize, maxSize
			:type free_space: tuple
		"""
		
		self.partition_name = partition_name
		self.resizable = resizable
		self.resize = False
		
		Gtk.Dialog.__init__(self, _("Edit device"), None, 0,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OK, Gtk.ResponseType.OK))

		self.set_default_size(550, 200)

		self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10, column_spacing=5)
		
		box = self.get_content_area()
		box.add(self.grid)
		
		self.add_size_scale()
		self.add_fs_chooser()
		self.add_name_chooser()
		
	def add_size_scale(self):
		
		self.scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=Gtk.Adjustment(0, self.resizable[1], self.resizable[2], 1, 10, 0))
		self.scale.set_hexpand(True)
		self.scale.set_valign(Gtk.Align.START)
		self.scale.set_digits(0)
		self.scale.set_value(self.resizable[3])
		self.scale.add_mark(self.resizable[1],Gtk.PositionType.BOTTOM,str(int(self.resizable[1])))
		self.scale.add_mark(self.resizable[2],Gtk.PositionType.BOTTOM,str(int(self.resizable[2])))
		self.scale.connect("value-changed", self.scale_moved)
		
		self.grid.attach(self.scale, 0, 1, 6, 1) #left-top-width-height
		
		self.label_size = Gtk.Label()
		self.label_size.set_text(_("Volume size:"))
		self.grid.attach(self.label_size, 0, 2, 1, 1) #left-top-width-height
		
		self.spin_size = Gtk.SpinButton(adjustment=Gtk.Adjustment(0, self.resizable[1], self.resizable[2], 1, 10, 0))
		self.spin_size.set_numeric(True)
		self.spin_size.set_value(self.resizable[3])
		self.spin_size.connect("value-changed", self.spin_size_moved)
		
		self.grid.attach(self.spin_size, 1, 2, 1, 1) #left-top-width-height
		
		self.label_mb = Gtk.Label()
		self.label_mb.set_text(_("MB"))
		self.grid.attach(self.label_mb, 2, 2, 1, 1) #left-top-width-height
		
		if self.resizable[0] == False or self.resizable[1] == self.resizable[2]:
			self.label_resize = Gtk.Label()
			self.label_resize.set_markup(_("<b>This device cannot be resized.</b>"))
			self.grid.attach(self.label_resize, 0, 0, 6, 1) #left-top-width-height
			
			self.scale.set_sensitive(False)
			self.spin_size.set_sensitive(False)
		
	def add_fs_chooser(self):
		
		self.label_fs = Gtk.Label()
		self.label_fs.set_text(_("Filesystem:"))
		self.grid.attach(self.label_fs, 0, 3, 1, 1)
		
		
		filesystems = ["ext2", "ext3", "ext4", "ntfs",
			"fat", "xfs", "reiserfs"]
		self.filesystems_combo = Gtk.ComboBoxText()
		self.filesystems_combo.set_entry_text_column(0)
		
		self.filesystems_combo.connect("changed", self.filesystems_combo_changed)
		
		for fs in filesystems:
			self.filesystems_combo.append_text(fs)
		
		self.grid.attach(self.filesystems_combo,1,3,2,1)
		
		self.label_warn = Gtk.Label()
		self.grid.attach(self.label_warn, 0, 5, 6, 1)
		
	def add_name_chooser(self):
		
		self.label_entry = Gtk.Label()
		self.label_entry.set_text(_("Label:"))
		self.grid.attach(self.label_entry, 0, 4, 1, 1)
		
		self.name_entry = Gtk.Entry()
		self.grid.attach(self.name_entry,1,4,2,1)
		
		self.show_all()
	
	def filesystems_combo_changed(self, event):
		
		if self.filesystems_combo.get_active_text() != None:
			self.label_warn.set_markup(_("<b>Warning: This will delete all data on {0}!</b>").format(self.partition_name))
	
	def scale_moved(self,event):
		
		self.resize = True
		self.spin_size.set_value(self.scale.get_value())
		
	def spin_size_moved(self,event):
		
		self.resize = True
		self.scale.set_value(self.spin_size.get_value())

	def get_selection(self):
		
		return (self.resize, self.spin_size.get_value(), self.filesystems_combo.get_active_text())


class AddDialog(Gtk.Dialog):
	""" Dialog window allowing user to add new partition including selecting size, fs, label etc.
	"""
	
	def __init__(self,device_type, parent_name, partition_name, free_space, free_pvs):
		"""
			
			:param device_type: type of parent device
			:type device_type: str
			:parama parent_name: name of parent device
			:type parent_name: str
			:param partition_name: name of device
			:type partition_name: str
			:param free_space: size of selected free space
			:type free_space: int
			:param free_pvs: list PVs with no VG
			:type free_pvs: list
			
        """
        
		self.partition_name = partition_name
		self.free_space = free_space
		self.device_type = device_type
		self.parent_name = parent_name
		self.free_pvs = free_pvs
        
		Gtk.Dialog.__init__(self, _("Create new partition"), None, 0,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OK, Gtk.ResponseType.OK))
		
		self.set_border_width(10)
		self.set_default_size(600, 300)

		self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10, column_spacing=5)

		box = self.get_content_area()
		box.add(self.grid)
		
		self.add_size_scale()
		self.add_fs_chooser()
		self.add_name_chooser()
		self.add_parent_list()
		self.add_device_chooser() #!important
		
		self.show_all()
		
	def add_device_chooser(self):
		
		map_type_devices = {
			"disk" : [_("Partition"), _("LVM2 Storage"), _("LVM2 Physical Volume")],
			"lvmpv" : [_("LVM2 Volume Group")],
			"lvmvg" : [_("LVM2 Logical Volume")],
			}
		
		self.label_devices = Gtk.Label()
		self.label_devices.set_text(_("Device type:"))
		self.grid.attach(self.label_devices, 0, 0, 1, 1)
		
		devices = map_type_devices[self.device_type]
		
		devices_store = Gtk.ListStore(str)
		
		for device in devices:
			devices_store.append([device])
            
		self.devices_combo = Gtk.ComboBox.new_with_model(devices_store)
		
		self.devices_combo.set_entry_text_column(0)
		self.devices_combo.set_active(0)
		
		if len(devices) == 1:
			self.devices_combo.set_sensitive(False)
		
		if self.device_type == "lvmpv":
			self.filesystems_combo.set_sensitive(False)
			self.label_fs.set_sensitive(False)
			self.label_size.set_sensitive(False)
			self.label_free.set_sensitive(False)
			self.scale.set_sensitive(False)
			self.spin_size.set_sensitive(False)
			self.spin_free.set_sensitive(False)
		
		self.grid.attach(self.devices_combo,1,0,2,1)
		
		self.devices_combo.connect("changed", self.on_devices_combo_changed)
		renderer_text = Gtk.CellRendererText()
		self.devices_combo.pack_start(renderer_text, True)
		self.devices_combo.add_attribute(renderer_text, "text", 0)
	
	def add_parent_list(self):
		
		self.parents_store = Gtk.ListStore(bool, str, str, str)
		
		self.parents = Gtk.TreeView(model=self.parents_store)
		#self.parents.set_vexpand(True)
		#self.parents.set_hexpand(True)
		
		renderer_toggle = Gtk.CellRendererToggle()
		renderer_toggle.connect("toggled", self.on_cell_toggled)
		
		renderer_text = Gtk.CellRendererText()
		
		column_toggle = Gtk.TreeViewColumn(None, renderer_toggle, active=0)
		column_name = Gtk.TreeViewColumn(_("Device"), renderer_text, text=1)
		column_type = Gtk.TreeViewColumn(_("Type"), renderer_text, text=2)
		column_size = Gtk.TreeViewColumn(_("Size"), renderer_text, text=3)
		
		self.parents.append_column(column_toggle)
		self.parents.append_column(column_name)
		self.parents.append_column(column_type)
		self.parents.append_column(column_size)
		
		self.parents.set_headers_visible(True)
		
		if self.device_type == "lvmpv":
			for pv in self.free_pvs:
				if pv[0] == self.parent_name:
					self.parents_store.append([True, self.parent_name, self.device_type, str(self.free_space) + " MB"])
				else:
					self.parents_store.append([False, pv[0], pv[1], str(pv[2]) + " MB"])
			
			self.parents.set_sensitive(True)
		
		else:
			self.parents_store.append([True, self.parent_name, self.device_type, str(self.free_space) + " MB"])
			self.parents.set_sensitive(False)
		
		self.label_list = Gtk.Label()
		self.label_list.set_text(_("Available devices:"))
		
		self.grid.attach(self.label_list, 0, 1, 1, 1)
		self.grid.attach(self.parents, 1, 1, 4, 4)
	
	def on_cell_toggled(self, event, path):
		
		if self.parents_store[path][1] == self.parent_name:
			pass
		
		else:
			self.parents_store[path][0] = not self.parents_store[path][0]		
	
	def add_size_scale(self):
		
		self.scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=Gtk.Adjustment(0, 1, self.free_space, 1, 10, 0))
		self.scale.set_hexpand(True)
		self.scale.set_valign(Gtk.Align.START)
		self.scale.set_digits(0)
		self.scale.set_value(self.free_space)
		self.scale.add_mark(0,Gtk.PositionType.BOTTOM,str(1))
		self.scale.add_mark(self.free_space,Gtk.PositionType.BOTTOM,str(self.free_space))
		self.scale.connect("value-changed", self.scale_moved)
		
		self.grid.attach(self.scale, 0, 6, 6, 1) #left-top-width-height
		
		self.label_size = Gtk.Label()
		self.label_size.set_text(_("Volume size:"))
		self.grid.attach(self.label_size, 0, 7, 1, 1) #left-top-width-height
		
		self.spin_size = Gtk.SpinButton(adjustment=Gtk.Adjustment(0, 1, self.free_space, 1, 10, 0))
		self.spin_size.set_numeric(True)
		self.spin_size.set_value(self.free_space)
		self.spin_size.connect("value-changed", self.spin_size_moved)
		
		self.grid.attach(self.spin_size, 1, 7, 1, 1) #left-top-width-height
		
		self.label_mb = Gtk.Label()
		self.label_mb.set_text(_("MB"))
		self.grid.attach(self.label_mb, 2, 7, 1, 1) #left-top-width-height
		
		self.label_free = Gtk.Label()
		self.label_free.set_text(_("Free space after:"))
		self.grid.attach(self.label_free, 3, 7, 1, 1) #left-top-width-height
		
		self.spin_free = Gtk.SpinButton(adjustment=Gtk.Adjustment(0, 0, self.free_space, 1, 10, 0))
		self.spin_free.set_numeric(True)
		self.spin_free.connect("value-changed", self.spin_free_moved)
		
		self.grid.attach(self.spin_free, 4, 7, 1, 1) #left-top-width-height
		
		self.label_mb2 = Gtk.Label()
		self.label_mb2.set_text(_("MB"))
		self.grid.attach(self.label_mb2, 5, 7, 1, 1) #left-top-width-height
		
	def add_fs_chooser(self):
		
		self.label_fs = Gtk.Label()
		self.label_fs.set_text(_("Filesystem:"))
		self.grid.attach(self.label_fs, 0, 8, 1, 1)
		
		filesystems = ["ext2", "ext3", "ext4", "ntfs",
			"fat", "xfs", "reiserfs", "swap"]
		self.filesystems_combo = Gtk.ComboBoxText()
		self.filesystems_combo.set_entry_text_column(0)
		
		for fs in filesystems:
			self.filesystems_combo.append_text(fs)
		
		self.grid.attach(self.filesystems_combo,1,8,2,1)
		
	def add_name_chooser(self):
		
		self.label_label = Gtk.Label()
		self.label_label.set_text(_("Label:"))
		self.grid.attach(self.label_label, 0, 9, 1, 1)
		
		self.label_entry = Gtk.Entry()
		self.grid.attach(self.label_entry,1,9,2,1)
		
		if self.device_type not in ["lvmvg", "disk"]:
			self.label_label.set_sensitive(False)
			self.label_entry.set_sensitive(False)
		
		self.name_label = Gtk.Label()
		self.name_label.set_text(_("Name:"))
		self.grid.attach(self.name_label, 3, 9, 1, 1)
		
		self.name_entry = Gtk.Entry()
		
		if self.device_type not in ["lvmvg", "lvmpv"]:
			self.name_label.set_sensitive(False)
			self.name_entry.set_sensitive(False)
		
		self.grid.attach(self.name_entry,4,9,2,1)
	
	def on_devices_combo_changed(self, event):
		
		tree_iter = self.devices_combo.get_active_iter()
		
		if tree_iter != None:
			model = self.devices_combo.get_model()
			device = model[tree_iter][0]
			
			if device == _("Partition"):
				self.label_label.set_sensitive(True)
				self.label_entry.set_sensitive(True)
				
				self.name_label.set_sensitive(False)
				self.name_entry.set_sensitive(False)
				
			if device == _("LVM2 Physical Volume"):
				self.label_label.set_sensitive(False)
				self.label_entry.set_sensitive(False)
				
				self.name_label.set_sensitive(False)
				self.name_entry.set_sensitive(False)
				
				self.filesystems_combo.set_sensitive(False)
				self.label_fs.set_sensitive(False)
			
			if device == _("LVM2 Storage"):
				self.label_label.set_sensitive(False)
				self.label_entry.set_sensitive(False)
				
				self.name_label.set_sensitive(True)
				self.name_entry.set_sensitive(True)
				
				self.filesystems_combo.set_sensitive(False)
				self.label_fs.set_sensitive(False)
	
	def scale_moved(self,event):
		
		self.spin_size.set_value(self.scale.get_value())
		self.spin_free.set_value(self.free_space - self.scale.get_value())
		
	def spin_size_moved(self,event):
		
		self.scale.set_value(self.spin_size.get_value())
		self.spin_free.set_value(self.free_space - self.scale.get_value())
		
	def spin_free_moved(self,event):
		
		self.scale.set_value(self.free_space - self.spin_free.get_value())
		self.spin_size.set_value(self.free_space - self.spin_free.get_value())
	
	def get_selection(self):
		tree_iter = self.devices_combo.get_active_iter()
		
		if tree_iter != None:
			model = self.devices_combo.get_model()
			device = model[tree_iter][0]
		
		if device == "LVM2 Volume Group":
			parents = []
			size = 0
			
			for row in self.parents_store:
				if row[0]:
					parents.append(row[1])
					size += int(row[3].split()[0])
			
			return (device, size, self.filesystems_combo.get_active_text(), 
				self.name_entry.get_text(), self.label_entry.get_text(), parents)
			
		return (device, self.spin_size.get_value(),
		  self.filesystems_combo.get_active_text(), self.name_entry.get_text(), 
		  self.label_entry.get_text())
	
class AddLabelDialog(Gtk.Dialog):
	""" Dialog window allowing user to add disklabel to disk
	"""
	
	def __init__(self, disk_name):
		"""
			:param disk_name: name of the disk
			:type disk_name: str
			
		"""
		
		self.disk_name = disk_name
        
		Gtk.Dialog.__init__(self, _("No partition table found on disk"), None, 0,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OK, Gtk.ResponseType.OK))

		self.set_default_size(550, 200)
		self.set_border_width(10)

		self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10, column_spacing=5)

		box = self.get_content_area()
		box.add(self.grid)
		
		self.add_labels()
		self.add_pt_chooser()
		
		self.show_all()
	
	def add_labels(self):
		
		self.info_label = Gtk.Label()
		self.info_label.set_markup(_("A partition table is required before partitions can be added.\n\n<b>Warning: This will delete all data on {0}!</b>").format(self.disk_name))
		
		self.grid.attach(self.info_label, 0, 0, 4, 1) #left-top-width-height
		
	def add_pt_chooser(self):
		
		self.pts_store = Gtk.ListStore(str)
		
		pt_list = ["msdos"]
		
		for pt in pt_list:
			self.pts_store.append([pt])
            
		self.pts_combo = Gtk.ComboBox.new_with_model(self.pts_store)
		
		self.pts_combo.set_entry_text_column(0)
		self.pts_combo.set_active(0)
		
		self.pts_combo.set_sensitive(False)
		
		self.label_list = Gtk.Label()
		self.label_list.set_text(_("Select new partition table type:"))
		
		self.grid.attach(self.label_list, 0, 1, 3, 1)
		self.grid.attach(self.pts_combo, 3, 1, 1, 1)
		
		self.pts_combo.connect("changed", self.on_devices_combo_changed)
		renderer_text = Gtk.CellRendererText()
		self.pts_combo.pack_start(renderer_text, True)
		self.pts_combo.add_attribute(renderer_text, "text", 0)
		
		
	def on_devices_combo_changed(self, event):
		
		tree_iter = self.devices_combo.get_active_iter()
		
		if tree_iter != None:
			model = self.devices_combo.get_model()
			device = model[tree_iter][0]
		
	def get_selection(self):
		tree_iter = self.pts_combo.get_active_iter()
		
		if tree_iter != None:
			model = self.pts_combo.get_model()
			pt = model[tree_iter][0]
		
		return [pt]

class AddPVDialog(Gtk.Dialog):
	""" Dialog window allowing user to add new LVM2 Physical Volume
	"""
	
	def __init__(self):
        
		Gtk.Dialog.__init__(self, _("Create new LVM2 PV"), None, 0,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OK, Gtk.ResponseType.OK))

		self.set_default_size(550, 200)
		self.set_border_width(10)

		self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10, column_spacing=5)

		box = self.get_content_area()
		box.add(self.grid)
		
	def get_selection(self):
		return
	
class AboutDialog(Gtk.AboutDialog):
	""" Standard 'about application' dialog
	"""
	
	def __init__(self):
		Gtk.AboutDialog.__init__(self)

		authors = ["Vojtech Trefny <vtrefny@redhat.com>"]
		documenters = ["Vojtech Trefny <vtrefny@redhat.com>"]

		self.set_program_name(APP_NAME)
		self.set_copyright(_("Copyright \xc2\xa9 2014 Red Hat Inc."))
		self.set_authors(authors)
		self.set_documenters(documenters)
		self.set_website("https://github.com/vojtechtrefny/blivet-gui")
		self.set_website_label("blivet-gui Website")
		self.set_license_type(Gtk.License.GPL_3_0)

		self.set_title("")

		self.connect("response", self.on_close)

		self.show()

	def on_close(self, action, par):
		self.destroy()