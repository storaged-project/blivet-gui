# -*- coding: utf-8 -*-
"""
Created on Wed Apr  3 13:16:47 2013

@author: Petr Hracek
"""

import os
from gi.repository import Gtk

class secondWindow(object):
    def __init__(self, parent, firstWin, builder):
        self.parent = parent
        self.firstWin = firstWin
        self.secondWindow = builder.get_object("secondWindow")
        self.builder = builder
        self.treeview = builder.get_object("treeview")
        self.entrytree = builder.get_object("entryTree")
        self.treestore = Gtk.TreeStore(str,str)
        first_iter = self.treestore.append(None, ['Childs books','Zdenek Miler and Karel Capek'])
        self.treestore.append(first_iter,['Little Mole', 'Zdenek Miler'])
        self.treestore.append(first_iter,['Dasenka', 'Karel Capek'])
        first_iter = self.treestore.append(None, ['Dramatic', 'Czech authors'])
        self.treestore.append(first_iter,['RUR', 'Karel Capek'])
        self.treestore.append(first_iter,['The Makropolus Affair', 'Karel Capek'])
        self.treeview.set_model(self.treestore)
        renderer = Gtk.CellRendererText()
        self.tvcolumn = Gtk.TreeViewColumn("Title and Author")
        title = Gtk.CellRendererText()
        author = Gtk.CellRendererText()
        self.tvcolumn.pack_start(title,True)
        self.tvcolumn.pack_start(author,True)
        self.tvcolumn.add_attribute(title, "text", 0)
        self.tvcolumn.add_attribute(author, "text", 1)
        # This is used for one column tree
        #self.tvcolumn = Gtk.TreeViewColumn('Column 0',renderer, text=0)
        self.treeview.append_column(self.tvcolumn)
                
        
    def cursor_changed(self, selection):
        select = selection.get_selection()
        (model, treeiter) = select.get_selected()
        if treeiter != None:
            self.entrytree.set_text("%s - %s" % (model[treeiter][1] , model[treeiter][0]))

    def open_window(self, widget, data=None):
        self.secondWindow.show_all()
   
    def prev_window(self, widget, data=None):
        self.secondWindow.hide()
        self.parent.open_window(widget, data)
    
    def next_window(self, widget, data=None):
        self.parent.lastWin.open_window(widget,data)
        self.secondWindow.hide()
