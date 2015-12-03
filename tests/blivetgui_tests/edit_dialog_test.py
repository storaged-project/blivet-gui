# -*- coding: utf-8 -*-

import unittest
from unittest.mock import MagicMock, patch

from blivetgui.dialogs.edit_dialog import PartitionEditDialog

from blivetgui.i18n import _

from blivet.size import Size

import os

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk


@unittest.skipUnless("DISPLAY" in os.environ.keys(), "requires X server")
class PartitionEditDialogTest(unittest.TestCase):

    error_dialog = MagicMock()

    @classmethod
    def setUpClass(cls):
        cls.parent_window = MagicMock(spec=Gtk.Window)
        cls.edited_device = MagicMock(type="partition", size=Size("1 GiB"), format=MagicMock(mountpoint=""))
        cls.edited_device.configure_mock(name="vda1")  # set name paremeter
        cls.resize_info = MagicMock(resizable=True, error="Not resizable.", min_size=Size("1 MiB"), max_size=Size("1 GiB"))
        cls.supported_fs = ["ext4", "xfs"]

    @patch("blivetgui.dialogs.edit_dialog.PartitionEditDialog.set_transient_for", lambda dialog, window: True)
    def test_resizable(self):
        # device is resizable, size widgtes should be active
        dialog = PartitionEditDialog(self.parent_window, self.edited_device, self.resize_info, self.supported_fs, [])

        self.assertTrue(dialog.widgets_dict["size"][0].get_sensitive())

        # device is not resizable, size widgtes should be inactive and message should be shown
        self.resize_info.configure_mock(resizable=False)
        dialog = PartitionEditDialog(self.parent_window, self.edited_device, self.resize_info, self.supported_fs, [])

        self.assertFalse(dialog.widgets_dict["size"][0].get_sensitive())
        self.assertTrue("info" in dialog.widgets_dict.keys())

        self.resize_info.configure_mock(resizable=True)  # set mock settings back to default

    @patch("blivetgui.dialogs.edit_dialog.PartitionEditDialog.set_transient_for", lambda dialog, window: True)
    def test_formattable(self):
        self.edited_device.configure_mock(is_extended=True)
        dialog = PartitionEditDialog(self.parent_window, self.edited_device, self.resize_info, self.supported_fs, [])

        # extended partition -- all fs widgets should be inactive
        self.assertFalse(any(w.get_sensitive() for w in dialog.widgets_dict["fs"]))

        self.edited_device.configure_mock(is_extended=False)
        dialog = PartitionEditDialog(self.parent_window, self.edited_device, self.resize_info, self.supported_fs, [])

        # 'normal' partition -- format check should be active
        self.assertTrue(dialog.format_check.get_sensitive())

    @patch("blivetgui.dialogs.edit_dialog.PartitionEditDialog.set_transient_for", lambda dialog, window: True)
    def test_format_check(self):
        dialog = PartitionEditDialog(self.parent_window, self.edited_device, self.resize_info, self.supported_fs, [])

        # format_check should be unchecked by default and filesystems_combo and fslabel_entry incactive
        self.assertFalse(dialog.format_check.get_active())
        self.assertFalse(dialog.filesystems_combo.get_sensitive())
        self.assertFalse(dialog.fslabel_entry.get_sensitive())

        # format_check active -> filesystems_combo and fslabel_entry active and a fs is selected
        dialog.format_check.set_active(True)
        self.assertTrue(dialog.filesystems_combo.get_sensitive())
        self.assertTrue(dialog.fslabel_entry.get_sensitive())
        self.assertIsNotNone(dialog.filesystems_combo.get_active_text())

    @patch("blivetgui.dialogs.edit_dialog.PartitionEditDialog.set_transient_for", lambda dialog, window: True)
    def test_mountpoint(self):
        dialog = PartitionEditDialog(self.parent_window, self.edited_device, self.resize_info, self.supported_fs, [], True)

        # in kickstart mode, mountpoint_entry is visible
        self.assertTrue(dialog.mountpoint_entry.get_visible())

    @patch("blivetgui.dialogs.edit_dialog.PartitionEditDialog.set_transient_for", lambda dialog, window: True)
    def test_selection_format(self):
        dialog = PartitionEditDialog(self.parent_window, self.edited_device, self.resize_info, self.supported_fs, [], True)

        # select the format_check
        dialog.format_check.set_active(True)
        dialog.fslabel_entry.set_text("Label")

        selection = dialog.get_selection()

        # check the results -- device should be resized without formatting and mountpoint
        self.assertEqual(selection.edit_device, self.edited_device)
        self.assertFalse(selection.resize)
        self.assertTrue(selection.fmt)
        self.assertIsNotNone(selection.filesystem)
        self.assertEqual(selection.label, "Label")

    @patch("blivetgui.dialogs.edit_dialog.PartitionEditDialog.set_transient_for", lambda dialog, window: True)
    def test_selection_resize(self):
        dialog = PartitionEditDialog(self.parent_window, self.edited_device, self.resize_info, self.supported_fs, [], True)

        # select new size
        size_area = dialog.widgets_dict["size"][0]
        size_area._scale.set_value(size_area._scale.get_value() // 2)

        # select new mountpoint
        dialog.mountpoint_entry.get_buffer().set_text("/home", len("/home"))

        selection = dialog.get_selection()

        # check the results -- device should be resized without formatting and mountpoint
        self.assertEqual(selection.edit_device, self.edited_device)
        self.assertTrue(selection.resize)
        self.assertFalse(selection.fmt)
        self.assertIsNone(selection.filesystem)
        self.assertEqual(selection.mountpoint, "/home")

    @patch("blivetgui.dialogs.edit_dialog.PartitionEditDialog.set_transient_for", lambda dialog, window: True)
    @patch("blivetgui.dialogs.message_dialogs.ErrorDialog", error_dialog)
    def test_label_validity_check(self):
        dialog = PartitionEditDialog(self.parent_window, self.edited_device, self.resize_info, self.supported_fs, [], True)

        # valid label
        label = "a" * 5
        dialog.format_check.set_active(True)
        dialog.filesystems_combo.set_active_id("ext4")
        dialog.fslabel_entry.set_text(label)

        dialog.validate_user_input()
        self.assertFalse(self.error_dialog.called)  # valid label, no error_dialog
        self.error_dialog.reset_mock()

        # invalid label for ext4 (too long)
        label = "a" * 50
        dialog.format_check.set_active(True)
        dialog.filesystems_combo.set_active_id("ext4")
        dialog.fslabel_entry.set_text(label)

        dialog.validate_user_input()
        self.error_dialog.assert_any_call(dialog, _("\"{label}\" is not a valid label.").format(label=label))
        self.error_dialog.reset_mock()

    @patch("blivetgui.dialogs.edit_dialog.PartitionEditDialog.set_transient_for", lambda dialog, window: True)
    @patch("blivetgui.dialogs.message_dialogs.ErrorDialog", error_dialog)
    def test_mountpoint_validity_check(self):
        dialog = PartitionEditDialog(self.parent_window, self.edited_device, self.resize_info, self.supported_fs, ["/root", "/var"], True)

        # valid mountpoint
        dialog.mountpoint_entry.set_text("/home")
        dialog.validate_user_input()
        self.assertFalse(self.error_dialog.called)
        self.error_dialog.reset_mock()

        # invalid mountpoint
        mnt = "home"
        dialog.mountpoint_entry.set_text(mnt)
        dialog.validate_user_input()
        self.error_dialog.assert_any_call(dialog, _("\"{0}\" is not a valid mountpoint.").format(mnt))
        self.error_dialog.reset_mock()

        # duplicate mountpoint
        mnt = "/root"
        dialog.mountpoint_entry.set_text(mnt)
        dialog.validate_user_input()
        self.error_dialog.assert_any_call(dialog, "Selected mountpoint \"%s\" is already set for another device." % mnt)
        self.error_dialog.reset_mock()

        # same mountpoint
        self.edited_device.format.configure_mock(mountpoint="/var")
        dialog.mountpoint_entry.set_text("/var")
        dialog.validate_user_input()
        self.assertFalse(self.error_dialog.called)  # no change --> no error
        self.error_dialog.reset_mock()
        self.edited_device.format.configure_mock(mountpoint="")

if __name__ == "__main__":
    unittest.main()
