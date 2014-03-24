#!/usr/bin/env python
import sys
import secondWindow
import lastWindow

from gi.repository import Gtk

gladefile = "template-gui.glade"

class firstWindow(object):

    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(gladefile)
        self.firstWin = self.builder.get_object("firstWindow")
        self.entrytextview = self.builder.get_object("entrytextview")
        self.secondWin = secondWindow.secondWindow(self, self.firstWin, self.builder)
        self.lastWin = lastWindow.lastWindow(self, self.secondWin, self.builder)
        self.mainhandlers = {
                    "on_nextBtn_first_clicked": self.next_window,
                    "on_browse_clicked": self.browse_path,
                    "on_cancel_clicked": Gtk.main_quit,
                    "on_cancelSecond_clicked": Gtk.main_quit,
                    "on_quit_clicked": Gtk.main_quit,
                    "on_prevSecond_clicked": self.secondWin.prev_window,
                    "on_nextSecond_clicked": self.secondWin.next_window,
                    "on_prevLast_clicked": self.lastWin.prev_window,
                    "on_mainWindow_delete_event": Gtk.main_quit,
                    "on_cancelBtn_clicked": Gtk.main_quit,
                    "on_firstWindow_delete_event": Gtk.main_quit,
                    "on_secondWindow_delete_event": Gtk.main_quit,
                    "on_lastWindow_delete_event": Gtk.main_quit,
                    "on_store_view_cursor_changed": self.store_view_cursor_changed,
                    "on_treeview_cursor_changed": self.secondWin.cursor_changed,
                    "on_centeredBtn_clicked" : self.lastWin.centered_clicked,
                    "on_editBtn_clicked" : self.lastWin.editable_clicked,
                    "on_listviewexample_cursor_changed": self.store_view_cursor_changed,
                        }
        self.builder.connect_signals(self.mainhandlers)
        self.listView = self.builder.get_object("listviewexample")
        self.entryText = self.builder.get_object("entryText")
        self.store = Gtk.ListStore(int, str,str)

        self.listView.set_model(self.store)
        self.store.append([1,"Paul Jones","pjones@gmail.com"])
        self.store.append([2,"Maria Doe", "mdoe@hotmail.com"])
        self.store.append([3,"Silvester Rambo","srambo@yahoo.com"])

        renderer = Gtk.CellRendererText()
        columnID = Gtk.TreeViewColumn("ID", renderer, text=0)
        columnID.set_sort_column_id(0)
        self.listView.append_column(columnID)
        rendererName = Gtk.CellRendererText()
        columnName = Gtk.TreeViewColumn("Name", renderer, text=1)
        columnName.set_sort_column_id(1)
        self.listView.append_column(columnName)
        rendererStreet = Gtk.CellRendererText()
        columnStreet = Gtk.TreeViewColumn("Email", renderer, text=2)
        columnStreet.set_sort_column_id(2)
        self.listView.append_column(columnStreet)
        self.firstWin.show_all()
        Gtk.main()

    def browse_path(self, window):
        dialog = Gtk.FileChooserDialog(
            "Please choose directory", self.firstWin,
            Gtk.FileChooserAction.SELECT_FOLDER,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
            )
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.entryText.set_text(dialog.get_filename())
        dialog.destroy()

    def next_window(self, widget, data=None):
        self.secondWin.open_window(widget, data=None)
        self.firstWin.hide()

    def open_window(self, widget, data=None):
        self.firstWin.show_all()

    def store_view_cursor_changed(self, selection):
        select = selection.get_selection()
        if select != None:
            (model, path_list) = select.get_selected()
            if path_list != None:
                row = model[path_list]
                self.entrytextview.set_text("{0} - {1}({2})".format(row[0],row[1],row[2]))
