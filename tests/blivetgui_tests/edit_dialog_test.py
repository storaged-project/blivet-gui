import os
import unittest
from unittest.mock import MagicMock, Mock, patch

from blivet.size import Size

from blivetgui.dialogs.edit_dialog import FormatDialog, MountpointDialog, LabelDialog, UnmountDialog, ResizeDialog
from blivetgui.i18n import _

from .add_dialog_test import supported_filesystems


@unittest.skipUnless("DISPLAY" in os.environ.keys(), "requires X server")
class FormatDialogTest(unittest.TestCase):

    error_dialog = MagicMock()

    @classmethod
    def setUpClass(cls):
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk

        cls.parent_window = Gtk.Window()
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


@unittest.skipUnless("DISPLAY" in os.environ.keys(), "requires X server")
class MountpointDialogTest(unittest.TestCase):

    error_dialog = MagicMock()

    @classmethod
    def setUpClass(cls):
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk

        cls.parent_window = Gtk.Window()

    @patch("blivetgui.dialogs.message_dialogs.ErrorDialog", error_dialog)
    def test_installer(self):
        dev = MagicMock(size=Size("1 GiB"), format=MagicMock(mountable=True, mountpoint="/var"))

        dialog = MountpointDialog(self.parent_window, dev, mountpoints=["/home"], installer_mode=True)

        # existing mountpoint should be pre-selected
        self.assertEqual(dialog.mnt_entry.get_text(), "/var")

        # invalid mountpoint
        dialog.mnt_entry.set_text("aaaaa")
        succ = dialog.validate_user_input()
        self.assertFalse(succ)
        self.error_dialog.assert_any_call(dialog.dialog,
                                          _("\"{0}\" is not a valid mountpoint.").format("aaaaa"),
                                          False)

        # mountpoint already in use
        dialog.mnt_entry.set_text("/home")
        succ = dialog.validate_user_input()
        self.assertFalse(succ)
        self.error_dialog.assert_any_call(dialog.dialog,
                                          _("Selected mountpoint \"{0}\" is already set for another device.").format("/home"),
                                          False)

        # valid mountpoint
        dialog.mnt_entry.set_text("/etc")
        succ = dialog.validate_user_input()
        self.assertTrue(succ)

        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk

        with patch.object(dialog.dialog, "run", lambda: Gtk.ResponseType.REJECT):
            ret = dialog.run()
            self.assertEqual(ret.edit_device, dev)
            self.assertFalse(ret.do_set)
            self.assertIsNone(ret.mountpoint)

        # valid mountpoint
        dialog.mnt_entry.set_text("/etc")
        succ = dialog.validate_user_input()
        self.assertTrue(succ)

        with patch.object(dialog.dialog, "run", lambda: Gtk.ResponseType.ACCEPT):
            ret = dialog.run()
            self.assertEqual(ret.edit_device, dev)
            self.assertTrue(ret.do_set)
            self.assertEqual(ret.mountpoint, "/etc")


@unittest.skipUnless("DISPLAY" in os.environ.keys(), "requires X server")
class LabelDialogTest(unittest.TestCase):

    error_dialog = MagicMock()

    @classmethod
    def setUpClass(cls):
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk

        cls.parent_window = Gtk.Window()

    @patch("blivetgui.dialogs.message_dialogs.ErrorDialog", error_dialog)
    def test_basic(self):
        fmt = MagicMock()
        dev = MagicMock(size=Size("1 GiB"), format=fmt)

        dialog = LabelDialog(self.parent_window, dev, installer_mode=False)

        # invalid label
        attrs = {"label_format_ok.return_value": False}
        fmt.configure_mock(**attrs)
        dialog.entry_label.set_text("aaaaa")
        succ = dialog._validate_user_input("aaaaa")
        self.assertFalse(succ)
        self.error_dialog.assert_any_call(dialog.dialog,
                                          _("'{label}' is not a valid label for this filesystem").format(label="aaaaa"),
                                          True)

        # valid label
        attrs = {"label_format_ok.return_value": True}
        fmt.configure_mock(**attrs)
        dialog.entry_label.set_text("aaaaa")
        succ = dialog._validate_user_input("aaaaa")
        self.assertTrue(succ)

        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk

        with patch.object(dialog.dialog, "run", lambda: Gtk.ResponseType.REJECT):
            ret = dialog.run()
            self.assertEqual(ret.edit_device, dev)
            self.assertFalse(ret.relabel)
            self.assertIsNone(ret.label)

        # valid label
        attrs = {"label_format_ok.return_value": True}
        fmt.configure_mock(**attrs)
        dialog.entry_label.set_text("aaaaa")
        succ = dialog._validate_user_input("aaaaa")
        self.assertTrue(succ)

        with patch.object(dialog.dialog, "run", lambda: Gtk.ResponseType.ACCEPT):
            ret = dialog.run()
            self.assertEqual(ret.edit_device, dev)
            self.assertTrue(ret.relabel)
            self.assertEqual(ret.label, "aaaaa")


@unittest.skipUnless("DISPLAY" in os.environ.keys(), "requires X server")
class UnmountDialogTest(unittest.TestCase):

    error_dialog = MagicMock()

    @classmethod
    def setUpClass(cls):
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk

        cls.parent_window = Gtk.Window()

    @patch("blivetgui.dialogs.message_dialogs.ErrorDialog", error_dialog)
    def test_basic(self):
        fmt = MagicMock()
        dev = MagicMock(size=Size("1 GiB"), format=fmt)

        dialog = UnmountDialog(self.parent_window, dev, mountpoints=["/mnt/a", "/mnt/b"], installer_mode=False)

        self.assertEqual(len(dialog.mountpoints_store), 2)
        self.assertTrue(dialog.mountpoints_store[0][0])
        self.assertEqual(dialog.mountpoints_store[0][1], "/mnt/a")
        self.assertTrue(dialog.mountpoints_store[1][0])
        self.assertEqual(dialog.mountpoints_store[1][1], "/mnt/b")

        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk

        with patch.object(dialog.dialog, "run", lambda: Gtk.ResponseType.REJECT):
            ret = dialog.run()
            self.assertEqual(ret.edit_device, dev)
            self.assertFalse(ret.unmount)
            self.assertListEqual(ret.mountpoints, [])

        dialog = UnmountDialog(self.parent_window, dev, mountpoints=["/mnt/a", "/mnt/b"], installer_mode=False)

        with patch.object(dialog.dialog, "run", lambda: Gtk.ResponseType.ACCEPT):
            ret = dialog.run()
            self.assertEqual(ret.edit_device, dev)
            self.assertTrue(ret.unmount)
            self.assertListEqual(ret.mountpoints, ["/mnt/a", "/mnt/b"])

        # deselect second mountpoint
        dialog = UnmountDialog(self.parent_window, dev, mountpoints=["/mnt/a", "/mnt/b"], installer_mode=False)
        dialog.mountpoints_store[1][0] = False

        with patch.object(dialog.dialog, "run", lambda: Gtk.ResponseType.ACCEPT):
            ret = dialog.run()
            self.assertEqual(ret.edit_device, dev)
            self.assertTrue(ret.unmount)
            self.assertListEqual(ret.mountpoints, ["/mnt/a"])


@unittest.skipUnless("DISPLAY" in os.environ.keys(), "requires X server")
class ResizeDialogTest(unittest.TestCase):

    error_dialog = MagicMock()

    @classmethod
    def setUpClass(cls):
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk

        cls.parent_window = Gtk.Window()

    @patch("blivetgui.dialogs.message_dialogs.ErrorDialog", error_dialog)
    def test_basic(self):
        fmt = MagicMock()
        dev = MagicMock(size=Size("1 GiB"), format=fmt)

        # device is not resizable
        resize_info = Mock(resizable=False, error="test", min_size=Size("1 MiB"), max_size=dev.size)
        dialog = ResizeDialog(self.parent_window, dev, resize_info=resize_info)

        self.assertIsNone(dialog.size_chooser)
        button_resize = dialog.builder.get_object("button_resize")
        self.assertFalse(button_resize.get_visible(), False)

        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk

        with patch.object(dialog.dialog, "run", lambda: Gtk.ResponseType.REJECT):
            ret = dialog.run()
            self.assertEqual(ret.edit_device, dev)
            self.assertFalse(ret.resize)
            self.assertIsNone(ret.size)

        dialog = ResizeDialog(self.parent_window, dev, resize_info=resize_info)

        with patch.object(dialog.dialog, "run", lambda: Gtk.ResponseType.ACCEPT):
            ret = dialog.run()
            self.assertEqual(ret.edit_device, dev)
            self.assertFalse(ret.resize)
            self.assertIsNone(ret.size)

        # device is resizable
        resize_info = Mock(resizable=True, error=None, min_size=Size("1 MiB"), max_size=dev.size)
        dialog = ResizeDialog(self.parent_window, dev, resize_info=resize_info)

        self.assertIsNotNone(dialog.size_chooser)
        button_resize = dialog.builder.get_object("button_resize")
        self.assertTrue(button_resize.get_visible(), False)

        dialog.size_chooser.selected_size = Size("10 MiB")

        with patch.object(dialog.dialog, "run", lambda: Gtk.ResponseType.ACCEPT):
            ret = dialog.run()
            self.assertEqual(ret.edit_device, dev)
            self.assertTrue(ret.resize)
            self.assertEqual(ret.size, Size("10 MiB"))


if __name__ == "__main__":
    unittest.main()
