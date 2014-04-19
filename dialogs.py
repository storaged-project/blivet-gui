#!/usr/bin/python2
 
import sys, os, signal

import gettext

from gi.repository import Gtk, GdkPixbuf

APP_NAME = "blivet-gui"

gettext.bindtextdomain(APP_NAME, 'po')
gettext.textdomain(APP_NAME)
_ = gettext.gettext
 
class RootTestDialog(Gtk.MessageDialog):
	
	def __init__(self,parent):
		Gtk.MessageDialog.__init__(self, parent, 0, Gtk.MessageType.ERROR,Gtk.ButtonsType.CANCEL, _("Root privileges required"))
		format_secondary_text = _("Root privileges are required for running blivet-gui.")
		
		self.connect("delete-event", Gtk.main_quit)
		self.run()
		self.destroy()