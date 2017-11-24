# -*- coding: utf-8 -*-

import os
import unittest
from unittest.mock import MagicMock, patch

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk

from blivet.size import Size

from blivetgui.dialogs.edit_dialog import FormatDialog
from blivetgui.i18n import _

from add_dialog_test import supported_filesystems


@unittest.skipUnless("DISPLAY" in os.environ.keys(), "requires X server")
class FormatDialogTest(unittest.TestCase):

    error_dialog = MagicMock()
    parent_window = Gtk.Window()

    @classmethod
    def setUpClass(cls):
        cls.supported_filesystems = supported_filesystems()

    def test_basic(self):

        dev = MagicMock(size=Size("1 GiB"), format=MagicMock(mountpoint=None))
        dialog = FormatDialog(self.parent_window, dev, self.supported_filesystems, [], False)

        # not installer_mode, mountpoint widgets should be invisible
        self.assertFalse(dialog.mnt_box.get_visible())

        # test filesystem selection
        fs = next((f for f in supported_filesystems()), None)
        if fs:
            dialog.fs_combo.set_active_id(fs.type)

            selected_fs, selected_label, selected_mnt = dialog.get_selection()
            self.assertEqual(selected_fs, fs.type)
            self.assertIsNone(selected_label)
            self.assertIsNone(selected_mnt)

            # test label selection
            if fs.labeling():
                self.assertTrue(dialog.label_entry.get_sensitive())
                dialog.label_entry.set_text("label")
                selected_fs, selected_label, selected_mnt = dialog.get_selection()
                self.assertEqual(selected_label, "label")
            else:
                self.assertFalse(dialog.label_entry.get_sensitive())

        # test 'unformatted' selection
        dialog.fs_combo.set_active_id("unformatted")
        self.assertFalse(dialog.label_entry.get_sensitive())
        selected_fs, selected_label, selected_mnt = dialog.get_selection()
        self.assertIsNone(selected_fs)
        self.assertIsNone(selected_label)
        self.assertIsNone(selected_mnt)

    @patch("blivetgui.dialogs.message_dialogs.ErrorDialog", error_dialog)
    def test_installer(self):
        dev = MagicMock(size=Size("1 GiB"), format=MagicMock(mountpoint=None))

        dialog = FormatDialog(self.parent_window, dev, self.supported_filesystems, [], True)

        # ninstaller_mode, mountpoint widgets should be visible
        self.assertTrue(dialog.mnt_entry.get_visible())

        # test mountpoint entry sensitivity (insensitive for not mountable) and selection
        fstype = next((fs.type for fs in supported_filesystems() if fs.mountable), None)
        if fstype:
            dialog.fs_combo.set_active_id(fstype)
            dialog.mnt_entry.set_text("/boot")

            selected_fs, _selected_label, selected_mnt = dialog.get_selection()
            self.assertTrue(dialog.mnt_entry.get_sensitive())
            self.assertEqual(selected_fs, fstype)
            self.assertEqual(selected_mnt, "/boot")

        # test 'unformatted' selection (can't set mountpoint for "none" format)
        dialog.fs_combo.set_active_id("unformatted")
        selected_fs, _selected_label, selected_mnt = dialog.get_selection()
        self.assertFalse(dialog.mnt_entry.get_sensitive())

        # test mountpoint validation
        fstype = next((fs.type for fs in supported_filesystems() if fs.mountable), None)
        if fstype:
            dialog.fs_combo.set_active_id(fstype)
            dialog.mnt_entry.set_text("aaaaa")
            dialog.validate_user_input()
            self.error_dialog.assert_any_call(dialog.dialog,
                                              _("\"{0}\" is not a valid mountpoint.").format("aaaaa"),
                                              False)

if __name__ == "__main__":
    unittest.main()
