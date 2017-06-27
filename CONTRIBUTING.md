## blivet-gui developer documentation

### Development

#### Running from source

To run blivet-gui directly from source without installing it (e.g. to test some
changes) clone the repo (or download a release tarball) and from directory with
the source run

```
PYTHONPATH=. PATH=`pwd`:$PATH blivet-gui
```

(You still need to install blivet-gui dependencies to be able to run it. See
[README.md](README.md) for more information.)

#### Running the tests

  * `make test`
    * run blivet-gui tests
    * this test suite needs a graphical session (or a "fake" one like _Xvfb_) to run
  * `make check`
    * run static code checks (_pylint_, _pep8_ and _translation canary_)
    * it is possible to run these separately -- `make pep8`, `make pylint` or
      `make canary`
  * `sudo install-requires`
    * install some addition dependencies needed for tests (uses _dnf_)

### Contributing

#### Branches

  * `master` is the only "active development" branch, new features should go
    to this branch
  * only bug fixes are being added to the "older" branches
    * names are currently based on the Fedora releases
      * `f25-devel` -- blivet-gui 2.0.x
      * `f24-devel` -- blivet-gui 1.2.x
      * `f23-devel` -- blivet-gui 1.0.x (not supported)
      * `f22-devel` -- blivet-gui 0.2.x (not supported)

#### Code style

  * `pep8` and `pylint` are used to check the code, see __Running the tests__
    * some checks are disabled, e.g. check for maximum line length (try to keep
      lines under 100 characters but avoid "artificial" line breaks just to keep
      lines short)

### Building blocks of blivet-gui

This is just a short summary of blivet-gui code structure/building blocks.
See [rhinstaller.github.io/blivet-gui/doc](https://rhinstaller.github.io/blivet-gui/docs)
for a complete API documentation.

#### BlivetUtils

`BlivetUtils` ([blivet_utils.py](blivetgui/blivet_utils.py)) class provides a higher level API for Blivet library.
It creates the `blivet.Blivet` object and all blivet methods are called using this class.

Check [Blivet API documentation](http://rhinstaller.github.io/blivet/docs/intro.html)
for more information about blivet and its API.

#### BlivetGUI

`BlivetGUI` ([blivetgui.py](blivetgui/blivetgui.py)) is the main class for the GUI.
There are separate classes for every UI part. These classes create all the necessary
Gtk widgets (or load them from the Glade files and provide signal handlers and
other helper functions.

**Important GUI objects:**

  * `ActionsMenu` ([actions_menu.py](blivetgui/actions_menu.py)) -- context (right
    click) menu for user actions
  * `DeviceToolbar` ([actions_toolbar.py](blivetgui/actions_toolbar.py)) -- toolbar
    with device-related actions (add, edit, remove...)
  * `ActionsToolbar` ([actions_toolbar.py](blivetgui/actions_toolbar.py))-- toolbar
    with "global" actions (process or clear actions, main menu)
  * `ListDevices` ([list_devices.py](blivetgui/list_devices.py)])-- list of "root"
    devices (disks, volume groups, RAIDs...)
  * `ListPartitions` ([list_partitions.py](blivetgui/list_partitions.py)) -- list
    of "child" devices for selected device
      * Gets list of "child" devices for given device.
      * Decides what "actions" (add, delete...) should be allowed based on current
        selection.
      * Displays list of "child" devices using `Gtk.TreeView`.
  * `LogicalView` ([visualization/logical_view.py](blivetgui/visualization/logical_view.py)) --
    visualization of child devices. These actually are buttons (`Gtk.Button`) styled
    with css (see [rectangle.css](data/css/rectangle.css))
  * `PhysicalView` ([visualization/physical_view.py](blivetgui/visualization/physical_view.py)) --
    visualization of parents for selected devices.

Most GUI objects are created using the [Glade](https://glade.gnome.org/) designer.
See files in [data/ui](data/ui).

#### Dialogs

Most of the user interaction is done using dialogs. Some important dialogs include:

  * `AddDialog` ([dialogs/add_dialog.py](blivetgui/dialogs/add_dialog.py)) -- a dialog
    for adding new devices
  * `ResizeDialog` ([dialogs/edit_dialog.py](blivetgui/dialogs/edit_dialog.py)) -- a dialog
    for resizing existing devices
  * `SizeArea` ([dialogs/size_chooser.py](blivetgui/dialogs/size_chooser.py)) -- a special
    widget for size selection used by both add and resize dialog.
  * `FormatDialog` ([dialogs/edit_dialog.py](blivetgui/dialogs/edit_dialog.py)) -- a dialog
    for changing format of existing devices

#### Multiprocess Communication

blivet-gui creates two processes -- `blivet-gui` for the UI and `blivet-gui-daemon`
for working with blivet.

Two processes are necessary because blivet needs root privileges to work with
storage but it isn't desirable to run GUI applications as root.

Both processes communicate using a socket file.

> For most cases, you don't need to worry about this. Only difference is that
> instead calling methods from `BlivetUtils`, you need to call them by using
> `BlivetGUIClient` (`BlivetGUI` class has and instance of it) `remote_call` method.
> So for example to get list of disks you'll need to use
> `self.client.remote_call("get_disks")`. It will return list of objects that
> you can use in the same way as [DiskDevice](http://rhinstaller.github.io/blivet/docs/blivet/blivet.devices.html#blivet.devices.disk.DiskDevice)
> objects from blivet.

##### Proxy

blivet-gui uses [pickle](https://docs.python.org/3/library/pickle.html) to send
objects between the processes. Unfortunately most blivet objects are not picklable.
To solve this, server and client parts of blivet-gui use "proxy objects" to
exchange unpicklable data. When `BlivetGUI` class "asks" for some "information"
that isn't picklable (e.g. using the `get_disks` method from `BlivetUtils` which
returns list of `StorageDevice` objects), `BlivetUtilsServer`
([communication/server.py](blivetgui/communication/server.py)) creates a new instance
of the `ProxyID` ([communication/proxy_utils.py](blivetgui/communication/proxy_utils.py))
object and sends it to the client instead. When client receives it, it creates an instance of
the `ClientProxyObject` ([communication/client.py](blivetgui/communication/client.py))
object and sends it to the `BlivetGUI` instead.

`ClientProxyObject` has a custom `__getattr__` method and has the ProxyID so it
can ask the server for values of attributes that `BlivetGUI` asks for.
Thanks to this, `BlivetGUI` can work with the blivet object without actually having it.

`ProxyDataContainer` ([communication/proxy_utils.py](blivetgui/communication/proxy_utils.py))
is a helper class used as a simple picklable container similar to namedtuple.

##### BlivetGUIClient

`BlivetGUIClient` ([communication/client.py](blivetgui/communication/client.py))
provides support for multiprocess communication for the client part of the blivet-gui.
`BlivetGUI` has an instance of the `BlivetGUIClient` and uses it to communicate
with the `BlivetUtils` via `BlivetUtilsServer`.

`BlivetGUI` can call `BlivetUtils` methods using `BlivetGUIClient.remote_call` method.

##### BlivetUtilsServer

`BlivetUtilsServer` ([communication/server.py](blivetgui/communication/server.py))
provides support for multiprocess communication for the server part of the blivet-gui.
It's a synchronous socketserver, it has an instance of `BlivetUtils` and processes
tasks from the `BlivetGUIClient`.
