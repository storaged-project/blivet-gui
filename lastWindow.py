# -*- coding: utf-8 -*-
"""
Created on Wed Apr  3 13:16:47 2013

@author: Petr Hracek
"""

import sys
import logging
from gi.repository import Gtk

class lastWindow(object):
    def __init__(self,  parent, secondWindow, builder):
        self.parent = parent
        self.secondWindow = secondWindow
        self.lastWindow = builder.get_object("lastWindow")
        self.textViewLog = builder.get_object("textview")
        self.centerBtn = builder.get_object("centeredBtn")
        self.editBtn = builder.get_object("editBtn")
        self.textbuffer = self.textViewLog.get_buffer()
        self.textViewLog.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.center = 0
        self.editable = 1
        self.editBtn.set_label("Disable editing")
        self.centerBtn.set_label("Text centered")

    def open_window(self, widget, data=None):
        #logger.info("main function")
        self.lastWindow.show_all()


    def visibility_event(self, widget, data=None):
        logging.info("Visibility event")

    def prev_window(self, widget, data=None):
        self.secondWindow.open_window(widget, data)
        self.lastWindow.hide()

    def centered_clicked(self, widget, data=None):
        if self.center == 0:
            self.textViewLog.set_justification(Gtk.Justification.CENTER)
            self.center = 1
            self.centerBtn.set_label("Text at the left edge")
        else:
            self.textViewLog.set_justification(Gtk.Justification.LEFT)
            self.center = 0
            self.centerBtn.set_label("Text centered")

    def editable_clicked(self, widget, data=None):
        if self.editable == 0:
            self.editable = 1
            self.textViewLog.set_editable(self.editable)
            self.textViewLog.set_cursor_visible(self.editable)
            self.editBtn.set_label("Disable editing")
        else:
            self.editable = 0
            self.textViewLog.set_editable(self.editable)
            self.textViewLog.set_cursor_visible(self.editable)
            self.editBtn.set_label("Make editable")
