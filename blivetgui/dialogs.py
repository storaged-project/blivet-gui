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

from blivet import Size

from math import floor, ceil

#------------------------------------------------------------------------------#

APP_NAME = "blivet-gui"

dirname, filename = os.path.split(os.path.abspath(__file__))

#t = gettext.translation('messages', dirname + '/i18n')
#_ = t.gettext

gettext.bindtextdomain('blivetgui', dirname + '/i18n')
gettext.textdomain('blivetgui')
_ = gettext.gettext

#------------------------------------------------------------------------------#
 
class RootTestDialog(Gtk.MessageDialog):
	""" Dialog window informing user to run blivet-gui as root	
	"""
	
	def __init__(self):
		Gtk.MessageDialog.__init__(self, None, 0, 
			Gtk.MessageType.ERROR,
			Gtk.ButtonsType.CANCEL, 
			_("Root privileges required"))
		
		self.format_secondary_text(_("Root privileges are required for running blivet-gui."))
		
		self.show_all()
		
		self.connect("delete-event", Gtk.main_quit)
		self.run()
		self.destroy()
		
class AddErrorDialog(Gtk.MessageDialog):
	""" Dialog window informing user he/she need to specify fs type to create new partition
	"""
	
	def __init__(self, parent_window, error_msg):
		
		self.parent_window = parent_window
		
		Gtk.MessageDialog.__init__(self, None, 0,
			Gtk.MessageType.ERROR,
			Gtk.ButtonsType.OK, 
			error_msg)
		
		self.set_transient_for(self.parent_window)
		
		self.show_all()
		
		self.connect("delete-event", Gtk.main_quit)
		self.run()
		self.destroy()

class BlivetError(Gtk.MessageDialog):
	""" Dialog window informing user about blivet error/exception
	"""
	
	def __init__(self, exception, parent_window):
		"""
			:param parent_window: parent window
			:type parent_window: Gtk.Window
			:param exception: raised exception
			:type exception: str
		"""
		
		self.parent_window = parent_window
		
		Gtk.MessageDialog.__init__(self, None, 0, 
			Gtk.MessageType.ERROR,
			Gtk.ButtonsType.OK, 
			_("Error:\n\nUnknown error appeared:\n\n%(exception)s." % locals()))
		
		self.set_transient_for(self.parent_window)
		
		self.show_all()
		
		self.connect("delete-event", Gtk.main_quit)
		self.run()
		self.destroy()	
		
class UnmountErrorDialog(Gtk.MessageDialog):
	""" Dialog window informing user about unsuccesfull unmount operation
	"""
	
	def __init__(self, device_name, parent_window):
		"""
		
			:param parent_window: parent window
			:type parent_window: Gtk.Window
			:param device_name: name of partition (device) to unmount
			:type device_name: str
		"""
		
		self.parent_window = parent_window
		
		Gtk.MessageDialog.__init__(self, None, 0, 
			Gtk.MessageType.ERROR,
			Gtk.ButtonsType.OK, 
			_("Unmount failed.\n\nAre you sure \'%(device_name)s\' is not in use?" % locals()))
		
		self.set_transient_for(self.parent_window)
		
		self.show_all()
		
		self.connect("delete-event", Gtk.main_quit)
		self.run()
		self.destroy()

class ConfirmDialog(Gtk.Dialog):
	""" General confirmation dialog
	"""
	
	def __init__(self, parent_window, title, msg):
		"""
		
			:param parent_window: parent window
			:type parent_window: Gtk.Window
			:param device_name: name of partition (device) to delete
			:type device_name: str
		
        """
		
		self.parent_window = parent_window
		self.title = title
		self.msg = msg
		
		Gtk.Dialog.__init__(self, self.title, None, 0,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OK, Gtk.ResponseType.OK))
		
		self.set_transient_for(self.parent_window)
		
		self.set_default_size(175, 110)

		label = Gtk.Label(self.msg)

		box = self.get_content_area()
		box.add(label)
		self.show_all()

class ConfirmDeleteDialog(Gtk.Dialog):
	""" Confirmation dialog for device deletion
	"""
	
	def __init__(self, device_name, parent_window):
		"""
		
			:param parent_window: parent window
			:type parent_window: Gtk.Window
			:param device_name: name of partition (device) to delete
			:type device_name: str
		
        """
		
		self.parent_window = parent_window
		
		Gtk.Dialog.__init__(self, _("Confirm delete operation"), None, 0,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OK, Gtk.ResponseType.OK))
		
		self.set_transient_for(self.parent_window)
		
		self.set_default_size(175, 110)

		label = Gtk.Label(_("Are you sure you want to delete device %(device_name)s?" % locals()))

		box = self.get_content_area()
		box.add(label)
		self.show_all()

class ConfirmPerformActions(Gtk.Dialog):
	""" Confirmation dialog for device deletion
	"""
	
	def __init__(self, parent_window):
		
		self.parent_window = parent_window
		
		Gtk.Dialog.__init__(self, _("Confirm scheduled actions"), None, 0,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OK, Gtk.ResponseType.OK))
		
		self.set_transient_for(self.parent_window)
		
		self.set_default_size(175, 110)

		label = Gtk.Label(_("Are you sure you want to perform scheduled actions?"))
		
		box = self.get_content_area()
		box.add(label)
		
		self.show_all()

class ConfirmQuitDialog(Gtk.Dialog):
	""" Confirmation dialog for application quit
	"""
	
	def __init__(self, parent_window, actions):
		"""
		
			:param parent_window: parent window
			:type parent_window: Gtk.Window
			:param actions: number of queued actions
			:type device_name: int
			
        """
		
		self.parent_window = parent_window
		
		Gtk.Dialog.__init__(self, _("Are you sure you want to quit?"), None, 0,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OK, Gtk.ResponseType.OK))
			
		self.set_transient_for(self.parent_window)
		
		self.set_default_size(175, 110)

		label = Gtk.Label(_("There are unapplied queued actions. Are you sure you want to quit blivet-gui now?"))

		box = self.get_content_area()
		box.add(label)
		self.show_all()
		
class EditDialog(Gtk.Dialog):
	""" Dialog window allowing user to edit partition including selecting size, fs, label etc.
	"""
	
	#FIXME add mountpoint validation -- os.path.isabs(path)
	def __init__(self, parent_window, partition_name, resizable, kickstart=False):
		"""
			
			:param parent_window: parent window
			:type parent_window: Gtk.Window
			:param partition_name: name of device
			:type partition_name: str
			:param resizable: is partition resizable, minSize, maxSize
			:type resizable: tuple
			:param kickstart: kickstart mode
			:type kickstart: bool
		"""
		
		self.partition_name = partition_name
		self.resizable = resizable
		self.resize = False
		self.kickstart = kickstart
		
		self.parent_window = parent_window
		
		Gtk.Dialog.__init__(self, _("Edit device"), None, 0,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OK, Gtk.ResponseType.OK))
		
		self.set_transient_for(self.parent_window)
		self.set_default_size(550, 200)

		self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10, column_spacing=5)
		
		box = self.get_content_area()
		box.add(self.grid)
		
		self.add_size_scale()
		self.add_fs_chooser()
		#self.add_name_chooser()
		
		if kickstart:
			self.add_mountpoint()
		
		self.show_all()
		
	def add_size_scale(self):
		
		# blivet.Size cuts fractional part -- eg. Size('2000 KiB').convertTo('MiB') = 1 MiB
		# so the down limit for resizing would be 1 MiB even though it is not possible to
		# resize the partition to less than 2 MiB (rounded to MiBs)
		self.down_limit = int(ceil(self.resizable[1].convertTo("KiB")/1024))
		self.up_limit = int(floor(self.resizable[2].convertTo("KiB")/1024))
		self.current_size = int(self.resizable[3].convertTo("MiB"))
		
		self.scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=Gtk.Adjustment(0, self.down_limit, self.up_limit, 1, 10, 0))
		self.scale.set_hexpand(True)
		self.scale.set_valign(Gtk.Align.START)
		self.scale.set_digits(0)
		self.scale.set_value(self.current_size)
		self.scale.add_mark(self.down_limit,Gtk.PositionType.BOTTOM,(str(self.down_limit)))
		self.scale.add_mark(self.up_limit,Gtk.PositionType.BOTTOM,str(self.up_limit))
		
		if self.current_size not in [self.down_limit, self.up_limit]:
			self.scale.add_mark(self.current_size,Gtk.PositionType.BOTTOM,str(self.current_size))
			
		self.scale.connect("value-changed", self.scale_moved)
		
		self.grid.attach(self.scale, 0, 1, 6, 1) #left-top-width-height
		
		self.label_size = Gtk.Label()
		self.label_size.set_text(_("Volume size:"))
		self.grid.attach(self.label_size, 0, 2, 1, 1) #left-top-width-height
		
		self.spin_size = Gtk.SpinButton(adjustment=Gtk.Adjustment(0, self.down_limit, self.up_limit, 1, 10, 0))
		self.spin_size.set_numeric(True)
		self.spin_size.set_value(self.current_size)
		self.spin_size.connect("value-changed", self.spin_size_moved)
		
		self.grid.attach(self.spin_size, 1, 2, 1, 1) #left-top-width-height
		
		self.label_mb = Gtk.Label()
		self.label_mb.set_text(_("MiB"))
		self.grid.attach(self.label_mb, 2, 2, 1, 1) #left-top-width-height
		
		if self.resizable[0] == False or self.down_limit == self.up_limit:
			self.label_resize = Gtk.Label()
			self.label_resize.set_markup(_("<b>This device cannot be resized.</b>"))
			self.grid.attach(self.label_resize, 0, 0, 6, 1) #left-top-width-height
			
			self.scale.set_sensitive(False)
			self.spin_size.set_sensitive(False)
		
	def add_fs_chooser(self):
		
		self.label_format = Gtk.Label()
		self.label_format.set_text(_("Format?:"))
		self.grid.attach(self.label_format, 0, 3, 1, 1)
		
		self.format_check = Gtk.CheckButton()
		self.grid.attach(self.format_check, 1, 3, 1, 1)
		self.format_check.connect("toggled", self.on_format_changed)
		
		self.label_fs = Gtk.Label()
		self.label_fs.set_text(_("Filesystem:"))
		self.grid.attach(self.label_fs, 0, 4, 1, 1)
		
		filesystems = ["ext2", "ext3", "ext4", "xfs", "reiserfs", "vfat"]
		self.filesystems_combo = Gtk.ComboBoxText()
		self.filesystems_combo.set_entry_text_column(0)
		self.filesystems_combo.set_sensitive(False)
		
		self.filesystems_combo.connect("changed", self.filesystems_combo_changed)
		
		for fs in filesystems:
			self.filesystems_combo.append_text(fs)
		
		self.grid.attach(self.filesystems_combo,1,4,2,1)
		
		self.label_warn = Gtk.Label()
		self.grid.attach(self.label_warn, 0, 6, 6, 1)
		
	def add_name_chooser(self):
		
		self.label_entry = Gtk.Label()
		self.label_entry.set_text(_("Label:"))
		self.grid.attach(self.label_entry, 0, 4, 1, 1)
		
		self.name_entry = Gtk.Entry()
		self.grid.attach(self.name_entry,1,4,2,1)
	
	def add_mountpoint(self):
		
		self.mountpoint_label = Gtk.Label()
		self.mountpoint_label.set_text(_("Mountpoint:"))
		self.grid.attach(self.mountpoint_label, 0, 5, 1, 1)
		
		self.mountpoint_entry = Gtk.Entry()
		self.grid.attach(self.mountpoint_entry,1,5,2,1)
	
	def filesystems_combo_changed(self, event):
		
		pass
	
	def scale_moved(self,event):
		
		self.resize = True
		self.spin_size.set_value(self.scale.get_value())
		
	def spin_size_moved(self,event):
		
		self.resize = True
		self.scale.set_value(self.spin_size.get_value())
	
	def on_format_changed(self, event):
		
		if self.format_check.get_active():
			self.filesystems_combo.set_sensitive(True)
			self.label_warn.set_markup(_("<b>Warning: This will delete all data on {0}!</b>").format(self.partition_name))
		
		else:
			self.filesystems_combo.set_sensitive(False)
			self.label_warn.set_markup("")
			
	def get_selection(self):
		
		if self.format_check.get_active():
			if self.kickstart:
				return (self.resize, self.spin_size.get_value(), self.filesystems_combo.get_active_text(), self.mountpoint_entry.get_text())
			
			else:
				return (self.resize, self.spin_size.get_value(), self.filesystems_combo.get_active_text(), None)
		
		else:
			if self.kickstart:
				return (self.resize, self.spin_size.get_value(), None, self.mountpoint_entry.get_text())
			
			else:
				return (self.resize, self.spin_size.get_value(), None, None)
	
class AddDialog(Gtk.Dialog):
	""" Dialog window allowing user to add new partition including selecting size, fs, label etc.
	"""
	
	#FIXME add mountpoint validation -- os.path.isabs(path)
	def __init__(self, parent_window, device_type, parent_device, partition_name, free_space, free_pvs, kickstart=False):
		"""
			
			:param device_type: type of parent device
			:type device_type: str
			:parama parent_device: parent device
			:type parent_device: blivet.Device
			:param partition_name: name of device
			:type partition_name: str
			:param free_device: free device
			:type free_space: FreeSpaceDevice
			:param free_pvs: list PVs with no VG
			:type free_pvs: list
			:param kickstart: kickstart mode
			:type kickstart: bool
			
        """
        
		self.partition_name = partition_name
		self.free_space = free_space
		self.device_type = device_type
		self.parent_device = parent_device
		self.free_pvs = free_pvs
		self.parent_window = parent_window
		self.kickstart = kickstart
		        
		Gtk.Dialog.__init__(self, _("Create new device"), None, 0,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OK, Gtk.ResponseType.OK))
		
		self.set_transient_for(self.parent_window)
		
		self.set_border_width(10)
		self.set_default_size(600, 300)

		self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10, column_spacing=5)

		box = self.get_content_area()
		box.add(self.grid)
		
		self.add_size_scale()
		self.add_fs_chooser()
		self.add_name_chooser()
		self.add_parent_list()
		self.add_encrypt_chooser()
		self.add_device_chooser() #!important
		
		if kickstart and self.device_type in ["disk", "lvmvg"]:
			self.add_mountpoint()
		
		self.show_all()
		
	def add_device_chooser(self):
		
		map_type_devices = {
			"disk" : [_("Partition"), _("LVM2 Storage"), _("LVM2 Physical Volume")],
			"lvmpv" : [_("LVM2 Volume Group")],
			"lvmvg" : [_("LVM2 Logical Volume")],
			"luks/dm-crypt" : [_("LVM2 Volume Group")]
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
		
		if self.device_type in ["lvmpv", "luks/dm-crypt"]:
			self.filesystems_combo.set_sensitive(False)
			self.label_fs.set_sensitive(False)
			self.label_size.set_sensitive(False)
			self.label_free.set_sensitive(False)
			self.scale.set_sensitive(False)
			self.spin_size.set_sensitive(False)
			self.spin_free.set_sensitive(False)
			self.name_entry.set_sensitive(True)
			self.name_label.set_sensitive(True)
		
		self.grid.attach(self.devices_combo,1,0,2,1)
		
		self.devices_combo.connect("changed", self.on_devices_combo_changed)
		renderer_text = Gtk.CellRendererText()
		self.devices_combo.pack_start(renderer_text, True)
		self.devices_combo.add_attribute(renderer_text, "text", 0)
	
	def add_parent_list(self):
		
		self.parents_store = Gtk.ListStore(object, bool, str, str, str)
		
		self.parents = Gtk.TreeView(model=self.parents_store)
		#self.parents.set_vexpand(True)
		#self.parents.set_hexpand(True)
		
		renderer_toggle = Gtk.CellRendererToggle()
		renderer_toggle.connect("toggled", self.on_cell_toggled)
		
		renderer_text = Gtk.CellRendererText()
		
		column_toggle = Gtk.TreeViewColumn(None, renderer_toggle, active=1)
		column_name = Gtk.TreeViewColumn(_("Device"), renderer_text, text=2)
		column_type = Gtk.TreeViewColumn(_("Type"), renderer_text, text=3)
		column_size = Gtk.TreeViewColumn(_("Size"), renderer_text, text=4)
		
		self.parents.append_column(column_toggle)
		self.parents.append_column(column_name)
		self.parents.append_column(column_type)
		self.parents.append_column(column_size)
		
		self.parents.set_headers_visible(True)
		
		if self.device_type == "lvmpv":
			for pv in self.free_pvs:
				if pv.name == self.parent_device.name:
					self.parents_store.append([self.parent_device, True, self.parent_device.name, self.device_type, str(self.free_space)])
				else:
					self.parents_store.append([pv, False, pv.name, "lvmpv", str(pv.size)])
			
			self.parents.set_sensitive(True)
		
		else:
			self.parents_store.append([self.parent_device, True, self.parent_device.name, self.device_type, str(self.free_space)])
			self.parents.set_sensitive(False)
		
		self.label_list = Gtk.Label()
		self.label_list.set_text(_("Available devices:"))
		
		self.grid.attach(self.label_list, 0, 1, 1, 1)
		self.grid.attach(self.parents, 1, 1, 4, 4)
	
	def on_cell_toggled(self, event, path):
		
		if self.parents_store[path][2] == self.parent_device.name:
			pass
		
		else:
			self.parents_store[path][1] = not self.parents_store[path][1]		
	
	def add_size_scale(self):
		
		self.up_limit = int(floor(self.free_space.convertTo("KiB")/1024)) # see edit dialog for explanation
		
		self.scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=Gtk.Adjustment(0, 1, self.up_limit, 1, 10, 0))
		self.scale.set_hexpand(True)
		self.scale.set_valign(Gtk.Align.START)
		self.scale.set_digits(0)
		self.scale.set_value(self.up_limit)
		self.scale.add_mark(0,Gtk.PositionType.BOTTOM,str(1))
		self.scale.add_mark(self.up_limit,Gtk.PositionType.BOTTOM,str(self.up_limit))
		self.scale.connect("value-changed", self.scale_moved)
		
		self.grid.attach(self.scale, 0, 6, 6, 1) #left-top-width-height
		
		self.label_size = Gtk.Label()
		self.label_size.set_text(_("Volume size:"))
		self.grid.attach(self.label_size, 0, 7, 1, 1) #left-top-width-height
		
		self.spin_size = Gtk.SpinButton(adjustment=Gtk.Adjustment(0, 1, self.up_limit, 1, 10, 0))
		self.spin_size.set_numeric(True)
		self.spin_size.set_value(self.up_limit)
		self.spin_size.connect("value-changed", self.spin_size_moved)
		
		self.grid.attach(self.spin_size, 1, 7, 1, 1) #left-top-width-height
		
		self.label_mb = Gtk.Label()
		self.label_mb.set_text(_("MiB"))
		self.grid.attach(self.label_mb, 2, 7, 1, 1) #left-top-width-height
		
		self.label_free = Gtk.Label()
		self.label_free.set_text(_("Free space after:"))
		self.grid.attach(self.label_free, 3, 7, 1, 1) #left-top-width-height
		
		self.spin_free = Gtk.SpinButton(adjustment=Gtk.Adjustment(0, 0, self.up_limit, 1, 10, 0))
		self.spin_free.set_numeric(True)
		self.spin_free.connect("value-changed", self.spin_free_moved)
		
		self.grid.attach(self.spin_free, 4, 7, 1, 1) #left-top-width-height
		
		self.label_mb2 = Gtk.Label()
		self.label_mb2.set_text(_("MiB"))
		self.grid.attach(self.label_mb2, 5, 7, 1, 1) #left-top-width-height
		
	def add_fs_chooser(self):
		
		self.label_fs = Gtk.Label()
		self.label_fs.set_text(_("Filesystem:"))
		self.grid.attach(self.label_fs, 0, 8, 1, 1)
		
		filesystems = ["ext2", "ext3", "ext4", "xfs", "reiserfs", "swap", "vfat"]
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
	
	def add_encrypt_chooser(self):
		
		self.encrypt_label = Gtk.Label()
		self.encrypt_label.set_text(_("Encrypt:"))
		self.grid.attach(self.encrypt_label, 0, 10, 1, 1)
		self.encrypt_label.set_sensitive(False)
		
		self.encrypt_check = Gtk.CheckButton()
		self.grid.attach(self.encrypt_check, 1, 10, 1, 1)
		self.encrypt_check.connect("toggled", self.on_encrypt_changed)
		self.encrypt_check.set_sensitive(False)
		
		self.passphrase_label = Gtk.Label()
		self.passphrase_label.set_text(_("Passphrase:"))
		self.grid.attach(self.passphrase_label, 3, 10, 1, 1)
		self.passphrase_label.set_sensitive(False)
		
		self.passphrase_entry = Gtk.Entry()
		self.passphrase_entry.set_visibility(False)
		self.passphrase_entry.set_property("caps-lock-warning", True)
		self.grid.attach(self.passphrase_entry,4,10,2,1)
		self.passphrase_entry.set_sensitive(False)
		
	def add_mountpoint(self):
		
		self.mountpoint_label = Gtk.Label()
		self.mountpoint_label.set_text(_("Mountpoint:"))
		self.grid.attach(self.mountpoint_label, 0, 11, 1, 1)
		
		self.mountpoint_entry = Gtk.Entry()
		self.grid.attach(self.mountpoint_entry,1,11,2,1)
		
		if self.device_type not in ["lvmvg", "disk"]:
			self.label_label.set_sensitive(False)
			self.label_entry.set_sensitive(False)
			
	def on_encrypt_changed(self, event):
		
		self.passphrase_entry.set_sensitive(not self.passphrase_entry.get_sensitive())
		self.passphrase_label.set_sensitive(not self.passphrase_label.get_sensitive())
	
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
				
				self.filesystems_combo.set_sensitive(True)
				self.label_fs.set_sensitive(True)
				
				self.encrypt_label.set_sensitive(False)
				self.encrypt_check.set_sensitive(False)
				
				if self.kickstart:
					self.mountpoint_label.set_sensitive(True)
					self.mountpoint_entry.set_sensitive(True)
				
			if device == _("LVM2 Physical Volume"):
				self.label_label.set_sensitive(False)
				self.label_entry.set_sensitive(False)
				
				self.name_label.set_sensitive(False)
				self.name_entry.set_sensitive(False)
				
				self.filesystems_combo.set_sensitive(False)
				self.label_fs.set_sensitive(False)
				
				self.encrypt_label.set_sensitive(True)
				self.encrypt_check.set_sensitive(True)
				
				if self.kickstart:
					self.mountpoint_label.set_sensitive(False)
					self.mountpoint_entry.set_sensitive(False)
			
			if device == _("LVM2 Storage"):
				self.label_label.set_sensitive(False)
				self.label_entry.set_sensitive(False)
				
				self.name_label.set_sensitive(True)
				self.name_entry.set_sensitive(True)
				
				self.filesystems_combo.set_sensitive(False)
				self.label_fs.set_sensitive(False)
				
				self.encrypt_label.set_sensitive(False)
				self.encrypt_check.set_sensitive(False)
				
				if self.kickstart:
					self.mountpoint_label.set_sensitive(False)
					self.mountpoint_entry.set_sensitive(False)
	
	def scale_moved(self,event):
		
		self.spin_size.set_value(self.scale.get_value())
		self.spin_free.set_value(self.up_limit - self.scale.get_value())
		
	def spin_size_moved(self,event):
		
		self.scale.set_value(self.spin_size.get_value())
		self.spin_free.set_value(self.up_limit - self.scale.get_value())
		
	def spin_free_moved(self,event):
		
		self.scale.set_value(self.up_limit - self.spin_free.get_value())
		self.spin_size.set_value(self.up_limit - self.spin_free.get_value())
	
	def get_selection(self):
		tree_iter = self.devices_combo.get_active_iter()
		
		if tree_iter != None:
			model = self.devices_combo.get_model()
			device = model[tree_iter][0]
		
		if device == "LVM2 Volume Group":
			parents = []
			size = 0
			
			for row in self.parents_store:
				if row[1]:
					parents.append(row[0])
					size += row[0].size
			
			return (device, int(size.convertTo("MiB")), self.filesystems_combo.get_active_text(), 
				self.name_entry.get_text(), self.label_entry.get_text(), parents)
		
		if self.kickstart:
			return (device, self.spin_size.get_value(),
				self.filesystems_combo.get_active_text(), self.name_entry.get_text(), 
				self.label_entry.get_text(), self.mountpoint_entry.get_text(), 
				self.encrypt_check.get_active(), {"passphrase" : self.passphrase_entry.get_text()})
		
		else:
			return (device, self.spin_size.get_value(),
				self.filesystems_combo.get_active_text(), self.name_entry.get_text(), 
				self.label_entry.get_text(), None, self.encrypt_check.get_active(), {"passphrase" : self.passphrase_entry.get_text()})
	
class AddLabelDialog(Gtk.Dialog):
	""" Dialog window allowing user to add disklabel to disk
	"""
	
	def __init__(self, disk_name, parent_window):
		"""
		
			:param parent_window: parent window
			:type parent_window: Gtk.Window
			:param disk_name: name of the disk
			:type disk_name: str
			
		"""
		
		self.disk_name = disk_name
		self.parent_window = parent_window
        
		Gtk.Dialog.__init__(self, _("No partition table found on disk"), None, 0,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OK, Gtk.ResponseType.OK))
		
		self.set_transient_for(self.parent_window)
		
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
	
class AboutDialog(Gtk.AboutDialog):
	""" Standard 'about application' dialog
	"""
	
	def __init__(self, parent_window):
		Gtk.AboutDialog.__init__(self)
		
		self.parent_window = parent_window
		
		self.set_transient_for(self.parent_window)
		
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

class KickstartFileSaveDialog(Gtk.FileChooserDialog):
	""" File choose dialog for kickstart file save
	"""
	
	def __init__(self, parent_window):
		Gtk.FileChooserDialog.__init__(self, _("Please choose a folder"), None,
						Gtk.FileChooserAction.SAVE,
						(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
						_("Select"), Gtk.ResponseType.OK))
		
		self.parent_window = parent_window
		
		self.set_transient_for(self.parent_window)
		self.set_default_size(800, 400)

class KickstartSelectDevicesDialog(Gtk.Dialog):
	""" Dialog window allowing user to select which devices will be used in kickstart mode
	"""
	
	def __init__(self, parent_window, blivet_disks):
		"""
			
			:param parent_window: parent_window
			:type parent_window: Gtk.Window
			:param blivet_disks: disks in the system
			:type blivet_disks: blivet.Device
			
		"""
        
		self.parent_window = parent_window
		self.blivet_disks = blivet_disks
		        
		Gtk.Dialog.__init__(self, _("Select devices"), None, 0,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OK, Gtk.ResponseType.OK))
			
		self.set_transient_for(self.parent_window)
		
		self.set_border_width(10)
		
		self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10, column_spacing=5)
		
		box = self.get_content_area()
		box.add(self.grid)
		
		self.add_device_list()
		self.add_bootloader_chooser()
		
		self.show_all()
	
	def add_device_list(self):
		
		self.disks_store = Gtk.ListStore(object, bool, GdkPixbuf.Pixbuf, str)
		
		self.disks_view = Gtk.TreeView(model=self.disks_store)
		#self.parents.set_vexpand(True)
		#self.parents.set_hexpand(True)
		
		renderer_toggle = Gtk.CellRendererToggle()
		renderer_toggle.connect("toggled", self.on_cell_toggled)		
		column_toggle = Gtk.TreeViewColumn(None, renderer_toggle, active=1)
		self.disks_view.append_column(column_toggle)
		
		renderer_pixbuf = Gtk.CellRendererPixbuf()
		column_pixbuf = Gtk.TreeViewColumn(None, renderer_pixbuf, pixbuf=2)
		self.disks_view.append_column(column_pixbuf)
		
		renderer_text = Gtk.CellRendererText()
		column_text = Gtk.TreeViewColumn('Pango Markup', renderer_text, markup=3)
		self.disks_view.append_column(column_text)
		
		self.disks_view.set_headers_visible(False)
		
		icon_theme = Gtk.IconTheme.get_default()
		icon_disk = Gtk.IconTheme.load_icon (icon_theme,"drive-harddisk",32, 0)
		icon_disk_usb = Gtk.IconTheme.load_icon (icon_theme,"drive-removable-media",32, 0)
		
		for disk in self.blivet_disks:
			if disk.removable:
				self.disks_store.append([disk,False,icon_disk_usb,str(disk.name +
											   "\n<i><small>" + disk.model + "</small></i>")])
			else:
				self.disks_store.append([disk,False,icon_disk,str(disk.name +
										   "\n<i><small>" + disk.model + "</small></i>")])
		
		self.label_list = Gtk.Label()
		self.label_list.set_text(_("Please select at least one of shown devices:"))
		
		self.grid.attach(self.label_list, 0, 1, 1, 1) #left-top-width-height
		self.grid.attach(self.disks_view, 0, 2, 4, 4)
	
	def on_cell_toggled(self, event, path):
		
		self.disks_store[path][1] = not self.disks_store[path][1]
	
	def add_bootloader_chooser(self):
		
		self.label_boot = Gtk.Label()
		self.label_boot.set_text(_("Install bootloader?:"))
		self.grid.attach(self.label_boot, 0, 7, 1, 1)
		
		self.boot_check = Gtk.CheckButton()
		self.grid.attach(self.boot_check, 1, 7, 1, 1)
		self.boot_check.connect("toggled", self.on_boot_changed)
		
		self.label_boot_device = Gtk.Label()
		self.label_boot_device.set_text(_("Device to install bootloader:")) #FIXME less stupid label
		self.grid.attach(self.label_boot_device, 0, 8, 1, 1)
		
		self.boot_device_combo = Gtk.ComboBoxText()
		self.boot_device_combo.set_entry_text_column(0)
		self.boot_device_combo.set_sensitive(False)
		self.grid.attach(self.boot_device_combo, 1, 8, 2, 1)
		
		for disk in self.blivet_disks:
			self.boot_device_combo.append_text(disk.name)
		
		self.boot_device_combo.connect("changed", self.on_boot_device_combo_changed)
	
	def on_boot_changed(self, event):
		
		self.boot_device_combo.set_sensitive(not self.boot_device_combo.get_sensitive())
	
	def on_boot_device_combo_changed(self, event):
		pass
	
	def get_selection(self):
		
		selected_disks_names = []
		
		for row in self.disks_store:
			if row[1]:
				selected_disks_names.append(row[0].name)
		
		return (selected_disks_names, self.boot_device_combo.get_sensitive() , self.boot_device_combo.get_active_text())

class KickstartAutoIgnoreDialog(Gtk.MessageDialog):
	""" Dialog window informing user about ignored devices in kickstart mode
	"""
	
	def __init__(self, parent_window, devices):
		"""
			:param parent_window: parent window
			:type parent_window: Gtk.Window
			:param devices: raised exception
			:type devices: str
		"""
		
		self.parent_window = parent_window
		
		Gtk.MessageDialog.__init__(self, None, 0, 
			Gtk.MessageType.ERROR,
			Gtk.ButtonsType.OK, 
			_("Following disk will be ignored"))
		
		self.set_transient_for(self.parent_window)
		
		info_str = "blivet-gui in kickstart mode can't work with disks with" \
			"active mounts, following disks will be ignored:\n\n"
		
		for device in devices:
			info_str = info_str + "\t• " + device + "\n"
		
		self.format_secondary_text(info_str)
		
		self.show_all()
		
		self.connect("delete-event", Gtk.main_quit)
		self.run()
		self.destroy()

class KickstartDuplicateMountpointDialog(Gtk.MessageDialog):
	""" Dialog window informing user about duplicate mountpoints in kickstart mode
	"""
	
	def __init__(self, parent_window, mountpoint, old_device):
		"""
		
			:param parent_window: parent window
			:type parent_window: Gtk.Window
			:param mountpoint: duplicate mountpoint
			:type mountpoint: str
			:param old_device: existing device with same mountpoint
			:type old_device: str
			
		"""
		
		self.parent_window = parent_window
		
		Gtk.Dialog.__init__(self, _("Duplicate mountpoint detected"), None, Gtk.MessageType.WARNING,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OK, Gtk.ResponseType.OK))
		
		self.set_transient_for(self.parent_window)
		
		self.set_default_size(175, 110)
		
		info_str = _("Selected mountpoint \"{0}\" is already used for \"{1}\" device. Do you want to remove this mountpoint?").format(mountpoint, old_device)
		
		self.format_secondary_text(info_str)
		
		self.show_all()
		

class LuksPassphraseDialog(Gtk.Dialog):
	""" Dialog window allowing user to enter passphrase to decrypt 
	"""
	
	def __init__(self, parent_window, device_name):
		"""
		
			:param parent_window: parent window
			:type parent_window: Gtk.Window
			:param device_name: name of device to decrypt
			:type device_name: str
			
		"""
		
		self.parent_window = parent_window
		self.device_name = device_name
		
		Gtk.Dialog.__init__(self, _("Enter passphrase to decrypt {0}").format(self.device_name), None, 0,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OK, Gtk.ResponseType.OK))
		
		self.set_transient_for(self.parent_window)
		
		self.set_default_size(250, 100)
		self.set_border_width(10)
		
		self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10, column_spacing=5)
		
		box = self.get_content_area()
		box.add(self.grid)
		
		self.pass_label = Gtk.Label()
		self.pass_label.set_markup(_("Passphrase:"))
		
		self.grid.attach(self.pass_label, 0, 0, 1, 1) #left-top-width-height
		
		self.pass_entry = Gtk.Entry()
		self.pass_entry.set_visibility(False)
		self.pass_entry.set_property("caps-lock-warning", True)
		
		self.grid.attach(self.pass_entry, 1, 0, 2, 1)
		
		self.show_all()
		
	def get_selection(self):
		
		return self.pass_entry.get_text()