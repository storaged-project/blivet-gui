#!/usr/bin/python2
from gi.repository import Gtk
from gi.repository.GdkPixbuf import Pixbuf


actresses = [i.strip().replace("'", "").split() for i in open("lista.txt").readlines()]


class PyApp(Gtk.Window): 
    def __init__(self):
        super(PyApp, self).__init__()

        self.set_size_request(350, 250)
        self.set_position(Gtk.WIN_POS_CENTER)

        self.connect("destroy", Gtk.main_quit)
        self.set_title("ListView")

        self.Boton = Gtk.Button("click")
        self.Boton.connect("clicked",self.create_list)

        self.Boton.show()

        vbox = Gtk.VBox(False, 8)

        sw = Gtk.ScrolledWindow()
        sw.set_shadow_type(Gtk.SHADOW_ETCHED_IN)
        sw.set_policy(Gtk.POLICY_AUTOMATIC, Gtk.POLICY_AUTOMATIC)

        vbox.pack_start(sw, True, True, 0)
        vbox.pack_start(self.Boton, True, True, 0)

        store = self.create_model()

        treeView = Gtk.TreeView(store)
        treeView.connect("row-activated", self.on_activated)
        treeView.set_rules_hint(True)
        sw.add(treeView)

        self.create_columns(treeView)
        self.statusbar = Gtk.Statusbar()

        vbox.pack_start(self.statusbar, False, False, 0)

        self.add(vbox)
        self.show_all()


    def create_model(self):
        store = Gtk.ListStore(str, str, str)

        for act in actresses:
            store.append([act[0], act[1], act[2]])

        return store


    def create_columns(self, treeView):

        rendererText = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Nombre", rendererText, text=0)
        column.set_sort_column_id(0)    
        treeView.append_column(column)

        rendererText = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("apellido", rendererText, text=1)
        column.set_sort_column_id(1)
        treeView.append_column(column)

        rendererText = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Tamano", rendererText, text=2)
        column.set_sort_column_id(2)
        treeView.append_column(column)


    def on_activated(self, widget, row, col):

        model = widget.get_model()
        text = model[row][0] + ", " + model[row][1] + ", " + model[row][2]
        self.statusbar.push(0, text)
    if model[row][0] == "lol":
       print "Funciona"

    def create_list(self, widget):
        # create a TreeView object which will work with our model (ListStore)
        self.listview = self.create_model()
        self.treeView = Gtk.TreeView(self.listview)
        self.treeView.set_rules_hint(True)

PyApp()
Gtk.main()