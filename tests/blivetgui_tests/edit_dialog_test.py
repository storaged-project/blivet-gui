import os
import unittest
from unittest.mock import MagicMock, Mock, patch

from blivet.size import Size

from blivetgui.dialogs.edit_dialog import FormatDialog, MountpointDialog, LabelDialog, UnmountDialog, ResizeDialog, LVMEditDialog, RenameDialog
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

        # empty mountpoint is also valid
        dialog.mnt_entry.set_text("")
        succ = dialog.validate_user_input()
        self.assertTrue(succ)

        with patch.object(dialog.dialog, "run", lambda: Gtk.ResponseType.ACCEPT):
            ret = dialog.run()
            self.assertEqual(ret.edit_device, dev)
            self.assertTrue(ret.do_set)
            self.assertEqual(ret.mountpoint, "")


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

        # deselect all mountpoints
        dialog.mountpoints_store[0][0] = False
        dialog.mountpoints_store[1][0] = False

        with patch.object(dialog.dialog, "run", lambda: Gtk.ResponseType.ACCEPT):
            ret = dialog.run()
            self.assertEqual(ret.edit_device, dev)
            self.assertTrue(ret.unmount)
            self.assertListEqual(ret.mountpoints, [])

        # single mountpoint
        dialog = UnmountDialog(self.parent_window, dev, mountpoints=["/mnt/test"], installer_mode=False)

        self.assertEqual(len(dialog.mountpoints_store), 1)
        self.assertTrue(dialog.mountpoints_store[0][0])
        self.assertEqual(dialog.mountpoints_store[0][1], "/mnt/test")


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

        # no size change (set to the same size)
        dialog = ResizeDialog(self.parent_window, dev, resize_info=resize_info)
        dialog.size_chooser.selected_size = Size("1 GiB")

        with patch.object(dialog.dialog, "run", lambda: Gtk.ResponseType.ACCEPT):
            ret = dialog.run()
            self.assertEqual(ret.edit_device, dev)
            self.assertFalse(ret.resize)
            self.assertEqual(ret.size, Size("1 GiB"))


@unittest.skipUnless("DISPLAY" in os.environ.keys(), "requires X server")
class RenameDialogTest(unittest.TestCase):

    error_dialog = MagicMock()

    @classmethod
    def setUpClass(cls):
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk

        cls.parent_window = Gtk.Window()

    @patch("blivetgui.dialogs.message_dialogs.ErrorDialog", error_dialog)
    def test_basic(self):
        vg = MagicMock()
        vg.configure_mock(name="testvg")
        dev = MagicMock()
        dev.configure_mock(type="lvmlv", name="testvg-testlv", lvname="testlv", vg=vg)

        dialog = RenameDialog(self.parent_window, dev, names=["testvg-otherlv"], installer_mode=False)

        # test same name as current
        dialog.entry_rename.set_text("testlv")
        succ = dialog._validate_user_input("testlv")
        self.assertFalse(succ)

        # test name already in use
        dialog.entry_rename.set_text("otherlv")
        succ = dialog._validate_user_input("otherlv")
        self.assertFalse(succ)

        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk

        # test accept with valid name
        dialog = RenameDialog(self.parent_window, dev, names=[], installer_mode=False)
        with patch("blivetgui.dialogs.helpers.is_name_valid", return_value=True):
            dialog.entry_rename.set_text("newname")

            with patch.object(dialog.dialog, "run", lambda: Gtk.ResponseType.ACCEPT):
                ret = dialog.run()
                self.assertEqual(ret.edit_device, dev)
                self.assertTrue(ret.rename)
                self.assertEqual(ret.name, "newname")

        # test reject
        dialog = RenameDialog(self.parent_window, dev, names=[], installer_mode=False)
        with patch("blivetgui.dialogs.helpers.is_name_valid", return_value=True):
            dialog.entry_rename.set_text("newname")
            with patch.object(dialog.dialog, "run", lambda: Gtk.ResponseType.REJECT):
                ret = dialog.run()
                self.assertEqual(ret.edit_device, dev)
                self.assertFalse(ret.rename)
                self.assertIsNone(ret.name)


@unittest.skipUnless("DISPLAY" in os.environ.keys(), "requires X server")
class LVMEditDialogTest(unittest.TestCase):

    error_dialog = MagicMock()

    @classmethod
    def setUpClass(cls):
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk

        cls.parent_window = Gtk.Window()

    @patch("blivetgui.dialogs.message_dialogs.ErrorDialog", error_dialog)
    def test_no_free_space_for_add(self):
        """Test LVMEditDialog when there's no free space to add parents"""

        # create mock VG with existing PVs (configure mock attributes properly)
        pv1 = MagicMock()
        pv1.configure_mock(name="pv1", size=Size("1 GiB"))
        vg = MagicMock()
        vg.configure_mock(name="testvg", parents=[pv1], pvs=[pv1], free_extents=0, pe_size=Size("4 MiB"))

        dialog = LVMEditDialog(self.parent_window, vg, free_info=[])

        # should show "no empty physical volumes" message
        self.assertIsNone(dialog.add_store)
        self.assertIn("add", dialog.widgets_dict)
        self.assertEqual(len(dialog.widgets_dict["add"]), 1)

    @patch("blivetgui.dialogs.message_dialogs.ErrorDialog", error_dialog)
    def test_no_removable_pvs(self):
        """Test LVMEditDialog when there are no removable PVs"""

        # create mock VG where all PVs are in use
        pv1 = MagicMock()
        pv1.configure_mock(name="pv1", size=Size("1 GiB"))
        vg = MagicMock()
        vg.configure_mock(name="testvg", parents=[pv1], pvs=[pv1], free_extents=0, pe_size=Size("4 MiB"))

        dialog = LVMEditDialog(self.parent_window, vg, free_info=[])

        # should show "no removable PVs" message
        self.assertIsNone(dialog.remove_store)
        self.assertIn("remove", dialog.widgets_dict)
        self.assertEqual(len(dialog.widgets_dict["remove"]), 1)

    @patch("blivetgui.dialogs.message_dialogs.ErrorDialog", error_dialog)
    def test_add_parents_available(self):
        """Test LVMEditDialog with available devices to add"""

        pv1 = MagicMock()
        pv1.configure_mock(name="pv1", size=Size("1 GiB"))
        vg = MagicMock()
        vg.configure_mock(name="testvg", parents=[pv1], pvs=[pv1], free_extents=100, pe_size=Size("4 MiB"))

        # mock available free space
        new_pv = MagicMock()
        new_pv.configure_mock(name="pv2", type="partition")
        free_region = MagicMock()
        free_region.configure_mock(parents=[new_pv], size=Size("1 GiB"))
        free_info = [("lvmpv", free_region)]

        dialog = LVMEditDialog(self.parent_window, vg, free_info=free_info)

        # should have add_store with one row
        self.assertIsNotNone(dialog.add_store)
        self.assertEqual(len(dialog.add_store), 1)
        self.assertEqual(dialog.add_store[0][3], "pv2")  # device name
        self.assertFalse(dialog.add_store[0][2])  # initially not selected

    @patch("blivetgui.dialogs.message_dialogs.ErrorDialog", error_dialog)
    def test_add_disk_free_region(self):
        """Test adding a disk free region to VG"""

        pv1 = MagicMock()
        pv1.configure_mock(name="pv1", size=Size("1 GiB"))
        vg = MagicMock()
        vg.configure_mock(name="testvg", parents=[pv1], pvs=[pv1], free_extents=100, pe_size=Size("4 MiB"))

        # mock free region on a disk
        disk = MagicMock()
        disk.configure_mock(name="sda", type="disk")
        free_region = MagicMock()
        free_region.configure_mock(parents=[disk], size=Size("5 GiB"))
        free_info = [("disk", free_region)]

        dialog = LVMEditDialog(self.parent_window, vg, free_info=free_info)

        # should have add_store with disk free region
        self.assertIsNotNone(dialog.add_store)
        self.assertEqual(len(dialog.add_store), 1)
        self.assertEqual(dialog.add_store[0][3], "sda")  # disk name
        self.assertEqual(dialog.add_store[0][4], "free region")  # type

    @patch("blivetgui.dialogs.message_dialogs.ErrorDialog", error_dialog)
    def test_toggle_buttons(self):
        """Test add/remove toggle buttons in LVMEditDialog"""

        pv1 = MagicMock()
        pv1.configure_mock(name="pv1", size=Size("1 GiB"))
        pv2 = MagicMock()
        pv2.configure_mock(name="pv2", size=Size("1 GiB"))
        vg = MagicMock()
        vg.configure_mock(name="testvg", parents=[pv1, pv2], pvs=[pv1, pv2],
                          free_extents=260, pe_size=Size("4 MiB"))

        new_pv = MagicMock()
        new_pv.configure_mock(name="pv3", type="partition")
        free_region = MagicMock()
        free_region.configure_mock(parents=[new_pv], size=Size("1 GiB"))
        free_info = [("lvmpv", free_region)]

        dialog = LVMEditDialog(self.parent_window, vg, free_info=free_info)

        # toggle add button
        dialog.button_add.set_active(True)
        self.assertTrue(dialog.button_add.get_active())
        self.assertFalse(dialog.button_remove.get_active())

        # toggle remove button
        dialog.button_remove.set_active(True)
        self.assertTrue(dialog.button_remove.get_active())
        self.assertFalse(dialog.button_add.get_active())

    @patch("blivetgui.dialogs.message_dialogs.ErrorDialog", error_dialog)
    def test_get_selection(self):
        # adding
        pv1 = MagicMock()
        pv1.configure_mock(name="pv1", size=Size("1 GiB"))
        vg = MagicMock()
        vg.configure_mock(name="testvg", parents=[pv1], pvs=[pv1], free_extents=100, pe_size=Size("4 MiB"))

        pv2 = MagicMock()
        pv2.configure_mock(name="pv2", type="partition", size=Size("1 GiB"))
        free_region = MagicMock()
        free_region.configure_mock(parents=[pv2], size=Size("1 GiB"))
        free_info = [("lvmpv", free_region)]

        dialog = LVMEditDialog(self.parent_window, vg, free_info=free_info)

        # activate add button and select a device
        dialog.button_add.set_active(True)
        dialog.add_store[0][2] = True  # select first device

        selection = dialog.get_selection()
        self.assertEqual(selection.edit_device, vg)
        self.assertEqual(selection.action_type, "add")
        self.assertEqual(len(selection.parents_list), 1)
        self.assertEqual(selection.parents_list[0].name, "pv2")

        # removing
        vg.configure_mock(name="testvg", parents=[pv1, pv2], pvs=[pv1, pv2],
                          free_extents=260, pe_size=Size("4 MiB"))

        dialog = LVMEditDialog(self.parent_window, vg, free_info=[])

        # activate remove button and select a device
        dialog.button_remove.set_active(True)
        dialog.remove_store[0][2] = True  # select first device

        selection = dialog.get_selection()
        self.assertEqual(selection.edit_device, vg)
        self.assertEqual(selection.action_type, "remove")
        self.assertEqual(len(selection.parents_list), 1)


if __name__ == "__main__":
    unittest.main()
