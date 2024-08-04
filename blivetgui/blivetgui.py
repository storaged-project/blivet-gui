# -*- coding: utf-8 -*-
# list_partitions.py
# Main blivet-gui class for GUI
#
# Copyright (C) 2014  Red Hat, Inc.
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
gi.require_version("GLib", "2.0")
gi.require_version("Gdk", "3.0")

from gi.repository import Gtk, GLib, Gdk

from blivet.size import Size
from blivet.errors import FSError
from blivet.formats import fs

from .list_devices import ListDevices
from .list_partitions import ListPartitions
from .list_parents import ListParents
from .list_actions import ListActions
from .main_menu import MainMenu
from .actions_menu import ActionsMenu
from .actions_toolbar import ActionsToolbar, DeviceToolbar
from .visualization.logical_view import LogicalView
from .visualization.physical_view import PhysicalView

from .i18n import _
from .gui_utils import locate_ui_file, locate_css_file
from .dialogs import message_dialogs, other_dialogs, edit_dialog, add_dialog, device_info_dialog
from .processing_window import ProcessingActions
from .loading_window import LoadingWindow
from .exception_handler import BlivetGUIExceptionHandler
from .communication.constants import ServerInitResponse
from .config import config

import threading
import sys
import atexit
import os

# ---------------------------------------------------------------------------- #


class BlivetGUI(object):
    """ Class representing the GUI part of the application. It creates all the
        Gtk.Widgets used in blivet-gui.
    """

    installer_mode = False

    def __init__(self, client, exclusive_disks=None, keep_above=False, auto_dev_updates=False):

        self.client = client

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain("blivet-gui")
        self.builder.add_from_file(locate_ui_file("blivet-gui.ui"))

        self.ignored_disks = []

        # blivet needs only names not paths, e.g. "sda" not "/dev/sda"
        if exclusive_disks:
            self.exclusive_disks = [os.path.basename(d) for d in exclusive_disks]
        else:
            self.exclusive_disks = []

        # allow creating ntfs filesystem
        # XXX: This shouldn't be necessary, NTFS is already "_formattable",
        # I don't have idea what "_supported" is for, the "supported" property
        # depends on this and "utils_available" so it is False when "ntfsprogs"
        # are not installed and that should be enough.
        fs.NTFS._supported = True

        # supported filesystems
        self._supported_filesystems = []

        self.flags = dict()
        if auto_dev_updates:
            self.flags["auto_dev_updates"] = True

        # CSS styles
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path(locate_css_file("rectangle.css"))
        screen = Gdk.Screen.get_default()  # pylint: disable=no-value-for-parameter
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        # MainWindow
        self.main_window = self.builder.get_object("main_window")
        self.main_window.connect("delete-event", self.quit)
        if keep_above:
            self.main_window.set_keep_above(True)

        # Exception handling
        self.exc = BlivetGUIExceptionHandler(self.main_window, sys.excepthook)
        self.exc.allow_ignore = False  # don't allow to ignore exceptions right now
        sys.excepthook = self.exc.handle_exception

        # BlivetUtils
        self.blivet_init()

        # Atexit
        atexit.register(self.client.quit)

        # MainMenu
        self.main_menu = MainMenu(self)

        # ActionsMenu
        self.popup_menu = ActionsMenu(self)

        # DeviceToolbar
        self.device_toolbar = DeviceToolbar(self)

        # ActionsToolbar
        self.actions_toolbar = ActionsToolbar(self)
        vbox_right = self.builder.get_object("vbox_right")
        vbox_right.pack_start(self.actions_toolbar.toolbar, expand=False, fill=True, padding=0)

        # ListDevices
        self.list_devices = ListDevices(self)

        # ListPartitions
        self.list_partitions = ListPartitions(self)

        # ListParents
        self.list_parents = ListParents(self)

        # ListActions
        self.label_actions = self.builder.get_object("label_actions")
        self.button_actions = self.builder.get_object("button_actions")
        self.button_actions.connect("clicked", self.show_actions)
        self.list_actions = ListActions(self)

        # Visualization
        self.logical_view = LogicalView(self)
        self.builder.get_object("image_window").add(self.logical_view.hbox)

        self.physical_view = PhysicalView(self)
        self.builder.get_object("scrolledwindow_physical").add(self.physical_view.vbox)

        # allow ignoring exceptions
        self.exc.allow_ignore = True

        # set some defaults from blivet now
        config.default_fstype = self.client.remote_call("get_default_filesystem")

        self.initialize()

    @property
    def supported_filesystems(self):
        if self._supported_filesystems:
            return self._supported_filesystems

        self._supported_filesystems = self.client.remote_call("get_supported_filesystems")
        return self._supported_filesystems

    def initialize(self):
        self.list_devices.load_devices()
        self.list_actions.initialize()

        # select first device in ListDevice
        self.list_devices.disks_view.set_cursor(1)
        self.main_window.show_all()
        self.list_devices.disks_view.set_cursor(0)

    def _set_physical_view_visible(self, visible):
        notebook = self.builder.get_object("notebook_views")
        physical_page = notebook.get_nth_page(1)

        if visible:
            physical_page.show()
        else:
            physical_page.hide()

    def update_partitions_view(self):
        self.list_partitions.update_partitions_list(self.list_devices.selected_device)
        self.logical_view.visualize_devices(self.list_partitions.partitions_list)

    def update_physical_view(self):
        self.list_parents.update_parents_list(self.list_devices.selected_device)
        self.physical_view.visualize_parents(self.list_parents.parents_list)

        if self.list_devices.selected_device.is_disk:
            self._set_physical_view_visible(False)
        else:
            self._set_physical_view_visible(True)

    def activate_action_buttons(self, activate):
        """ Set the actions toolbar buttons (in)active
        """

        if activate:
            self.actions_toolbar.activate_buttons(["clear", "apply", "undo"])
        else:
            self.actions_toolbar.deactivate_buttons(["clear", "apply", "undo"])

    def activate_device_actions(self, activate_list):
        """ Activate available device actions in device toolbar and popup menu

            :param activate_list: list of items to activate
            :type activate_list: list of str

        """

        for item in activate_list:
            self.device_toolbar.activate_buttons([item])
            self.popup_menu.activate_menu_items([item])

    def deactivate_device_actions(self, deactivate_list):
        """ Deactivate toolbar buttons and menu items

            :param deactivate_list: list of items to deactivate
            :type deactivate_list: list of str

        """

        for item in deactivate_list:
            self.device_toolbar.deactivate_buttons([item])
            self.popup_menu.deactivate_menu_items([item])

    def deactivate_all_actions(self):
        """ Deactivate all partition-based buttons/menu items
        """

        self.device_toolbar.deactivate_all()
        self.popup_menu.deactivate_all()

    def _reraise_exception(self, exception, traceback, message, dialog_window=None):
        raise type(exception)(message + "\n" + str(exception) + "\n" + traceback)

    def show_error_dialog(self, error_message):
        message_dialogs.ErrorDialog(self.main_window, error_message)

    def show_warning_dialog(self, warning_message):
        message_dialogs.WarningDialog(self.main_window, warning_message)

    def show_confirmation_dialog(self, title, question):
        dialog = message_dialogs.ConfirmDialog(self.main_window, title, question)
        response = dialog.run()

        return response

    def run_dialog(self, dialog):
        response = dialog.run()
        return response

    def _raise_exception(self, exception, traceback):
        raise exception.with_traceback(traceback)

    def switch_device_view(self, device):
        if not (device.is_disk or device.type in ("lvmvg", "btrfs volume", "mdarray")):
            raise ValueError

        self.list_devices.select_device_by_name(device.name)

    def _handle_user_change(self):
        # do this after user changed something -- currently only used
        # in installer mode
        pass

    def device_information(self, _widget=None):
        """ Display information about currently selected device
        """

        blivet_device = self.list_partitions.selected_partition[0]

        dialog = device_info_dialog.DeviceInformationDialog(self.main_window, blivet_device,
                                                            self.client, self.installer_mode)
        self.run_dialog(dialog)
        dialog.destroy()

    def resize_device(self, _widget=None):
        device = self.list_partitions.selected_partition[0]

        dialog = edit_dialog.ResizeDialog(self.main_window, device,
                                          self.client.remote_call("device_resizable", device))
        message = _("Failed to resize the device:")
        user_input = self.run_dialog(dialog)
        if user_input.resize:
            result = self.client.remote_call("resize_device", user_input)
            if not result.success:
                if not result.exception:
                    self.show_error_dialog(result.message)
                else:
                    self._reraise_exception(result.exception, result.traceback, message,
                                            dialog_window=dialog.dialog)
            else:
                if result.actions:
                    action_str = _("resize {name} {type}").format(name=device.name, type=device.type)
                    self.list_actions.append("edit", action_str, result.actions)

                self._handle_user_change()
                self.update_partitions_view()

    def format_device(self, _widget=None):
        device = self.list_partitions.selected_partition[0]

        if self.installer_mode:
            mountpoints = self.client.remote_call("get_mountpoints")
        else:
            mountpoints = []

        dialog = edit_dialog.FormatDialog(main_window=self.main_window,
                                          edit_device=device,
                                          supported_filesystems=self.supported_filesystems,
                                          mountpoints=mountpoints,
                                          installer_mode=self.installer_mode)
        message = _("Failed to format the device:")
        user_input = self.run_dialog(dialog)

        if user_input.format:
            result = self.client.remote_call("format_device", user_input)

            if not result.success:
                if not result.exception:
                    self.show_error_dialog(result.message)
                else:
                    self._reraise_exception(result.exception, result.traceback, message,
                                            dialog_window=dialog.dialog)
            else:
                if result.actions:
                    action_str = _("format {name} {type}").format(name=device.name, type=device.type)
                    self.list_actions.append("edit", action_str, result.actions)

                self._handle_user_change()
                self.update_partitions_view()

    def edit_lvmvg(self, _widget=None):
        """ Edit selected lvmvg
        """

        device = self.list_partitions.selected_partition[0]
        dialog = edit_dialog.LVMEditDialog(self.main_window, device,
                                           self.client.remote_call("get_free_info"))
        message = _("Failed to edit the LVM2 Volume Group:")
        response = self.run_dialog(dialog)

        if response == Gtk.ResponseType.OK:
            user_input = dialog.get_selection()
            result = self.client.remote_call("edit_lvmvg_device", user_input)

            if not result.success:
                if not result.exception:
                    self.show_error_dialog(result.message)
                else:
                    self._reraise_exception(result.exception, result.traceback, message,
                                            dialog_window=dialog)
            else:
                if result.actions:
                    action_str = _("edit {name} {type}").format(name=device.name, type=device.type)
                    self.list_actions.append("edit", action_str, result.actions)

            self._handle_user_change()
            self.update_partitions_view()

        dialog.destroy()
        return

    def set_partition_table(self, _widget=None):
        """ Create partition table on selected disk
        """

        device = self.list_partitions.selected_partition[0]
        self._add_disklabel(device.disk)

    def edit_label(self, _widget=None):
        device = self.list_partitions.selected_partition[0]
        dialog = edit_dialog.LabelDialog(self.main_window, device, installer_mode=self.installer_mode)

        user_input = dialog.run()

        if user_input.relabel:
            result = self.client.remote_call("relabel_format", user_input)

            if not result.success:
                if not result.exception:
                    self.show_error_dialog(result.message)
                else:
                    message = _("Failed to change filesystem label on the device:")
                    self._reraise_exception(result.exception, result.traceback, message,
                                            dialog_window=dialog)
            else:
                if result.actions:
                    action_str = _("change filesystem label of {name} {type}").format(name=device.name, type=device.type)
                    self.list_actions.append("edit", action_str, result.actions)
                self.update_partitions_view()

    def _allow_add_device(self, selected_device):
        """ Allow add device?
        """

        msg = None

        if selected_device.type == "free space":
            parent_device = selected_device.parents[0]
        else:
            parent_device = selected_device

        if parent_device.type == "lvmvg" and not parent_device.complete:
            msg = _("{name} is not complete. It is not possible to add new LVs to VG with "
                    "missing PVs.").format(name=parent_device.name)

        # not enough free space for at least two 2 MiB physical extents
        if parent_device.format.type == "lvmpv" and parent_device.size < Size("4 MiB"):
            msg = _("Not enough free space for a new LVM Volume Group.")

        if parent_device.is_disk and parent_device.format.type == "disklabel":
            disk = parent_device.format.parted_disk
            selected_device = self.list_partitions.selected_partition[0]
            if disk.primaryPartitionCount >= disk.maxPrimaryPartitionCount and selected_device.is_primary:
                msg = _("Disk {name} already reached maximum allowed number of primary partitions "
                        "for {label} disklabel.").format(name=parent_device.name, label=parent_device.format.label_type)

        return (False, msg) if msg else (True, None)

    def _add_disklabel(self, disk):
        """ Create a new disklabel on disk """

        dialog = other_dialogs.AddLabelDialog(self.main_window)
        selection = self.run_dialog(dialog)
        message = _("Failed to add disklabel:")

        if selection:
            result = self.client.remote_call("create_disk_label", disk, selection)
            if not result.success:
                if not result.exception:
                    self.show_error_dialog(result.message)
                else:
                    self._reraise_exception(result.exception, result.traceback, message,
                                            dialog_window=dialog.dialog)

            else:
                if result.actions:
                    action_str = _("create new disklabel on {name}").format(name=disk.name)
                    self.list_actions.append("add", action_str, result.actions)

            self._handle_user_change()
            self.update_partitions_view()

    def add_device(self, _widget=None):
        """ Show dialog for adding new device and create the device based on
            user selection """

        selected_device = self.list_partitions.selected_partition[0]

        # allow adding new device?
        allow, msg = self._allow_add_device(selected_device)

        if not allow:
            self.show_error_dialog(msg)
            return

        # uninitialized disk or mdarray -> add a disklabel
        if selected_device.type == "free space":
            if selected_device.is_uninitialized_disk:
                self._add_disklabel(disk=selected_device.disk)
                return
            elif selected_device.parents[0].type == "mdarray" and not selected_device.parents[0].format.type:
                self._add_disklabel(disk=selected_device.parents[0])
                return

        # adding a new device is allowed when selected both free space and some
        # "normal" devices -- we need both information: "future" parent and
        # selected free space (if available)
        if selected_device.type == "free space":
            selected_parent = selected_device.parents[0]
            selected_free = selected_device
        else:
            selected_parent = selected_device
            selected_free = self.client.remote_call("get_free_device", selected_device)

        if self.installer_mode:
            mountpoints = self.client.remote_call("get_mountpoints")
        else:
            mountpoints = []

        dialog = add_dialog.AddDialog(parent_window=self.main_window,
                                      selected_parent=selected_parent,
                                      selected_free=selected_free,
                                      available_free=self.client.remote_call("get_free_info"),
                                      supported_filesystems=self.supported_filesystems,
                                      mountpoints=mountpoints,
                                      installer_mode=self.installer_mode)

        response = self.run_dialog(dialog)
        message = _("Failed to add the device:")

        if response == Gtk.ResponseType.OK:
            user_input = dialog.get_selection()
            result = self.client.remote_call("add_device", user_input)

            if not result.success:
                if not result.exception:
                    self.show_error_dialog(result.message)
                else:
                    self._reraise_exception(result.exception, result.traceback, message,
                                            dialog_window=dialog)

            else:
                if result.actions:
                    action_str = _("add {size} {type} device").format(size=str(user_input.size_selection.total_size),
                                                                      type=user_input.device_type)

                    self.list_actions.append("add", action_str, result.actions)

            self._handle_user_change()
            self.list_devices.update_devices_view()
            self.update_partitions_view()

        dialog.destroy()

    def _deletable_parents(self, device):

        if device.type not in ("btrfs volume", "mdarray", "lvmvg"):
            return None

        deletable_parents = []
        for parent in device.parents:
            if not parent.is_disk:
                deletable_parents.append(parent)

        return deletable_parents

    def _device_descendants(self, device):
        descendants = []
        for child in device.children:
            descendants.append(child)
            descendants.extend(self._device_descendants(child))

        return descendants

    def delete_selected_partition(self, _widget=None):
        """ Delete selected partition

            :param widget: widget calling this function (only for calls via signal.connect)
            :type widget: Gtk.Widget()

        """

        deleted_device = self.list_partitions.selected_partition[0]
        dialog = message_dialogs.ConfirmDeleteDialog(parent_window=self.main_window,
                                                     device=deleted_device,
                                                     parents=self._deletable_parents(deleted_device),
                                                     children=self._device_descendants(deleted_device))
        message = _("Failed to delete the device:")
        response = self.run_dialog(dialog)

        if response.delete:
            result = self.client.remote_call("delete_device", deleted_device, response.delete_parents)

            if not result.success:
                if not result.exception:
                    self.show_error_dialog(result.message)

                else:
                    self._reraise_exception(result.exception, result.traceback, message,
                                            dialog_window=dialog.dialog)

            else:
                action_str = _("delete partition {name}").format(name=deleted_device.name)
                self.list_actions.append("delete", action_str, result.actions)

            self._handle_user_change()
            self.update_partitions_view()
            self.list_devices.update_devices_view()

    def set_mountpoint(self, _widget=None):
        device = self.list_partitions.selected_partition[0]

        if not device.format.mountable:
            raise RuntimeError("Format (%s) of selected device (%s) "
                               "is not mountable." % (device.format.type, device.name))

        if self.installer_mode:
            mountpoints = self.client.remote_call("get_mountpoints")
        else:
            mountpoints = []

        dialog = edit_dialog.MountpointDialog(main_window=self.main_window,
                                              edit_device=device,
                                              mountpoints=mountpoints,
                                              installer_mode=self.installer_mode)

        user_input = self.run_dialog(dialog)

        if user_input.do_set:
            msg = "Setting mountpoint for device '%s'" % device.name
            self.client.remote_call("log_debug", msg, user_input)
            device.format.mountpoint = user_input.mountpoint
            self._handle_user_change()
            self.update_partitions_view()

    def perform_actions(self, dialog):
        """ Perform queued actions
        """

        def end(success, error, traceback):
            if success:
                dialog.stop()
            else:
                message = _("Failed to perform the actions:")
                dialog.destroy()
                self.main_window.set_sensitive(False)
                self._reraise_exception(error, traceback, message, dialog_window=dialog)  # pylint: disable=raising-bad-type

        def show_progress(message):
            dialog.progress_msg(message)

        def do_it():
            """ Run blivet.doIt()
            """

            result = self.client.remote_do_it(show_progress)
            if result.success:
                GLib.idle_add(end, True, None, None)

            else:
                self.client.remote_call("blivet_reset")
                GLib.idle_add(end, False, result.exception, result.traceback)

            return

        # don't allow to ignore exceptions raised during do_it
        self.exc.allow_ignore = False

        thread = threading.Thread(target=do_it)
        thread.start()
        dialog.start()
        thread.join()

        self.list_actions.clear()

        self.list_devices.update_devices_view()
        self.update_partitions_view()

        # allow ignoring exceptions now
        self.exc.allow_ignore = True

    def apply_event(self, _widget=None):
        """ Apply event for main menu/toolbar
            :param widget: widget calling this function (only for calls via signal.connect)
            :type widget: Gtk.Widget()
        """

        title = _("Confirm scheduled actions")
        msg = _("Are you sure you want to perform scheduled actions?")
        actions = self.client.remote_call("get_actions")

        dialog = message_dialogs.ConfirmActionsDialog(self.main_window, title, msg, self.list_actions.actions_list)

        response = self.run_dialog(dialog)

        if response:
            processing_dialog = ProcessingActions(self, actions)
            self.perform_actions(processing_dialog)

    def umount_partition(self, _widget=None):
        """ Unmount selected partition

            :param widget: widget calling this function (only for calls via signal.connect)
            :type widget: Gtk.Widget()

        """

        device = self.list_partitions.selected_partition[0]

        if not device.format.mountable or not device.format.system_mountpoint:
            return ValueError("Selected device is not mounted")

        all_mountpoints = self.client.remote_call("get_system_mountpoints", device)
        if len(all_mountpoints) > 1:
            dialog = edit_dialog.UnmountDialog(self.main_window, device, mountpoints=all_mountpoints,
                                               installer_mode=self.installer_mode)
            user_input = dialog.run()

            if user_input.unmount:
                mountpoints = user_input.mountpoints
            else:
                return
        else:
            mountpoints = (device.format.system_mountpoint,)

        for mountpoint in mountpoints:
            try:
                device.format.unmount(mountpoint=mountpoint)
            except FSError:
                msg = _("Unmount of '{mountpoint}' failed. Are you sure the device is "
                        "not in use?".format(mountpoint=mountpoint))
                self.show_error_dialog(msg)

        self._handle_user_change()
        self.update_partitions_view()

    def decrypt_device(self, _widget=None):
        """ Unlock selected device

            :param widget: widget calling this function (only for calls via signal.connect)
            :type widget: Gtk.Widget()
        """

        dialog = other_dialogs.LuksPassphraseDialog(self.main_window)

        response = self.run_dialog(dialog)

        if response:
            ret = self.client.remote_call("luks_decrypt", self.list_partitions.selected_partition[0], response)

            if not ret:
                msg = _("Unlocking failed. Are you sure provided password is correct?")
                self.show_error_dialog(msg)
                return

        self._handle_user_change()
        self.list_devices.update_devices_view()
        self.update_partitions_view()

    def actions_undo(self, _widget=None):
        """ Undo last action

            :param widget: widget calling this function (only for calls via signal.connect)
            :type widget: Gtk.Widget()

        """

        removed_actions = self.list_actions.pop()
        self.client.remote_call("blivet_cancel_actions", removed_actions)

        self._handle_user_change()
        self.list_devices.update_devices_view()
        self.update_partitions_view()

    def clear_actions(self, _widget=None):
        """ Clear all scheduled actions

            :param widget: widget calling this function (only for calls via signal.connect)
            :type widget: Gtk.Widget()

        """

        self.client.remote_call("blivet_reset")

        self.list_actions.clear()

        self._handle_user_change()
        self.list_devices.update_devices_view()
        self.update_partitions_view()

    def show_actions(self, _widget=None, _uri=None):
        """ Show scheduled actions
        """

        dialog = message_dialogs.ShowActionsDialog(self.main_window, self.list_actions.actions_list)
        self.run_dialog(dialog)

        return True

    def _blivet_init_already_running(self):
        dialog = message_dialogs.CustomDialog(parent_window=self.main_window,
                                              buttons=[_("Quit"),
                                                       Gtk.ResponseType.ACCEPT])

        dialog.dialog.set_title(_("blivet-gui is already running"))
        dialog.dialog.set_markup(_("Another instance of blivet-gui is already running.\n"
                                   "Only one instance of blivet-gui can run at the same time."))
        msg = _("If your previous instance of blivet-gui crashed, please make sure that the <i>blivet-gui-daemon</i> "
                "process was terminated too.\nIf it is still running you can use\n\n"
                "<tt>$ sudo killall blivet-gui-daemon</tt>\n\n"
                "command to force quit it.")
        dialog.details.set_markup(msg)

        dialog.run()
        self.client.quit()
        sys.exit(1)

    def blivet_init(self):
        loading_window = LoadingWindow(self.main_window)
        ret = self._run_thread(loading_window, self.client.remote_control, ("init", self.ignored_disks, self.exclusive_disks, self.flags))

        if not ret.success:  # pylint: disable=maybe-no-member
            # blivet-gui is already running --> quit
            if ret.reason == ServerInitResponse.RUNNING:
                self._blivet_init_already_running()
            # unusable configuration (corrupted/unknown) disklabel --> ask
            elif ret.reason == ServerInitResponse.UNUSABLE:
                loading_window.destroy()

                cont = self._blivet_init_ignore(ret.exception, ret.disk)

                if cont:
                    self.ignored_disks.append(ret.disk)
                    self.blivet_init()
                else:
                    self.client.quit()
                    sys.exit(1)
            # unknown problem --> re-raise exception
            else:
                message = _("Failed to init blivet:")
                self._reraise_exception(ret.exception, ret.traceback, message,
                                        dialog_window=loading_window)

    def _blivet_init_ignore(self, exception, device_name):

        dialog = message_dialogs.CustomDialog(parent_window=self.main_window,
                                              buttons=[_("Quit blivet-gui"),
                                                       Gtk.ResponseType.REJECT,
                                                       _("Ignore disk and continue"),
                                                       Gtk.ResponseType.ACCEPT])

        dialog.dialog.set_title(_("Error: {error}").format(error=str(exception)))
        dialog.dialog.set_markup(_("Blivet-gui can't use the <b>{name}</b> disk due to a corrupted/unknown disklabel.\n"
                                   "You can either quit blivet-gui now or continue without being able to "
                                   "use this disk.").format(name=device_name))
        dialog.details.set_markup(exception.suggestion)

        response = dialog.run()

        return response == Gtk.ResponseType.ACCEPT

    def _run_thread(self, dialog, method, args):

        ret = []

        def end():
            dialog.stop()

        def do_it(ret):
            ret.append(method(*args))
            GLib.idle_add(end)

        thread = threading.Thread(target=do_it, args=(ret,))
        thread.start()
        dialog.start()
        thread.join()

        return ret[0]

    def reload(self, _widget=None):
        """ Reload storage information

            :param widget: widget calling this function (only for calls via signal.connect)
            :type widget: Gtk.Widget()

        """

        if self.list_actions.actions:
            title = _("Confirm reload storage")
            msg = _("There are pending operations. Are you sure you want to continue?")

            response = self.show_confirmation_dialog(title, msg)

            if not response:
                return

        # don't allow to ignore exceptions raised during reset
        self.exc.allow_ignore = False

        loading_window = LoadingWindow(self.main_window)
        self._run_thread(loading_window, self.client.remote_call, ("blivet_reset",))

        self.list_actions.clear()

        self._handle_user_change()
        self.list_devices.update_devices_view()
        self.update_partitions_view()

        # allow ignoring exceptions now
        self.exc.allow_ignore = True

    def quit(self, _event=None, _widget=None):
        """ Quit blivet-gui

            :param widget: widget calling this function (only for calls via signal.connect)
            :type widget: Gtk.Widget()

        """

        if self.list_actions.actions:
            title = _("Are you sure you want to quit?")
            msg = _("There are pending operations. Are you sure you want to quit blivet-gui now?")

            response = self.show_confirmation_dialog(title, msg)

            if not response:
                return True

        Gtk.main_quit()
