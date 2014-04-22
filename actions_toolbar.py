# list_partitions.py
# Toolbar class
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

APP_NAME = "blivet-gui"

gettext.bindtextdomain(APP_NAME, 'po')
gettext.textdomain(APP_NAME)
_ = gettext.gettext

class actions_toolbar():
	def __init__(self,list_partitions):
		self.list_partitions = list_partitions
		self.toolbar = Gtk.Toolbar()
		self.buttons = {}
		
		self.create_buttons()
		
	def create_buttons(self):
		
		button_new = Gtk.ToolButton.new_from_stock(Gtk.STOCK_ADD)
		button_new.set_sensitive(False)
		button_new.set_tooltip_text(_("Create new partition"))
		self.toolbar.insert(button_new, 0)
		self.buttons["new"] = button_new
		
		button_delete = Gtk.ToolButton.new_from_stock(Gtk.STOCK_DELETE)
		button_delete.set_sensitive(False)
		button_delete.set_tooltip_text(_("Delete selected partition"))
		self.toolbar.insert(button_delete, 1)
		self.buttons["delete"] = button_delete
		
		self.toolbar.insert(Gtk.SeparatorToolItem(), 2)
		
		button_edit = Gtk.ToolButton.new_from_stock(Gtk.STOCK_EDIT)
		button_edit.set_sensitive(False)
		button_edit.set_tooltip_text(_("Move or resize partition"))
		self.toolbar.insert(button_edit, 3)
		self.buttons["edit"] = button_edit
	
	def activate_buttons(self,button_names):
		
		for button in button_names:
			self.buttons[button].set_sensitive(True)
		
	def deactivate_buttons(self,button_names):
		
		for button in button_names:
			self.buttons[button].set_sensitive(False)
			
	def deactivate_all(self):
		
		for button in self.buttons.values():
			button.set_sensitive(False)
	
	def get_toolbar(self):
		return self.toolbar
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
