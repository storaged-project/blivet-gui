Introduction to blivet-gui
==========================

Building Blocks
---------------

BlivetUtils
^^^^^^^^^^^

:class:`~.blivet_utils.BlivetUtils` class provides higher level API for Blivet library. It creates the
:class:`blivet.Blivet` object (:attr:`~.blivet_utils.BlivetUtils.storage`) and all blivet methods are called using this
class.

BlivetGUI
^^^^^^^^^

:class:`~.blivetgui.BlivetGUI` is the main class for the GUI. There are separate classes for every UI part. These
classes create all the necessary Gtk widgets (or loads them from Glade files) and provide signal handlers and other
helper functions.

Important GUI objects:
 - :class:`~.actions_menu.ActionsMenu` -- context (right click) menu for user actions
 - :class:`~.actions_toolbar.DeviceToolbar` -- toolbar with device-related actions (add, edit, remove...)
 - :class:`~.actions_toolbar.ActionsToolbar` -- toolbar with "global" actions (process or clear actions, main menu)
 - :class:`~.list_devices.ListDevices` -- list of "root" devices (disks, volume groups, RAIDs...)
 - :class:`~.visualization.logical_view.LogicalView` -- displays list of children of selected device (both as list using
   `Gtk.TreeView` and graphically using :class:`~.visualization.rectangle.Rectangle`)
 - :class:`~.visualization.physical_view.PhysicalView` -- displays list of parents of selected device

Dialogs
^^^^^^^

Most of the user interaction is done using dialogs. Some important dialogs include:
 - :class:`~.dialogs.add_dialog.AddDialog` -- dialog for adding new devices
 - :class:`~.dialogs.edit_dialog.ResizeDialog` -- dialog for resizing existing devices
 - :class:`~.message_dialogs.ErrorDialog`, :class:`~.message_dialogs.ExceptionDialog`,
   :class:`~.message_dialogs.ConfirmDialog` -- simple dialogs to display errors, exceptions and information
 - :class:`~.processing_window.ProcessingActions` -- dialog displaying progress during processing actions
 - :class:`~.loading_window.LoadingWindow` -- dialog displaying progress during blivet-gui start

Multiprocess Communication
^^^^^^^^^^^^^^^^^^^^^^^^^^

Blivet-gui creates two processes -- `blivet-gui` for the UI and `blivet-gui-daemon` for working with blivet.

Two processes are necessary because blivet needs root privileges to work with storage but GUI applications shouldn't be
running with root privileges.

Both processes communicate using a socket file.

Proxy
~~~~~

Blivet-gui uses `pickle` to send objects between the processes. Unfortunately most blivet objects are not picklable.
To solve this, server and client parts of blivet-gui communicate using "proxy objects".
When :class:`~.blivetgui.BlivetGUI` "asks" for some "information" that isn't picklable (e.g. using
:meth:`~.blivet_utils.BlivetUtils.get_disks` that returns list of :class:`blivet.devices.storage.StorageDevice`),
:class:`~.communication.server.BlivetUtilsServer` creates a new instance of :class:`~.communication.proxy_utils.ProxyID`
and sends it to the client instead. When client receives it, it creates an instance of
:class:`~.communication.client.ClientProxyObject` and sends it to the :class:`~.blivetgui.BlivetGUI` instead.

:class:`~.communication.client.ClientProxyObject` has a custom `__getattr__` method and has the ProxyID so it can ask
the server for values of attributes that :class:`~.blivetgui.BlivetGUI` asks for. Thanks to this,
:class:`~.blivetgui.BlivetGUI` can work with the blivet object without having it.

.. note::

  It isn't possible to call methods of proxied objects. Only attributes (and properties) are supported.

:class:`~.communication.proxy_utils.ProxyDataContainer` is a helper class used as a simple picklable container similar
to `namedtuple`.


BlivetGUIClient
~~~~~~~~~~~~~~~

:class:`~.communication.client.BlivetGUIClient` provides support for multiprocess communication for the client part of
the blivet-gui. :class:`~.blivetgui.BlivetGUI` has an instance of the :class:`~.communication.client.BlivetGUIClient`
and uses it to communicate with the :class:`~.blivet_utils.BlivetUtils` via :class:`~.communication.server.BlivetUtilsServer`.

:class:`~.blivetgui.BlivetGUI` can call :class:`~.blivet_utils.BlivetUtils` methods using
:meth:`~.communication.client.BlivetGUIClient.remote_call` method.


BlivetUtilsServer
~~~~~~~~~~~~~~~~~

:class:`~.communication.server.BlivetUtilsServer` provides support for multiprocess communication for the server part
of the blivet-gui. It's a synchronous `socketserver`, it has an instance of :class:`~.blivet_utils.BlivetUtils` and
processes tasks from the :class:`~.communication.client.BlivetGUIClient`.

.. note::

  Only one `blivet-gui-daemon` process can run at a time and it can communicate with only one `blivet-gui` process.
  "Binary" file `blivet-gui` should be used to start blivet-gui. It will automatically spawn the `blivet-gui-daemon`
  process with root privileges using `pkexec`.
