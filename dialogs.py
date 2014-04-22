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
	
	def __init__(self):
		Gtk.MessageDialog.__init__(self, None, 0, Gtk.MessageType.ERROR,Gtk.ButtonsType.CANCEL, _("Root privileges required"))
		format_secondary_text = _("Root privileges are required for running blivet-gui.")
		
		self.connect("delete-event", Gtk.main_quit)
		self.run()
		self.destroy()
		

class ConfirmDeleteDialog(Gtk.Dialog):
	
	def __init__(self,partition_name):
		Gtk.Dialog.__init__(self, _("Confirm delete operation"), None, 0,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OK, Gtk.ResponseType.OK))

		self.set_default_size(150, 100)

		label = Gtk.Label(_("Are you sure you want to delete partition %(partition_name)s" % locals()))

		box = self.get_content_area()
		box.add(label)
		self.show_all()