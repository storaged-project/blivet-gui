# -*- coding: utf-8 -*-
# embeded.py
# Example of blivet-gui embeded in another window
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

import subprocess, time

import gettext

from gi.repository import Gtk, GdkPixbuf, Gdk, GLib

#------------------------------------------------------------------------------#

dirname, filename = os.path.split(os.path.abspath(__file__))

gettext.install('messages', dirname + '/i18n', unicode=True)
_ = gettext.gettext

#------------------------------------------------------------------------------#

class SocketWindow(Gtk.Window):
	""" Example Gtk.Window for blivet-gui embedding test
	"""
	
	def __init__(self):
		Gtk.Window.__init__(self, title="Embeded Window Example")
		
		self.set_default_size(800, 600)
		
		socket = Gtk.Socket()
		self.add(socket)
		
		socket_id = None
		
		process = subprocess.Popen(["python2",  dirname + "/main.py", "-e"])

		socket_id = raw_input("Enter the ID printed above:\n")
		socket.add_id(int(socket_id))
		
		self.connect("destroy", lambda w: Gtk.main_quit())
		socket.connect("plug-added", self.plugged_event)
		
		self.show_all()
	
	def plugged_event(self, widget):
		print "A plug has been inserted."

window = SocketWindow()
Gtk.main()