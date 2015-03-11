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
#------------------------------------------------------------------------------#

from gi.repository import Gtk, GObject

from .main_window import MainWindow
from .list_devices import ListDevices
from .list_partitions import ListPartitions
from .list_actions import ListActions
from .main_menu import MainMenu
from .actions_menu import ActionsMenu
from .actions_toolbar import ActionsToolbar
from .device_info import DeviceInfo
from .devicevisualization.device_canvas import DeviceCanvas
from .utils import BlivetUtils

from .logs import set_logging, set_python_meh, remove_logs
from .dialogs import message_dialogs, other_dialogs, edit_dialog, add_dialog
from .processing_window import ProcessingActions

import gettext

import threading
import os
import sys
import atexit

#------------------------------------------------------------------------------#

_ = lambda x: gettext.ldgettext("blivet-gui", x)

#------------------------------------------------------------------------------#

def locate_ui_file(filename):
    """ Locate neccessary Glade .ui files
    """

    path = [os.path.split(os.path.abspath(__file__))[0] + "/../data/ui/",
            "/usr/share/blivet-gui/ui/"]

    for folder in path:
        fname = folder + filename
        if os.access(fname, os.R_OK):
            return fname

    raise RuntimeError("Unable to find glade file %s" % file)

#------------------------------------------------------------------------------#

class BlivetGUI(object):

    def __init__(self, embedded_socket=None, kickstart_mode=False):

        self.embedded_socket = embedded_socket
        self.kickstart_mode = kickstart_mode

        self.builder = Gtk.Builder()
        self.builder.add_from_file(locate_ui_file("blivet-gui.ui"))

        ### Logging
        self.blivet_logfile, self.blivet_log = set_logging(component="blivet")
        self.program_logfile, self.program_log = set_logging(component="program")
        self.blivetgui_logfile, self.log = set_logging(component="blivet-gui")

        handler = set_python_meh(log_files=[self.blivet_logfile, self.program_logfile, self.blivetgui_logfile])
        handler.install(None)

        atexit.register(remove_logs, log_files=[self.blivet_logfile, self.program_logfile,
                                                self.blivetgui_logfile])

        ### BlivetUtils
        self.blivet_utils = BlivetUtils(kickstart_mode)

        ### MainWindow
        self.main_window = MainWindow(self).window

        ### Kickstart devices dialog
        if self.kickstart_mode:
            self.use_disks = self.kickstart_disk_selection()
            self.old_mountpoints = self.blivet_utils.kickstart_mountpoints()

        ### MainMenu
        self.main_menu = MainMenu(self)
        self.builder.get_object("vbox").add(self.main_menu.menu_bar)

        ### ActionsMenu
        self.popup_menu = ActionsMenu(self)

        ### ActionsToolbar
        self.toolbar = ActionsToolbar(self)
        self.builder.get_object("vbox").add(self.toolbar.toolbar)

        ### ListDevices
        self.list_devices = ListDevices(self)
        self.builder.get_object("disks_viewport").add(self.list_devices.disks_view)

        ### ListPartitions
        self.list_partitions = ListPartitions(self)
        self.builder.get_object("partitions_viewport").add(self.list_partitions.partitions_view)
        self.partitions_label = self.builder.get_object("partitions_page")
        self.partitions_label.set_text(_("Partitions"))

        ### ListActions
        self.list_actions = ListActions(self)
        self.builder.get_object("actions_viewport").add(self.list_actions.actions_view)
        self.actions_label = self.builder.get_object("actions_page")
        self.actions_label.set_text(_("Pending actions ({0})").format(self.list_actions.actions))

        ### DeviceInfo
        self.device_info = DeviceInfo(self)
        self.builder.get_object("pv_viewport").add(self.device_info.info_label)

        ### DeviceCanvas
        self.device_canvas = DeviceCanvas(self)
        self.builder.get_object("image_window").add(self.device_canvas)

        # select first device in ListDevice
        self.list_devices.disks_view.set_cursor(1)
        self.main_window.show_all()

    def update_partitions_view(self, device_changed=False):
        self.list_partitions.update_partitions_list(self.list_devices.selected_device)
        self.device_canvas.visualize_device(self.list_partitions.partitions_list,
                                            self.list_partitions.partitions_view,
                                            self.list_devices.selected_device)

        if device_changed:
            self.device_info.update_device_info(self.list_devices.selected_device)

    def activate_options(self, activate_list):
        """ Activate toolbar buttons and menu items

            :param activate_list: list of items to activate
            :type activate_list: list of str

        """

        for item in activate_list:
            self.toolbar.activate_buttons([item])
            self.main_menu.activate_menu_items([item])

            if item not in ("apply", "clear", "undo"):
                self.popup_menu.activate_menu_items([item])

    def deactivate_options(self, deactivate_list):
        """ Deactivate toolbar buttons and menu items

            :param deactivate_list: list of items to deactivate
            :type deactivate_list: list of str

        """

        for item in deactivate_list:
            self.toolbar.deactivate_buttons([item])
            self.main_menu.deactivate_menu_items([item])

            if item not in ("apply", "clear", "undo"):
                self.popup_menu.deactivate_menu_items([item])

    def deactivate_all_options(self):
        """ Deactivate all partition-based buttons/menu items
        """

        self.toolbar.deactivate_all()
        self.main_menu.deactivate_all()
        self.popup_menu.deactivate_all()

    def kickstart_disk_selection(self):
        disks = self.blivet_utils.get_disks()

        if len(disks) == 0:
            msg = _("blivet-gui failed to find at least one storage device to work with.\n\n" \
                    "Please connect a storage device to your computer and re-run blivet-gui.")

            self.show_error_dialog(msg)
            self.quit()

        dialog = other_dialogs.KickstartSelectDevicesDialog(self.main_window, disks)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            use_disks, install_bootloader, bootloader_device = dialog.get_selection()
            dialog.destroy()

        else:
            dialog.destroy()
            self.quit()

        if install_bootloader and bootloader_device:
            self.blivet_utils.set_bootloader_device(bootloader_device)

        self.blivet_utils.kickstart_hide_disks(use_disks)

        return use_disks

    def show_exception_dialog(self, exception_data, exception_traceback):
        message_dialogs.ExceptionDialog(self.main_window, exception_data, exception_traceback)

    def show_error_dialog(self, error_message):
        message_dialogs.ErrorDialog(self.main_window, error_message)

    def show_warning_dialog(self, warning_message):
        message_dialogs.WarningDialog(self.main_window, warning_message)

    def show_confirmation_dialog(self, title, question):
        dialog = message_dialogs.ConfirmDialog(self.main_window, title, question)
        response = dialog.run()

        return response

    def edit_device(self, widget=None):
        """ Edit selected device

            :param widget: widget calling this function (only for calls via signal.connect)
            :type widget: Gtk.Widget()

        """

        device = self.list_partitions.selected_partition[0]

        if device.type in ("partition", "lvmlv"):
            dialog = edit_dialog.PartitionEditDialog(self.main_window, device,
                                                     self.blivet_utils.device_resizable(device),
                                                     self.kickstart_mode)

        elif device.type in ("lvmvg",):
            dialog = edit_dialog.LVMEditDialog(self.main_window, device,
                                               self.blivet_utils.get_free_pvs_info(),
                                               self.blivet_utils.get_free_disks_regions(),
                                               self.blivet_utils.get_removable_pvs_info(device))

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            user_input = dialog.get_selection()

            if device.type in ("partition", "lvmlv"):
                result = self.blivet_utils.edit_partition_device(user_input)

            elif device.type in ("lvmvg",):
                result = self.blivet_utils.edit_lvmvg_device(user_input)

            if not result.success:
                if not result.exception:
                    self.show_error_dialog(result.message)

                else:
                    raise result.exception, None, result.traceback

            else:
                if result.actions:
                    action_str = _("edit {0} {1}").format(device.name, device.type)
                    self.list_actions.append("edit", action_str, result.actions)

            if result.actions:
                self.list_partitions.update_partitions_list(self.list_devices.selected_device)

        dialog.destroy()
        return

    def add_partition(self, widget=None, btrfs_pt=False):
        """ Add new partition
            :param widget: widget calling this function (only for calls via signal.connect)
            :type widget: Gtk.Widget()
            :param btrfs_pt: create btrfs as partition table
            :type btrfs_pt: bool
        """

        # parent device; free space has always only one parent #FIXME
        parent_device = self.list_partitions.selected_partition[0].parents[0]

        # btrfs volume has no special free space device -- parent device for newly
        # created subvolume is not parent of selected device but device (btrfs volume)
        # itself
        if self.list_partitions.selected_partition[0].type == "btrfs volume":
            parent_device = self.list_partitions.selected_partition[0]

        parent_device_type = parent_device.type

        if parent_device_type == "partition" and parent_device.format.type == "lvmpv":
            parent_device_type = "lvmpv"

        if parent_device_type == "disk" and not self.blivet_utils.has_disklabel(self.list_devices.selected_device) \
            and btrfs_pt == False:

            dialog = add_dialog.AddLabelDialog(self.main_window, self.list_devices.selected_device,
                                               self.blivet_utils.get_available_disklabels())

            response = dialog.run()

            if response == Gtk.ResponseType.OK:

                selection = dialog.get_selection()

                if selection == "btrfs":
                    dialog.destroy()
                    self.add_partition(btrfs_pt=True)
                    return

                result = self.blivet_utils.create_disk_label(self.list_devices.selected_device, selection)
                if not result.success:
                    if not result.exception:
                        self.show_error_dialog(result.message)

                    else:
                        raise result.exception, None, result.traceback

                else:
                    if result.actions:
                        action_str = _("create new disklabel on {0}").format(self.list_devices.selected_device.name)
                        self.list_actions.append("add", action_str, result.actions)

                self.update_partitions_view()

            dialog.destroy()
            return

        dialog = add_dialog.AddDialog(self.main_window,
                                      parent_device_type,
                                      parent_device,
                                      self.list_partitions.selected_partition[0],
                                      self.list_partitions.selected_partition[0].size,
                                      self.blivet_utils.get_free_pvs_info(),
                                      self.blivet_utils.get_free_disks_regions(),
                                      self.blivet_utils.get_available_raid_levels(),
                                      self.blivet_utils.has_extended_partition(self.list_devices.selected_device),
                                      self.blivet_utils.storage.mountpoints,
                                      self.kickstart_mode)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:

            user_input = dialog.get_selection()
            result = self.blivet_utils.add_device(user_input)

            if not result.success:
                if not result.exception:
                    self.show_error_dialog(result.message)

                else:
                    raise result.exception, None, result.traceback

            else:
                if result.actions:
                    if not user_input.filesystem:
                        action_str = _("add {0} {1} device").format(str(user_input.size),
                                                                    user_input.device_type)
                    else:
                        action_str = _("add {0} {1} partition").format(str(user_input.size),
                                                                       user_input.filesystem)

                    self.list_actions.append("add", action_str, result.actions)

            self.list_devices.update_devices_view()
            self.update_partitions_view()

        dialog.destroy()
        return

    def delete_selected_partition(self, widget=None):
        """ Delete selected partition

            :param widget: widget calling this function (only for calls via signal.connect)
            :type widget: Gtk.Widget()

        """

        deleted_device = self.list_partitions.selected_partition[0]

        title = _("Confirm delete operation")
        msg = _("Are you sure you want delete device {0}?").format(deleted_device.name)

        dialog = message_dialogs.ConfirmDialog(self.main_window, title, msg)
        response = dialog.run()

        if response:
            result = self.blivet_utils.delete_device(deleted_device)

            if not result.success:
                if not result.exception:
                    self.show_error_dialog(result.message)

                else:
                    raise result.exception, None, result.traceback

            else:
                action_str = _("delete partition {0}").format(deleted_device.name)
                self.list_actions.append("delete", action_str, result.actions)

        self.update_partitions_view()
        self.list_devices.update_devices_view()

    def perform_actions(self, dialog):
        """ Perform queued actions
        """

        def end(success, error, traceback):
            if success:
                dialog.stop()

            else:
                dialog.destroy()
                self.main_window.set_sensitive(False)
                raise error, None, traceback # pylint: disable=raising-bad-type

        def do_it():
            """ Run blivet.doIt()
            """

            try:
                self.blivet_utils.blivet_do_it()
                GObject.idle_add(end, True, None, None)

            except Exception as e: # pylint: disable=broad-except
                self.blivet_utils.blivet_reset()
                GObject.idle_add(end, False, e, sys.exc_info()[2])

            return

        thread = threading.Thread(target=do_it)
        thread.start()
        dialog.start()
        thread.join()

        self.list_actions.clear()

        self.list_devices.update_devices_view()
        self.update_partitions_view()

    def apply_event(self, widget=None):
        """ Apply event for main menu/toolbar

            :param widget: widget calling this function (only for calls via signal.connect)
            :type widget: Gtk.Widget()

        .. note::
                This is neccessary because of kickstart mode -- in "standard" mode
                we need only simple confirmation dialog, but in kickstart mode it
                is neccessary to create file choosing dialog for kickstart file save.

        """

        if self.kickstart_mode:

            dialog = other_dialogs.KickstartFileSaveDialog(self.main_window)

            response = dialog.run()

            if response:
                if os.path.isfile(response):
                    title = _("File exists")
                    msg = _("Selected file already exists, do you want to overwrite it?")
                    dialog_file = message_dialogs.ConfirmDialog(self.main_window, title, msg)
                    response_file = dialog_file.run()

                    if not response_file:
                        return

                self.blivet_utils.create_kickstart_file(response)

                msg = _("File with your Kickstart configuration was successfully saved to:\n\n" \
                    "{0}").format(response)
                message_dialogs.InfoDialog(self.main_window, msg)

        else:
            title = _("Confirm scheduled actions")
            msg = _("Are you sure you want to perform scheduled actions?")
            actions = self.blivet_utils.get_actions()

            dialog = message_dialogs.ConfirmActionsDialog(self.main_window, title, msg, actions)

            response = dialog.run()

            if response:
                processing_dialog = ProcessingActions(self)
                self.perform_actions(processing_dialog)

    def umount_partition(self, widget=None):
        """ Unmount selected partition

            :param widget: widget calling this function (only for calls via signal.connect)
            :type widget: Gtk.Widget()

        """

        result = self.blivet_utils.unmount_device(self.list_partitions.selected_partition[0])

        if not result:
            msg = _("Unmount failed. Are you sure device is not in use?")
            self.show_error_dialog(msg)

        self.update_partitions_view()

    def decrypt_device(self, widget=None):
        """ Decrypt selected device

            :param widget: widget calling this function (only for calls via signal.connect)
            :type widget: Gtk.Widget()
        """

        dialog = other_dialogs.LuksPassphraseDialog(self.main_window)

        response = dialog.run()

        if response:
            ret = self.blivet_utils.luks_decrypt(self.list_partitions.selected_partition[0], response)

            if ret:
                msg = _("Unknown error appeared:\n\n{0}.").format(ret)
                message_dialogs.ErrorDialog(self.main_window, msg)

                return

        self.list_devices.update_devices_view()
        self.update_partitions_view()

    def actions_undo(self, widget=None):
        """ Undo last action

            :param widget: widget calling this function (only for calls via signal.connect)
            :type widget: Gtk.Widget()

        """

        removed_actions = self.list_actions.pop()
        self.blivet_utils.blivet_cancel_actions(removed_actions)

        self.list_devices.update_devices_view()
        self.update_partitions_view()

    def clear_actions(self, widget=None):
        """ Clear all scheduled actions

            :param widget: widget calling this function (only for calls via signal.connect)
            :type widget: Gtk.Widget()

        """

        self.blivet_utils.blivet_reset()

        self.list_actions.clear()

        self.list_devices.update_devices_view()
        self.update_partitions_view()

    def reload(self):
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

        self.blivet_utils.blivet_reset()

        if self.kickstart_mode:
            self.blivet_utils.kickstart_hide_disks(self.use_disks)

        self.list_actions.clear()

        self.list_devices.update_devices_view()
        self.update_partitions_view()

    def quit(self, event=None, widget=None):
        """ Quit blivet-gui

            :param widget: widget calling this function (only for calls via signal.connect)
            :type widget: Gtk.Widget()

        """

        if self.list_actions.actions:
            title = _("Are you sure you want to quit?")
            msg = _("There are unapplied actions. Are you sure you want to quit blivet-gui now?")

            response = self.show_confirmation_dialog(title, msg)

            if not response:
                return True

        Gtk.main_quit()
