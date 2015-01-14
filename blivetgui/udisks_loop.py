from threading import Thread

import dbus
from dbus.mainloop.glib import DBusGMainLoop

class udisks_thread(Thread):
    def __init__(self):
        Thread.__init__(self)
        DBusGMainLoop(set_as_default=True)

        bus = dbus.SystemBus()
        proxy = bus.get_object('org.freedesktop.UDisks',
            '/org/freedesktop/UDisks')
        iface = dbus.Interface(proxy, 'org.freedesktop.UDisks')
        devices = iface.get_dbus_method('EnumerateDevices')()

        iface.connect_to_signal('DeviceAdded', self.on_device_added)
        iface.connect_to_signal('DeviceRemoved', self.on_device_removed)

    def on_device_added(self, device):
        print device, "added"

        # FIXME bad idea
        # self.l.b.blivet_reset()
        # self.l.update_devices_view()
        # this has to be ignored when doing doIt()

    def on_device_removed(self, device):
        print device, "removed"
