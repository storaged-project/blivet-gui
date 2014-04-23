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
 
import sys, os, signal

import gettext

from gi.repository import Gtk, GdkPixbuf

APP_NAME = "blivet-gui"

gettext.bindtextdomain(APP_NAME, 'po')
gettext.textdomain(APP_NAME)
_ = gettext.gettext
 
class RootTestDialog(Gtk.MessageDialog):
	""" Dialog window informing user to run blivet-gui as root	
	"""
	
	def __init__(self):
		Gtk.MessageDialog.__init__(self, None, 0, Gtk.MessageType.ERROR,Gtk.ButtonsType.CANCEL, _("Root privileges required"))
		format_secondary_text = _("Root privileges are required for running blivet-gui.")
		
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

		self.set_default_size(160, 110)

		label = Gtk.Label(_("Are you sure you want to delete device %(device_name)s" % locals()))

		box = self.get_content_area()
		box.add(label)
		self.show_all()


class AddDialog(Gtk.Dialog):
	""" Confirmation dialog for device deletion
	"""
	def __init__(self,partition_name, free_space):
		"""
            :param free_space: size of selected free space
            :type free_space: int
        """
        
		self.free_space = free_space
        
		Gtk.Dialog.__init__(self, _("Create new partition"), None, 0,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OK, Gtk.ResponseType.OK))

		self.set_default_size(450, 300)

		self.grid = Gtk.Grid(column_homogeneous=False)

		box = self.get_content_area()
		box.add(self.grid)
		
		self.scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=Gtk.Adjustment(0, 1, self.free_space, 1, 10, 0))
		self.scale.set_hexpand(True)
		self.scale.set_valign(Gtk.Align.START)
		self.scale.set_digits(0)
		self.scale.set_value(self.free_space)
		self.scale.connect("value-changed", self.scale_moved)
		
		self.grid.attach(self.scale, 0, 0, 6, 1) #left-top-width-height
		
		self.label_size = Gtk.Label()
		self.label_size.set_text(_("Volume size"))
		self.grid.attach(self.label_size, 0, 1, 1, 1) #left-top-width-height
		
		self.spin_size = Gtk.SpinButton(adjustment=Gtk.Adjustment(0, 1, self.free_space, 1, 10, 0))
		self.spin_size.set_numeric(True)
		self.spin_size.set_value(self.free_space)
		self.spin_size.connect("value-changed", self.spin_size_moved)
		
		self.grid.attach(self.spin_size, 1, 1, 1, 1) #left-top-width-height
		
		self.label_free = Gtk.Label()
		self.label_free.set_text(_("Free space after"))
		self.grid.attach(self.label_free, 4, 1, 1, 1) #left-top-width-height
		
		self.spin_free = Gtk.SpinButton(adjustment=Gtk.Adjustment(0, 0, self.free_space, 1, 10, 0))
		self.spin_free.set_numeric(True)
		self.spin_free.connect("value-changed", self.spin_free_moved)
		
		self.grid.attach(self.spin_free, 5, 1, 1, 1) #left-top-width-height
		
		
		self.show_all()
	
	def scale_moved(self,event):
		
		self.spin_size.set_value(self.scale.get_value())
		self.spin_free.set_value(self.free_space - self.scale.get_value())
		
	def spin_size_moved(self,event):
		
		self.scale.set_value(self.spin_size.get_value())
		self.spin_free.set_value(self.free_space - self.scale.get_value())
		
	def spin_free_moved(self,event):
		
		self.scale.set_value(self.free_space - self.spin_free.get_value())
		self.spin_size.set_value(self.free_space - self.spin_free.get_value())
