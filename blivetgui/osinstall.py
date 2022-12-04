# -*- coding: utf-8 -*-
# osinstall.py
# blivet-gui code for running in Anaconda installer
#
# Copyright (C) 2016  Red Hat, Inc.
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
# ---------------------------------------------------------------------------- #

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

from gi.repository import Gtk, Gdk

from .blivetgui import BlivetGUI
from .list_devices import ListDevices
from .list_partitions import ListPartitions
from .list_parents import ListParents
from .list_actions import ListActions
from .actions_menu import ActionsMenu
from .actions_toolbar import DeviceToolbar
from .visualization.logical_view import LogicalView
from .visualization.physical_view import PhysicalView
from .blivet_utils import BlivetUtils
from .dialogs import message_dialogs, constants
from .i18n import _
from .gui_utils import locate_ui_file, locate_css_file
from .logs import set_logging
from .config import config

from blivet.errors import StorageError
import sys
from contextlib import contextmanager


class BlivetUtilsAnaconda(BlivetUtils):

    installer_mode = True

    def __init__(self):
        # pylint: disable=super-init-not-called

        self._resizable_filesystems = None

        self._storage = None
        _log_file, self.log = set_logging(component="blivet-gui-utils")

    @property
    def storage(self):
        return self._storage

    @storage.setter
    def storage(self, storage):
        self._storage = storage


class BlivetGUIAnacondaClient(object):

    def __init__(self):
        self.utils = BlivetUtilsAnaconda()

    def initialize(self, storage):
        self.utils.storage = storage

    def remote_call(self, method, *args):

        utils_method = getattr(self.utils, method, None)
        if utils_method is None:
            raise RuntimeError("Unknown utils method %s" % method)

        return utils_method(*args)


class BlivetGUIAnaconda(BlivetGUI):

    installer_mode = True
    allow_ignore = True

    def __init__(self, client, spoke, spoke_container):
        # pylint: disable=super-init-not-called

        self.spoke = spoke
        self.client = client

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain("blivet-gui")
        self.builder.add_from_file(locate_ui_file("blivet-gui.ui"))

        # supported filesystems
        self._supported_filesystems = []

        # CSS styles
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path(locate_css_file("rectangle.css"))
        screen = Gdk.Screen.get_default()  # pylint: disable=no-value-for-parameter
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        # get the main vbox from blivet-gui and add it into given Gtk.Container
        win = self.builder.get_object("main_window")
        vbox = self.builder.get_object("vbox")
        win.remove(vbox)
        spoke_container.add(vbox)

        # ActionsMenu
        self.popup_menu = ActionsMenu(self)

        # ActionsToolbar
        self.device_toolbar = DeviceToolbar(self)

        # ListDevices
        self.list_devices = ListDevices(self)

        # ListPartitions
        self.list_partitions = ListPartitions(self)

        # ListParents
        self.list_parents = ListParents(self)

        # ListActions
        self.list_actions = ListActions(self)
        label_actions = self.builder.get_object("label_actions")
        label_actions.destroy()  # label with actions is part of the spoke

        # Visualization
        self.logical_view = LogicalView(self)
        self.builder.get_object("image_window").add(self.logical_view.hbox)

        self.physical_view = PhysicalView(self)
        self.builder.get_object("scrolledwindow_physical").add(self.physical_view.vbox)

    def initialize(self):
        super().initialize()

        # set some defaults from blivet now
        config.default_fstype = self.client.remote_call("get_default_filesystem")

    def ui_refresh(self, _spoke):
        """ This should be called only from Anaconda using the spoke 'entered'
            signal.

            In Anaconda blivetgui.initialize runs during 'refresh' when Gtk
            widgets are not visible ('realized') and this causes some UI
            elements to look weird because of wrong size allocation
            (unrealized widgets don't have size allocation so things like
            size of devices in visualization fail).
        """

        # just set cursor to first line in the device view -- this will select
        # the first disk and re-draw visualization
        self.list_devices.disks_view.set_cursor(0)

    def set_keyboard_shortcuts(self, _spoke):
        """ Configure blivet-gui keyboard shortcuts and add our accel group
            to the Anaconda main window. This configuration should be removed
            using "unset_keyboard_shortcuts" when exiting blivet-gui spoke
        """
        accel = self.builder.get_object("accelgroup")
        self.main_window.add_accel_group(accel)

        add = self.builder.get_object("button_add")
        add.add_accelerator("clicked", accel, Gdk.KEY_Insert, 0, Gtk.AccelFlags.VISIBLE)
        delete = self.builder.get_object("button_delete")
        delete.add_accelerator("clicked", accel, Gdk.KEY_Delete, 0, Gtk.AccelFlags.VISIBLE)

    def unset_keyboard_shortcuts(self, _spoke):
        """ Remove configuration added using "set_keyboard_shortcuts"
        """
        accel = self.builder.get_object("accelgroup")
        self.main_window.remove_accel_group(accel)

        add = self.builder.get_object("button_add")
        add.remove_accelerator(accel, Gdk.KEY_Insert, 0)
        delete = self.builder.get_object("button_delete")
        delete.remove_accelerator(accel, Gdk.KEY_Delete, 0)

    @property
    def label_actions(self):
        # Gtk.Label with number of currently scheduled actions is placed
        # in the spoke, not in blivet-gui window
        return self.spoke.label_actions

    def activate_action_buttons(self, activate):
        # 'action' buttons (reset and undo) are in the spoke
        self.spoke.activate_action_buttons(activate)

    @property
    def main_window(self):
        return self.spoke.main_window

    @contextmanager
    def enlightbox(self):
        self.main_window.lightbox_on()

        yield

        self.main_window.lightbox_off()

    def _reraise_exception(self, exception, traceback, message, dialog_window=None):
        allow_report = True
        allow_ignore = self.allow_ignore and issubclass(type(exception), StorageError)
        if allow_ignore:
            msg = _("{message}\n{error}\n Please click Report button to raise the error and let anaconda \n to handle the report process if you want to report this.").format(message=message, error=str(exception))
        else:
            msg = _("Unknown error occurred. Anaconda will be terminated.\n{error}").format(error=str(exception))

        with self.enlightbox():
            dialog = message_dialogs.ExceptionDialog(dialog_window if dialog_window else self.main_window,
                                                     allow_ignore, allow_report,
                                                     msg, str(traceback),
                                                     decorated=False)
            response = dialog.run()

        if response == constants.DialogResponseType.BACK:
            return
        else:
            if response == constants.DialogResponseType.REPORT:
                raise type(exception)(message + str(exception) + "\n" + traceback)
            if response == constants.DialogResponseType.QUIT:
                sys.exit(0)

    def show_error_dialog(self, error_message):
        with self.enlightbox():
            message_dialogs.ErrorDialog(self.main_window, error_message, decorated=False)

    def show_warning_dialog(self, warning_message):
        with self.enlightbox():
            message_dialogs.WarningDialog(self.main_window, warning_message, decorated=False)

    def show_confirmation_dialog(self, title, question):
        with self.enlightbox():
            dialog = message_dialogs.ConfirmDialog(self.main_window, title, question, decorated=False)
            response = dialog.run()

        return response

    def run_dialog(self, dialog):
        with self.enlightbox():
            if hasattr(dialog, "set_decorated"):  # FIXME
                dialog.set_decorated(False)
            response = dialog.run()

        return response

    def set_actions(self, blivet_actions):
        if not blivet_actions:
            return

        # clear all saved 'blivet-gui actions'
        self.list_actions.clear()

        # add a new 'placeholder' action for all currently registered blivet actions
        action_str = _("actions configured by installer")
        self.list_actions.append("misc", action_str, blivet_actions)

    def _handle_user_change(self):
        # user changed something blivet-gui -- blivet-gui spoke needs to clear
        # existing errors and run checks again to see if this change fixed that
        self.spoke._back_already_clicked = False

    def reload(self, _widget=None):
        """ Reload storage information
        """

        self.list_actions.clear()

        self.list_devices.update_devices_view()
        self.update_partitions_view()
