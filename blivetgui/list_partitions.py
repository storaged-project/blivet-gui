# -*- coding: utf-8 -*-
# list_partitions.py
# Load and display partitions for selected device
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

from gi.repository import Gtk, GdkPixbuf

import gettext

from utils import *

from dialogs import *

from actions_toolbar import *

from actions_menu import *

from main_menu import *

from processing_window import *

from devicevisualization.device_canvas import device_canvas

#------------------------------------------------------------------------------#

_ = lambda x: gettext.ldgettext("blivet-gui", x)

#------------------------------------------------------------------------------#

class ListPartitions():

    def __init__(self, main_window, list_devices, blivet_utils, builder,
        kickstart_mode=False, disk=None):

        self.list_devices = list_devices
        self.b = blivet_utils
        self.builder = builder

        self.kickstart_mode = kickstart_mode

        self.disk = disk
        self.main_window = main_window

        # ListStores for partitions and actions
        self.partitions_list = Gtk.TreeStore(object, str, str, str, str, str,
            str, object)

        self.actions_list = Gtk.TreeStore(GdkPixbuf.Pixbuf, str)

        self.partitions_view = self.create_partitions_view()
        self.builder.get_object("partitions_viewport").add(self.partitions_view)

        self.actions_view = self.create_actions_view()
        self.builder.get_object("actions_viewport").add(self.actions_view)

        self.info_label = Gtk.Label()
        self.builder.get_object("pv_viewport").add(self.info_label)

        self.darea = device_canvas(blivet_utils=self.b, list_partitions=self)
        self.builder.get_object("image_window").add(self.darea)

        self.main_menu = MainMenu(self.main_window, self, self.list_devices)
        self.builder.get_object("vbox").add(self.main_menu.get_main_menu)

        self.popup_menu = ActionsMenu(self)
        self.toolbar = actions_toolbar(self, self.main_window)
        self.builder.get_object("vbox").add(self.toolbar.get_toolbar)

        self.select = self.partitions_view.get_selection()
        self.path = self.select.select_path("1")

        self.on_partition_selection_changed(self.select)
        self.selection_signal = self.select.connect("changed",
            self.on_partition_selection_changed)

        self.actions = 0
        self.actions_label = self.builder.get_object("actions_page")
        self.actions_label.set_text(_("Pending actions ({0})").format(self.actions))

        self.partitions_label = self.builder.get_object("partitions_page")
        self.partitions_label.set_text(_("Partitions").format(self.actions))

        self.main_window.connect("delete-event", self.quit)

        self.selected_partition = None

        self.history = []

    def device_info(self):
        """ Basic information for selected device
        """

        device_type = self.b.get_device_type(self.disk)

        if device_type == "lvmvg":
            pvs = self.b.get_parent_pvs(self.disk)

            info_str = _("<b>LVM2 Volume group <i>{0}</i> occupying {1} " \
                "physical volume(s):</b>\n\n").format(self.disk.name, len(pvs))

            for pv in pvs:
                info_str += _("\t• PV <i>{0}</i>, size: {1} on <i>{2}</i> " \
                    "disk.\n").format(pv.name, str(pv.size), pv.disks[0].name)

        elif device_type in ["lvmpv", "luks/dm-crypt"]:
            blivet_device = self.disk

            if blivet_device.format.type == "lvmpv":
                info_str = _("<b>LVM2 Physical Volume</b>").format()

            else:
                info_str = ""

        elif device_type == "disk":

            blivet_disk = self.disk

            info_str = _("<b>Hard disk</b> <i>{0}</i>\n\n\t• Size: <i>{1}</i>" \
                "\n\t• Model: <i>{2}</i>\n").format(blivet_disk.path,
                str(blivet_disk.size), blivet_disk.model)

        else:
            info_str = ""

        self.info_label.set_markup(info_str)

        return

    def update_partitions_view(self, selected_device):
        """ Update partition view with selected disc children (partitions)

            :param selected_device: selected device from list (eg. disk or VG)
            :type device_name: blivet.Device

        """

        self.disk = selected_device

        if self.disk:
            self.device_info()

        def childs_loop(childs, parent):

            extended_iter = None
            unadded_logical = []

            for child in childs:

                if hasattr(child, "isExtended") and child.isExtended:
                    extended_iter = self.add_partition_to_view(child, parent)

                elif hasattr(child, "isLogical") and child.isLogical:

                    if not extended_iter:
                        unadded_logical.append(child)

                    else:
                        self.add_partition_to_view(child, extended_iter)

                elif child.type != "free space" and len(self.b.get_partitions(child)) != 0:

                    parent_iter = self.add_partition_to_view(child, parent)

                    childs_loop(self.b.get_partitions(child), parent_iter)

                else:
                    self.add_partition_to_view(child, parent)

            if len(unadded_logical) != 0 and extended_iter:
                # if blivet creates extended partition it is sometimes huges mess
                # and we need to be sure they are added in proper way
                for logical in unadded_logical:
                    self.add_partition_to_view(logical, extended_iter)

        self.partitions_list.clear()

        partitions = self.b.get_partitions(self.disk)

        childs_loop(partitions, None)

        # select first line in partitions view
        self.select = self.partitions_view.get_selection()
        self.path = self.select.select_path("0")

        # expand all expanders
        self.partitions_view.expand_all()

        # update partitions image

        self.darea.visualize_device(self.partitions_list, self.partitions_view,
            self.disk)

    def add_partition_to_view(self, partition, parent):
        """ Add partition into partition_list

        """
        resize_size = "--"

        if partition.type == "free space":
            iter_added = self.partitions_list.append(parent, [partition,
                partition.name, "--", "--", str(partition.size), "--", None,
                None])
        elif partition.type == "partition" and hasattr(partition, "isExtended") and partition.isExtended:
            iter_added = self.partitions_list.append(None, [partition,
                partition.name, _("extended"), "--", str(partition.size), "--",
                None, None])
        elif partition.type == "lvmvg":
            iter_added = self.partitions_list.append(parent, [partition,
                partition.name, _("lvmvg"), "--", str(partition.size), "--",
                None, None])

        elif partition.format.mountable:

            if partition.format.resizable:
                partition.format.updateSizeInfo()
                resize_size = partition.format.minSize

            if partition.format.mountpoint != None:
                iter_added = self.partitions_list.append(parent, [partition,
                    partition.name, partition.format.type,
                    partition.format.mountpoint, str(partition.size),
                    str(resize_size), None, None])

            elif partition.format.mountpoint == None and self.kickstart_mode:

                if partition.format.uuid in self.list_devices.old_mountpoints.keys():
                    old_mnt = self.list_devices.old_mountpoints[partition.format.uuid]
                else:
                    old_mnt = None

                iter_added = self.partitions_list.append(parent, [partition,
                    partition.name, partition.format.type, partition.format.mountpoint,
                    str(partition.size), str(resize_size), old_mnt, None])

            else:
                iter_added = self.partitions_list.append(parent, [partition,
                    partition.name, partition.format.type, partition_mounted(partition.path),
                    str(partition.size), str(resize_size), None, None])
        else:
            iter_added = self.partitions_list.append(parent, [partition,
                partition.name, partition.format.type, "--",
                str(partition.size), str(resize_size), None, None])

        return iter_added

    def create_partitions_view(self):
        """ Create Gtk.TreeView for device children (partitions)
        """

        partitions = self.partitions_list

        treeview = Gtk.TreeView(model=partitions)
        treeview.set_vexpand(True)

        renderer_text = Gtk.CellRendererText()

        column_text1 = Gtk.TreeViewColumn(_("Partition"), renderer_text, text=1)
        column_text2 = Gtk.TreeViewColumn(_("Filesystem"), renderer_text, text=2)
        column_text3 = Gtk.TreeViewColumn(_("Mountpoint"), renderer_text, text=3)
        column_text4 = Gtk.TreeViewColumn(_("Size"), renderer_text, text=4)
        column_text5 = Gtk.TreeViewColumn(_("Used"), renderer_text, text=5)
        column_text6 = Gtk.TreeViewColumn(_("Current Mountpoint"), renderer_text, text=6)

        treeview.append_column(column_text1)
        treeview.append_column(column_text2)
        treeview.append_column(column_text3)
        treeview.append_column(column_text4)
        treeview.append_column(column_text5)

        if self.kickstart_mode:
            treeview.append_column(column_text6)

        treeview.set_headers_visible(True)

        treeview.connect("button-release-event", self.on_right_click_event)

        return treeview

    def on_right_click_event(self, treeview, event):
        """ Right click event on partition treeview
        """

        if event.button == 3:

            selection = treeview.get_selection()

            if selection == None:
                return False

            self.popup_menu.get_menu.popup(None, None, None, None, event.button,
                event.time)

            return True

    def create_actions_view(self):
        """ Create treeview for actions

            :returns: treeview
            :rtype: Gtk.TreeView

        """

        treeview = Gtk.TreeView(model=self.actions_list)
        treeview.set_vexpand(True)
        treeview.set_hexpand(True)

        renderer_pixbuf = Gtk.CellRendererPixbuf()
        column_pixbuf = Gtk.TreeViewColumn(None, renderer_pixbuf, pixbuf=0)
        treeview.append_column(column_pixbuf)

        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn(None, renderer_text, text=1)
        treeview.append_column(column_text)

        treeview.set_headers_visible(False)

        return treeview

    def clear_actions_view(self):
        """ Delete all actions in actions view
        """

        self.actions = 0
        self.actions_label.set_text(_("Pending actions ({0})").format(self.actions))
        self.actions_list.clear()

        self.deactivate_options(["apply", "clear"])

        self.update_partitions_view(self.disk)

    def update_actions_view(self, action_type=None, action_desc=None, blivet_actions=None):
        """ Update list of scheduled actions

            :param action_type: type of action (delete/add/edit)
            :type action_type: str
            :param action_desc: description of scheduled action
            :type partition_name: str

        """

        icon_theme = Gtk.IconTheme.get_default()
        icon_add = Gtk.IconTheme.load_icon(icon_theme, "list-add", 16, 0)
        icon_delete = Gtk.IconTheme.load_icon(icon_theme, "edit-delete", 16, 0)
        icon_edit = Gtk.IconTheme.load_icon(icon_theme, "edit-select-all", 16, 0)

        action_icons = {"add" : icon_add, "delete" : icon_delete, "edit" : icon_edit}


        parent_iter = self.actions_list.append(None, [action_icons[action_type], action_desc])

        for action in blivet_actions:
            self.actions_list.append(parent_iter, [None, str(action)])

        self.actions_view.expand_all()
        self.actions_label.set_text(_("Pending actions ({0})").format(self.actions))

        self.activate_options(["apply", "clear"])

    def activate_options(self, activate_list):
        """ Activate toolbar buttons and menu items

            :param activate_list: list of items to activate
            :type activate_list: list of str

        """

        for item in activate_list:
            self.toolbar.activate_buttons([item])
            self.main_menu.activate_menu_items([item])

            if item not in ["apply", "clear", "undo"]:
                self.popup_menu.activate_menu_items([item])

    def deactivate_options(self, deactivate_list):
        """ Deactivate toolbar buttons and menu items

            :param deactivate_list: list of items to deactivate
            :type deactivate_list: list of str

        """

        for item in deactivate_list:
            self.toolbar.deactivate_buttons([item])
            self.main_menu.deactivate_menu_items([item])

            if item not in ["apply", "clear", "undo"]:
                self.popup_menu.deactivate_menu_items([item])

    def deactivate_all_options(self):
        """ Deactivate all partition-based buttons/menu items
        """

        self.toolbar.deactivate_all()
        self.main_menu.deactivate_all()
        self.popup_menu.deactivate_all()

    def _allow_delete_device(self, device):
        """ Is this device deletable?

            :param device: selected device
            :type device: blivet.Device
            :returns: device possible to delete
            :rtype: bool

        """

        if device.type == "free space" or not device.isleaf:
            return False

        else:
            if self.kickstart_mode or not device.format.type:
                return True

            elif device.format.type == "swap" and swap_is_on(device.sysfsPath):
                return False

            else:
                if not device.format.mountable:
                    return True

                else:
                    # partition_mounted returns true for mounted partitions
                    # we need to return false, because mounted partitions
                    # cannot be deleted
                    return not partition_mounted(device.path)

    def _allow_edit_device(self, device):
        """ Is this device editable?

            :param device: selected device
            :type device: blivet.Device
            :returns: device possible to edit
            :rtype: bool

        """

        if device.type == "free space":
            return False

        elif self.kickstart_mode:
            return device.format.mountable

        else:
            if device.type in ["lvmvg"]:
                return True

            elif not device.format.mountable:
                return False

            else:
                return not partition_mounted(device.path)


    def activate_action_buttons(self, selected_device):
        """ Activate buttons in toolbar based on selected device

            :param selected_device: Selected partition
            :type selected_device: Gtk.TreeModelRow

        """

        device = selected_device[0]

        self.deactivate_all_options()

        if self._allow_delete_device(device):
            self.activate_options(["delete"])

        if self._allow_edit_device(device):
            self.activate_options(["edit"])

        if device.type in ["free space", "btrfs volume"]:
            self.activate_options(["add"])

        if device.format:
            if device.format.type == "luks" and not device.format.status \
                and device.format.exists:
                self.activate_options(["decrypt"])

            elif device.format.mountable and partition_mounted(device.path):
                self.activate_options(["unmount"])

    def delete_selected_partition(self):
        """ Delete selected partition
        """

        deleted_device = self.selected_partition[0]

        title = _("Confirm delete operation")
        msg = _("Are you sure you want to delete device {0}?").format(self.selected_partition[0].name)

        dialog = message_dialogs.ConfirmDialog(self.main_window, title, msg)
        response = dialog.run()

        if response :
            actions = self.b.delete_device(self.selected_partition[0])

            if actions:
                action_str = _("delete partition {0}").format(deleted_device.name)
                self.add_undo_actions(actions)
                self.main_menu.activate_menu_items(["undo"])
                self.update_actions_view("delete", action_str, actions)
                self.selected_partition = None

        self.update_partitions_view(self.disk)
        self.list_devices.update_devices_view()

    def add_partition(self, btrfs_pt=False):
        """ Add new partition

            :param btrfs_pt: create btrfs as partition table
            :type btrfs_pt: bool

        """

        # parent device; free space has always only one parent #FIXME
        parent_device = self.selected_partition[0].parents[0]

        # btrfs volume has no special free space device -- parent device for newly
        # created subvolume is not parent of selected device but device (btrfs volume)
        # itself
        if self.selected_partition[0].type == "btrfs volume":
            parent_device = self.selected_partition[0]

        parent_device_type = parent_device.type

        if parent_device_type == "partition" and parent_device.format.type == "lvmpv":
            parent_device_type = "lvmpv"

        if parent_device_type == "disk" and self.b.has_disklabel(self.disk) != True \
            and btrfs_pt == False:

            dialog = add_dialog.AddLabelDialog(self.main_window, self.disk,
                self.b.get_available_disklabels())

            response = dialog.run()

            if response == Gtk.ResponseType.OK:

                selection = dialog.get_selection()

                if selection == "btrfs":
                    dialog.destroy()
                    self.add_partition(btrfs_pt=True)
                    return

                actions = self.b.create_disk_label(self.disk, selection)
                if actions:
                    action_str = _("create new disklabel on {0}").format(self.disk.name)
                    self.add_undo_actions(actions)
                    self.main_menu.activate_menu_items(["undo"])
                    self.update_actions_view("add", action_str, actions)

                self.update_partitions_view(self.disk)

            dialog.destroy()
            return

        dialog = add_dialog.AddDialog(self.main_window, parent_device_type,
            parent_device, self.selected_partition[0],
            self.selected_partition[0].size, self.b.get_free_pvs_info(),
            self.b.get_free_disks_regions(), self.b.get_available_raid_levels(),
            self.b.has_extended_partition(self.disk), self.kickstart_mode)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:

            user_input = dialog.get_selection()
            actions = self.b.add_device(user_input)

            if actions:
                if user_input.filesystem == None:
                    action_str = _("add {0} {1} device").format(str(user_input.size), user_input.device_type)
                else:
                    action_str = _("add {0} {1} partition").format(str(user_input.size), user_input.filesystem)

                self.add_undo_actions(actions)
                self.main_menu.activate_menu_items(["undo"])
                self.update_actions_view("add", action_str, actions)

            self.list_devices.update_devices_view()
            self.update_partitions_view(self.disk)

        dialog.destroy()
        return

    def check_mountpoint(self, mountpoint):
        """ Kickstart mode; check for duplicate mountpoints

            :param mountpoint: mountpoint selected by user
            :type mountpoint: str
            :returns: mountpoint validity
            :rtype: bool
        """

        if mountpoint == None:
            return True

        elif mountpoint not in self.b.storage.mountpoints.keys():
            return True

        else:

            old_device = self.b.storage.mountpoints[mountpoint]

            title = _("Duplicate mountpoint detected")
            msg = _("Selected mountpoint \"{0}\" is already used for \"{1}\" " \
                "device. Do you want to remove this mountpoint?").format(mountpoint,
                old_device.name)

            dialog = message_dialogs.ConfirmDialog(self.main_window, title, msg)

            response = dialog.run()

            if response:
                old_device.format.mountpoint = None

            return response

    def perform_actions(self):
        """ Perform queued actions

        .. note::
                New window creates separate thread to run blivet.doIt()

        """

        ProcessingActions(self, self.main_window)

        self.clear_actions_view()
        self.clear_undo_actions()

        self.update_partitions_view(self.disk)

    def apply_event(self):
        """ Apply event for main menu/toolbar

        .. note::
                This is neccessary because of kickstart mode -- in "standard" mode
                we need only simple confirmation dialog, but in kickstart mode it
                is neccessary to create file choosing dialog for kickstart file save.

        """
        if self.kickstart_mode:

            dialog = other_dialogs.KickstartFileSaveDialog(self.main_window)

            response = dialog.run()

            if response:
                self.clear_actions_view()
                self.b.create_kickstart_file(response)

            self.clear_actions_view()
            self.clear_undo_actions()

        else:

            title = _("Confirm scheduled actions")
            msg = _("Are you sure you want to perform scheduled actions?")
            actions = self.b.get_actions()

            dialog = message_dialogs.ConfirmActionsDialog(self.main_window, title,
                msg, actions)

            response = dialog.run()

            if response:
                self.perform_actions()

    def umount_partition(self):
        """ Unmount selected partition
        """

        mountpoint = self.selected_partition[3]

        if os_umount_partition(mountpoint):
            self.update_partitions_view(self.disk)

        else:

            msg = _("Unmount failed. Are you sure {0} is not in use?").format(self.selected_partition[0].name)
            message_dialogs.ErrorDialog(self.main_window, msg)

    def decrypt_device(self):
        """ Decrypt selected device
        """

        dialog = other_dialogs.LuksPassphraseDialog(self.main_window,
            self.selected_partition[0].name)

        response = dialog.run()

        if response:
            ret = self.b.luks_decrypt(self.selected_partition[0],
                response)

            if ret:
                msg = _("Unknown error appeared:\n\n{0}.").format(ret)
                message_dialogs.ErrorDialog(self.main_window, msg)

                return

        self.list_devices.update_devices_view()
        self.update_partitions_view(self.disk)

    def edit_device(self):
        """ Edit selected device
        """

        device = self.selected_partition[0]

        if device.type in ["partition", "lvmlv"]:
            dialog = edit_dialog.PartitionEditDialog(self.main_window, device,
                self.b.device_resizable(device), self.kickstart_mode)

        elif device.type in ["lvmvg"]:
            dialog = edit_dialog.LVMEditDialog(self.main_window, device,
                self.b.get_free_pvs_info(), self.b.get_free_disks_regions(),
                self.b.get_removable_pvs_info(device))

        dialog.connect("delete-event", Gtk.main_quit)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:

            user_input = dialog.get_selection()

            if device.type in ["partition", "lvmlv"]:
                actions = self.b.edit_partition_device(user_input)

            elif device.type in ["lvmvg"]:
                actions = self.b.edit_lvmvg_device(user_input)

            if actions:
                action_str = _("edit {0} {1}").format(device.name, device.type)
                self.add_undo_actions(actions)
                self.main_menu.activate_menu_items(["undo"])
                self.update_actions_view("edit", action_str, actions)

            self.update_partitions_view(self.disk)

        dialog.destroy()
        return

    def clear_actions(self):
        """ Clear all scheduled actions
        """

        self.b.blivet_reset()

        self.clear_undo_actions()
        self.clear_actions_view()

        self.list_devices.update_devices_view()
        self.update_partitions_view(self.disk)

    def add_undo_actions(self, actions):
        """ Add actions to list of actions to undo
        """

        self.history.append(actions)

        self.actions += 1
        self.actions_label.set_text(_("Pending actions ({0})").format(self.actions))

        self.activate_options(["undo"])

    def clear_undo_actions(self):
        """ Clear list of undo actions
        """

        self.history = []
        self.actions = 0
        self.actions_label.set_text(_("Pending actions ({0})").format(self.actions))

        self.deactivate_options(["undo"])

    def actions_undo(self):
        """ Undo last action
        """

        self.b.blivet_cancel_actions(self.history.pop())
        self.actions_list.remove(self.actions_list.get_iter(len(self.actions_list)-1))

        self.list_devices.update_devices_view()
        self.update_partitions_view(self.disk)

        self.actions -= 1
        self.actions_label.set_text(_("Pending actions ({0})").format(self.actions))

        if self.actions == 0:
            self.deactivate_options(["clear", "apply", "undo"])

    def on_partition_selection_changed(self, selection):
        """ On selected partition action
        """

        model, treeiter = selection.get_selected()

        self.deactivate_all_options()

        if treeiter != None:
            self.activate_action_buttons(model[treeiter])
            self.selected_partition = model[treeiter]
            self.darea.update_visualisation()

    def reload(self):
        """ Quit blivet-gui
        """

        if self.actions != 0:
            # There are queued actions we don't want do quit now

            title = _("Confirm reload storage")
            msg = _("There are pending operations. Are you sure you want to " \
            "continue?")

            dialog = message_dialogs.ConfirmDialog(self.main_window, title, msg)
            response = dialog.run()

            if response:
                self.b.blivet_reload()
                self.clear_undo_actions()
                self.clear_actions_view()

                self.list_devices.update_devices_view()
                self.update_partitions_view(self.disk)

        else:
            self.b.blivet_reload()
            self.clear_undo_actions()
            self.clear_actions_view()

            self.list_devices.update_devices_view()
            self.update_partitions_view(self.disk)

    def quit(self, event=None, widget=None):
        """ Quit blivet-gui
        """

        if self.actions != 0:
            # There are queued actions we don't want do quit now

            title = _("Are you sure you want to quit?")
            msg = _("There are unapplied queued actions. Are you sure you want " \
                " to quit blivet-gui now?")

            dialog = message_dialogs.ConfirmDialog(self.main_window, title, msg)
            response = dialog.run()

            if response:
                Gtk.main_quit()

        else:
            Gtk.main_quit()

        return True
