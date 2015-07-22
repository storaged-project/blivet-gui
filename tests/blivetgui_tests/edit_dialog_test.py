# -*- coding: utf-8 -*-

import unittest
from unittest.mock import MagicMock, patch

from blivetgui.dialogs.edit_dialog import PartitionEditDialog

from blivet.size import Size

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk

class PartitionEditDialogTest(unittest.TestCase):

    parent_window = MagicMock(spec=Gtk.Window)
    edited_device = MagicMock(size=Size("1 GiB"))
    edited_device.configure_mock(name="vda1") # set name paremeter
    resize_info = MagicMock(resizable=True, error="Not resizable.", min_size=Size("1 MiB"), max_size=Size("1 GiB"))

    @patch("blivetgui.dialogs.edit_dialog.PartitionEditDialog.set_transient_for", lambda dialog, window: True)
    def test_resizable(self):
        # device is resizable, size widgtes should be active
        dialog = PartitionEditDialog(self.parent_window, self.edited_device, self.resize_info)

        self.assertTrue(dialog.widgets_dict["size"][0].get_sensitive())

        # device is not resizable, size widgtes should be inactive and message should be shown
        self.resize_info.configure_mock(resizable=False)
        dialog = PartitionEditDialog(self.parent_window, self.edited_device, self.resize_info)

        self.assertFalse(dialog.widgets_dict["size"][0].get_sensitive())
        self.assertTrue("info" in dialog.widgets_dict.keys())

        self.resize_info.configure_mock(resizable=True) # set mock settings back to default

    @patch("blivetgui.dialogs.edit_dialog.PartitionEditDialog.set_transient_for", lambda dialog, window: True)
    def test_format_check(self):
        dialog = PartitionEditDialog(self.parent_window, self.edited_device, self.resize_info)

        # format_check should be unchecked by default and filesystems_combo incactive
        self.assertFalse(dialog.format_check.get_active())
        self.assertFalse(dialog.filesystems_combo.get_sensitive())

        # format_check active -> filesystems_combo active and a fs is selected
        dialog.format_check.set_active(True)
        self.assertTrue(dialog.filesystems_combo.get_sensitive())
        self.assertIsNotNone(dialog.filesystems_combo.get_active_text())

    @patch("blivetgui.dialogs.edit_dialog.PartitionEditDialog.set_transient_for", lambda dialog, window: True)
    def test_mountpoint(self):
        dialog = PartitionEditDialog(self.parent_window, self.edited_device, self.resize_info, True)

        # in kickstart mode, mountpoint_entry is visible
        self.assertTrue(dialog.mountpoint_entry.get_visible())


    @patch("blivetgui.dialogs.edit_dialog.PartitionEditDialog.set_transient_for", lambda dialog, window: True)
    def test_selection_format(self):
        dialog = PartitionEditDialog(self.parent_window, self.edited_device, self.resize_info, True)

        # select the format_check
        dialog.format_check.set_active(True)

        selection = dialog.get_selection()

        # check the results -- device should be resized without formatting and mountpoint
        self.assertEqual(selection.edit_device, self.edited_device)
        self.assertFalse(selection.resize)
        self.assertTrue(selection.fmt)
        self.assertIsNotNone(selection.filesystem)

    @patch("blivetgui.dialogs.edit_dialog.PartitionEditDialog.set_transient_for", lambda dialog, window: True)
    def test_selection_resize(self):
        dialog = PartitionEditDialog(self.parent_window, self.edited_device, self.resize_info, True)

        # select new size
        size_area = dialog.widgets_dict["size"][0]
        size_area.scale.set_value(size_area.scale.get_value() // 2)

        # select new mountpoint
        dialog.mountpoint_entry.get_buffer().set_text("/home", len("/home"))

        selection = dialog.get_selection()

        # check the results -- device should be resized without formatting and mountpoint
        self.assertEqual(selection.edit_device, self.edited_device)
        self.assertTrue(selection.resize)
        self.assertFalse(selection.fmt)
        self.assertIsNone(selection.filesystem)
        self.assertEqual(selection.mountpoint, "/home")






if __name__ == "__main__":
    unittest.main()
