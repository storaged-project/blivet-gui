from gi.repository import Gtk

win = Gtk.Window()
win.connect("delete-event", Gtk.main_quit)
win.show_all()


socket = Gtk.Socket()
socket.show()
window.add(socket)

Gtk.main()

