# -*- coding: utf-8 -*-

import unittest
from unittest.mock import Mock, MagicMock, patch

from blivetgui.dialogs.add_dialog import AdvancedOptions, AddDialog
from blivetgui.i18n import _

import os

from blivet.size import Size
from blivet import formats
from blivet.devicelibs import raid


def supported_filesystems():
    _fs_types = []

    _supported_fs = ["ext2", "ext3", "ext4", "xfs", "swap", "lvmpv"]

    for cls in formats.device_formats.values():
        obj = cls()
        if obj.type in _supported_fs:
            _fs_types.append(obj)

    return sorted(_fs_types, key=lambda fs: fs.type)


@unittest.skipUnless("DISPLAY" in os.environ.keys(), "requires X server")
class AdvancedOptionsTest(unittest.TestCase):

    error_dialog = MagicMock()

    @classmethod
    def setUpClass(cls):
        cls.add_dialog = Mock(show_widgets=Mock(return_value=True), hide_widgets=Mock(return_value=True))

    def test_lvm_options(self):
        # test lvm options are displayed for lvm/lvmvg type
        parent_device = Mock(type="disk", format=Mock(label_type="gpt", extended_partition=None))
        free_device = Mock(is_logical=False, size=Size("8 GiB"))

        advanced_options = AdvancedOptions(add_dialog=self.add_dialog, device_type="lvm",
                                           parent_device=parent_device, free_device=free_device)

        self.assertFalse(hasattr(advanced_options, "partition_combo"))
        self.assertTrue(hasattr(advanced_options, "pesize_combo"))
        self.assertFalse(hasattr(advanced_options, "chunk_combo"))

        advanced_options = AdvancedOptions(add_dialog=self.add_dialog, device_type="lvmvg",
                                           parent_device=parent_device, free_device=free_device)

        self.assertFalse(hasattr(advanced_options, "partition_combo"))
        self.assertTrue(hasattr(advanced_options, "pesize_combo"))
        self.assertFalse(hasattr(advanced_options, "chunk_combo"))

    def test_allowed_pesize(self):
        # test allowed pesize options based on free space available
        parent_device = Mock(type="disk", format=Mock(label_type="gpt", extended_partition=None))

        # only 8 MiB free space, allow only 2 and 4 MiB PE Size
        free_device = Mock(is_logical=False, size=Size("8 MiB"))
        advanced_options = AdvancedOptions(add_dialog=self.add_dialog, device_type="lvm",
                                           parent_device=parent_device, free_device=free_device)

        pesizes = [i[0] for i in advanced_options.pesize_combo.get_model()]
        self.assertEqual(["2 MiB", "4 MiB"], pesizes)

        # enough free space, allow up to 64 MiB PE Size
        free_device = Mock(is_logical=False, size=Size("1 GiB"))
        advanced_options = AdvancedOptions(add_dialog=self.add_dialog, device_type="lvm",
                                           parent_device=parent_device, free_device=free_device)

        pesizes = [i[0] for i in advanced_options.pesize_combo.get_model()]
        self.assertEqual(["2 MiB", "4 MiB", "8 MiB", "16 MiB", "32 MiB", "64 MiB"], pesizes)

    def test_partition_options(self):
        # test partition options are displayed for partition type

        parent_device = Mock(type="disk", format=Mock(label_type="msdos", extended_partition=None))
        free_device = Mock(is_logical=False)

        advanced_options = AdvancedOptions(add_dialog=self.add_dialog, device_type="partition",
                                           parent_device=parent_device, free_device=free_device)

        self.assertTrue(hasattr(advanced_options, "partition_combo"))
        self.assertFalse(hasattr(advanced_options, "pesize_combo"))
        self.assertFalse(hasattr(advanced_options, "chunk_combo"))

    def test_normal_partition(self):
        # "standard" situation -- disk with msdos part table, no existing extended partition
        # → both "primary and extended" types should be allowed

        parent_device = Mock(type="disk", format=Mock(label_type="msdos", extended_partition=None))
        free_device = Mock(is_logical=False)

        advanced_options = AdvancedOptions(add_dialog=self.add_dialog, device_type="partition",
                                           parent_device=parent_device, free_device=free_device)

        part_types = advanced_options.partition_combo.get_model()

        self.assertEqual(len(part_types), 2)
        self.assertEqual(part_types[0][1], "primary")
        self.assertEqual(part_types[1][1], "extended")

    def test_logical_partition(self):
        # adding partition to free space inside extended partition -> only "logical allowed"

        parent_device = Mock(type="disk", format=Mock(label_type="msdos", extended_partition=Mock()))
        free_device = Mock(is_logical=True)

        advanced_options = AdvancedOptions(add_dialog=self.add_dialog, device_type="partition",
                                           parent_device=parent_device, free_device=free_device)

        part_types = advanced_options.partition_combo.get_model()

        self.assertEqual(len(part_types), 1)
        self.assertEqual(part_types[0][1], "logical")

    def test_extended_partition(self):
        # extended partition already exists -> allow only "primary" type

        parent_device = Mock(type="disk", format=Mock(label_type="msdos", extended_partition=Mock()))
        free_device = Mock(is_logical=False)

        advanced_options = AdvancedOptions(add_dialog=self.add_dialog, device_type="partition",
                                           parent_device=parent_device, free_device=free_device)

        part_types = advanced_options.partition_combo.get_model()

        self.assertEqual(len(part_types), 1)
        self.assertEqual(part_types[0][1], "primary")

    def test_gpt_partitions(self):
        # adding partition on gpt disk -> only "primary" type allowed
        parent_device = Mock(type="disk", format=Mock(label_type="gpt", extended_partition=None))
        free_device = Mock(is_logical=False)

        advanced_options = AdvancedOptions(add_dialog=self.add_dialog, device_type="partition",
                                           parent_device=parent_device, free_device=free_device)

        part_types = advanced_options.partition_combo.get_model()

        self.assertEqual(len(part_types), 1)
        self.assertEqual(part_types[0][1], "primary")

    def test_mdraid_options(self):
        parent_device = Mock(type="disk", format=Mock(label_type="gpt", extended_partition=None))
        free_device = Mock(is_logical=False, size=Size("8 GiB"))

        advanced_options = AdvancedOptions(add_dialog=self.add_dialog, device_type="mdraid",
                                           parent_device=parent_device, free_device=free_device)

        self.assertFalse(hasattr(advanced_options, "partition_combo"))
        self.assertFalse(hasattr(advanced_options, "pesize_combo"))
        self.assertTrue(hasattr(advanced_options, "chunk_combo"))

    @patch("blivetgui.dialogs.message_dialogs.ErrorDialog", error_dialog)
    def test_mdraid_validation(self):
        parent_device = Mock(type="disk", format=Mock(label_type="gpt", extended_partition=None))
        free_device = Mock(is_logical=False, size=Size("8 GiB"))

        advanced_options = AdvancedOptions(add_dialog=self.add_dialog, device_type="mdraid",
                                           parent_device=parent_device, free_device=free_device)

        entry = advanced_options.chunk_combo.get_child()

        # invalid size specification
        entry.set_text("aaaaaaa")
        advanced_options.validate_user_input()
        self.error_dialog.assert_any_call(self.add_dialog, _("'{0}' is not a valid chunk size specification.").format("aaaaaaa"),
                                          not self.add_dialog.installer_mode)
        self.error_dialog.reset_mock()

        # invalid size
        entry.set_text("1 KiB")
        advanced_options.validate_user_input()
        self.error_dialog.assert_any_call(self.add_dialog, _("Chunk size must be multiple of 4 KiB."),
                                          not self.add_dialog.installer_mode)
        self.error_dialog.reset_mock()

        # valid size
        entry.set_text("64 KiB")
        advanced_options.validate_user_input()
        self.assertFalse(self.error_dialog.called)
        self.error_dialog.reset_mock()

    def test_selection(self):
        # partition
        parent_device = Mock(type="disk", format=Mock(label_type="msdos", extended_partition=None))
        free_device = Mock(is_logical=False)
        advanced_options = AdvancedOptions(add_dialog=self.add_dialog, device_type="partition",
                                           parent_device=parent_device, free_device=free_device)

        advanced_options.partition_combo.set_active_id("extended")

        selection = advanced_options.get_selection()
        self.assertEqual(selection["parttype"], "extended")

        # lvm
        parent_device = Mock(type="disk", format=Mock(label_type="gpt", extended_partition=None))
        free_device = Mock(is_logical=False, size=Size("8 GiB"))
        advanced_options = AdvancedOptions(add_dialog=self.add_dialog, device_type="lvm",
                                           parent_device=parent_device, free_device=free_device)

        advanced_options.pesize_combo.set_active_id("64 MiB")

        selection = advanced_options.get_selection()
        self.assertEqual(selection["pesize"], Size("64 MiB"))

        # mdraid
        parent_device = Mock(type="disk", format=Mock(label_type="msdos", extended_partition=None))
        free_device = Mock(is_logical=False)
        advanced_options = AdvancedOptions(add_dialog=self.add_dialog, device_type="mdraid",
                                           parent_device=parent_device, free_device=free_device)

        advanced_options.chunk_combo.set_active_id("64 KiB")

        selection = advanced_options.get_selection()
        self.assertEqual(selection["chunk_size"], Size("64 KiB"))


@unittest.skipUnless("DISPLAY" in os.environ.keys(), "requires X server")
@patch("blivetgui.dialogs.add_dialog.get_monitor_size", lambda window: (1024, 768))
class AddDialogTest(unittest.TestCase):

    error_dialog = MagicMock()

    @classmethod
    def setUpClass(cls):
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk

        cls.parent_window = Gtk.Window()
        cls.supported_filesystems = supported_filesystems()

    def _get_free_device(self, size=Size("8 GiB"), logical=False, parent=None, **kwargs):
        if not parent:
            parent = self._get_parent_device(name="vda", dtype="disk", size=size)

        free_region = kwargs.get("is_free_region", True)
        empty_disk = kwargs.get("is_empty_disk", False)
        uninitialized_disk = kwargs.get("is_uninitialized_disk", False)

        return MagicMock(type="free_space", size=size, is_logical=logical, parents=[parent], disk=parent,
                         is_free_region=free_region, is_empty_disk=empty_disk, is_uninitialized_disk=uninitialized_disk)

    def _get_parent_device(self, name=None, dtype="disk", size=Size("8 GiB"), ftype="disklabel"):
        if not name:
            if dtype == "disk":
                name = "vda"
            else:
                name = "fedora"

        dev = MagicMock()
        dev.configure_mock(name=name, type=dtype, size=size,
                           format=MagicMock(type=ftype,
                                            sector_size=512,
                                            parted_disk=MagicMock(maxPartitionLength=4294967295)))
        if dtype != "disk":
            disk = self._get_parent_device()
            dev.configure_mock(disk=disk, parents=[disk])
        if dtype == "lvmvg":
            pv = MagicMock()
            disk = self._get_parent_device()
            pv.configure_mock(name="vda1", size=size, format=MagicMock(free=size), disk=disk, parents=[disk])
            dev.configure_mock(pe_size=Size("4 MiB"), free_space=size, pvs=[pv], parents=[pv],
                               pmspare_size=Size("4 MiB"))

        return dev

    def test_allowed_device_types(self):
        # disk with disklabel and enough free space, other disks available
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, parent_device, free_device,
                               [("free", free_device), ("free", self._get_free_device())],
                               self.supported_filesystems, [])

        types = sorted([i[1] for i in add_dialog.devices_combo.get_model()])

        self.assertTrue(sorted(["partition", "lvm", "btrfs volume", "mdraid"]) == types)
        self.assertTrue(add_dialog.devices_combo.get_sensitive())

        # disk with disklabel and not enough free space, no other disks available
        parent_device = self._get_parent_device(size=Size("200 MiB"))
        free_device = self._get_free_device(size=parent_device.size, parent=parent_device)

        add_dialog = AddDialog(self.parent_window, parent_device, free_device,
                               [("free", free_device)], self.supported_filesystems, [])

        types = sorted([i[1] for i in add_dialog.devices_combo.get_model()])

        self.assertTrue(sorted(["partition", "lvm"]) == types)
        self.assertTrue(add_dialog.devices_combo.get_sensitive())

        # lvmpv
        parent_device = self._get_parent_device(dtype="partition", ftype="lvmpv")
        parent_device.format.configure_mock(vg_name=None)
        free_device = parent_device

        add_dialog = AddDialog(self.parent_window, parent_device, free_device,
                               [("lvmpv", free_device)], self.supported_filesystems, [])

        types = sorted([i[1] for i in add_dialog.devices_combo.get_model()])
        self.assertTrue(sorted(["lvmvg"]) == types)
        self.assertFalse(add_dialog.devices_combo.get_sensitive())

        # lvmpv on disk
        parent_device = self._get_parent_device(dtype="disk", ftype="lvmpv")
        free_device = self._get_free_device(size=parent_device.size, parent=parent_device)
        parent_device.format.configure_mock(vg_name=None)
        add_dialog = AddDialog(self.parent_window, parent_device, free_device,
                               [("lvmpv", free_device)], self.supported_filesystems, [])

        types = sorted([i[1] for i in add_dialog.devices_combo.get_model()])
        self.assertTrue(sorted(["lvmvg"]) == types)
        self.assertFalse(add_dialog.devices_combo.get_sensitive())

    def test_partition_widgets(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, parent_device, free_device,
                               [("free", free_device)], self.supported_filesystems, [])

        add_dialog.devices_combo.set_active_id("partition")
        self.assertEqual(add_dialog.selected_type, "partition")

        self.assertTrue(add_dialog.filesystems_combo.get_visible())
        self.assertFalse(add_dialog.name_entry.get_visible())
        self.assertTrue(add_dialog._encryption_chooser._encrypt_check.get_visible())
        self.assertFalse(add_dialog._raid_chooser.get_visible())
        self.assertIsNotNone(add_dialog.advanced)
        self.assertFalse(add_dialog.md_type_combo.get_visible())
        self.assertTrue(add_dialog.size_area.get_sensitive())

    def test_lvm_widgets(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, parent_device, free_device,
                               [("free", free_device)], self.supported_filesystems, [])

        add_dialog.devices_combo.set_active_id("lvm")
        self.assertEqual(add_dialog.selected_type, "lvm")

        self.assertFalse(add_dialog.filesystems_combo.get_visible())
        self.assertTrue(add_dialog.name_entry.get_visible())
        self.assertTrue(add_dialog._encryption_chooser._encrypt_check.get_visible())
        self.assertFalse(add_dialog._raid_chooser.get_visible())
        self.assertIsNotNone(add_dialog.advanced)
        self.assertFalse(add_dialog.md_type_combo.get_visible())
        self.assertTrue(add_dialog.size_area.get_sensitive())

    def test_btrfsvolume_widgets(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, parent_device, free_device,
                               [("free", free_device)], self.supported_filesystems, [])

        add_dialog.devices_combo.set_active_id("btrfs volume")
        self.assertEqual(add_dialog.selected_type, "btrfs volume")

        self.assertFalse(add_dialog.filesystems_combo.get_visible())
        self.assertTrue(add_dialog.name_entry.get_visible())
        self.assertTrue(add_dialog._encryption_chooser._encrypt_check.get_visible())
        self.assertTrue(add_dialog._raid_chooser.get_visible())
        self.assertIsNone(add_dialog.advanced)
        self.assertFalse(add_dialog.md_type_combo.get_visible())
        self.assertTrue(add_dialog.size_area.get_sensitive())

    def test_mdraid_widgets(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, parent_device, free_device,
                               [("free", free_device), ("free", self._get_free_device())],
                               self.supported_filesystems, [])

        add_dialog.devices_combo.set_active_id("mdraid")
        self.assertEqual(add_dialog.selected_type, "mdraid")

        self.assertTrue(add_dialog.filesystems_combo.get_visible())
        self.assertTrue(add_dialog.name_entry.get_visible())
        self.assertTrue(add_dialog._encryption_chooser._encrypt_check.get_visible())
        self.assertIsNotNone(add_dialog.advanced)
        self.assertFalse(add_dialog.md_type_combo.get_visible())

    def test_partition_parents(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, parent_device, free_device,
                               [("free", free_device), ("free", self._get_free_device()), ("free", self._get_free_device())],
                               self.supported_filesystems, [])
        add_dialog.devices_combo.set_active_id("partition")

        # partition allows only one parent -- make sure we have the right one and it is selected
        self.assertEqual(len(add_dialog.parents_store), 1)
        self.assertEqual(add_dialog.parents_store[0][0], parent_device)
        self.assertEqual(add_dialog.parents_store[0][1], free_device)
        self.assertTrue(add_dialog.parents_store[0][2])
        self.assertTrue(add_dialog.parents_store[0][3])
        self.assertEqual(add_dialog.parents_store[0][5], "disk")

    def test_lvm_parents(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, parent_device, free_device,
                               [("free", free_device), ("free", self._get_free_device(size=Size("4 GiB"))), ("free", self._get_free_device(size=Size("4 GiB")))],
                               self.supported_filesystems, [])
        add_dialog.devices_combo.set_active_id("lvm")

        # lvm allows multiple parents -- make sure we have all available and the right one is selected
        self.assertEqual(len(add_dialog.parents_store), 3)
        self.assertEqual(add_dialog.parents_store[0][0], parent_device)
        self.assertEqual(add_dialog.parents_store[0][1], free_device)
        self.assertTrue(add_dialog.parents_store[0][2])
        self.assertFalse(add_dialog.parents_store[1][2])  # other two free devices shouldn't be selected
        self.assertFalse(add_dialog.parents_store[2][2])

    def test_lvmlv_parents(self):
        parent_device = self._get_parent_device(dtype="lvmvg", ftype=None)
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, parent_device, free_device,
                               [("free", free_device), ("free", self._get_free_device()), ("free", self._get_free_device())],
                               self.supported_filesystems, [])
        add_dialog.devices_combo.set_active_id("lvmlv")

        # lvmlv allows only one parent -- make sure we have the right one and it is selected
        self.assertEqual(len(add_dialog.parents_store), 1)
        self.assertEqual(add_dialog.parents_store[0][0], parent_device)
        self.assertEqual(add_dialog.parents_store[0][1], free_device)
        self.assertTrue(add_dialog.parents_store[0][2])
        self.assertTrue(add_dialog.parents_store[0][3])
        self.assertEqual(add_dialog.parents_store[0][5], "lvmvg")

    def test_btrfs_parents(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, parent_device, free_device,
                               [("free", free_device), ("free", self._get_free_device(size=Size("200 MiB"))), ("free", self._get_free_device(size=Size("4 GiB")))],
                               self.supported_filesystems, [])
        add_dialog.devices_combo.set_active_id("btrfs volume")

        # lvm allows multiple parents -- make sure we have all available (= larger than 256 MiB) and the right one is selected
        self.assertEqual(len(add_dialog.parents_store), 2)  # third device is smaller than min size for btrfs
        self.assertEqual(add_dialog.parents_store[0][0], parent_device)
        self.assertEqual(add_dialog.parents_store[0][1], free_device)
        self.assertTrue(add_dialog.parents_store[0][2])
        self.assertFalse(add_dialog.parents_store[1][2])  # other free device shouldn't be selected

    def test_parents_update(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, parent_device, free_device,
                               [("free", free_device), ("free", self._get_free_device()), ("free", self._get_free_device())],
                               self.supported_filesystems, [])

        # partition -- only one parent
        add_dialog.devices_combo.set_active_id("partition")
        self.assertEqual(len(add_dialog.parents_store), 1)

        # lvm -- all available parents
        add_dialog.devices_combo.set_active_id("lvm")
        self.assertEqual(len(add_dialog.parents_store), 3)

    def test_parents_selection(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, parent_device, free_device,
                               [("free", free_device), ("free", self._get_free_device()), ("free", self._get_free_device())],
                               self.supported_filesystems, [])

        # partition -- only one parent, shouldn't be allowed to deselect it
        add_dialog.devices_combo.set_active_id("partition")
        add_dialog.on_cell_toggled(None, 0)
        self.assertTrue(add_dialog.parents_store[0][2])
        self.assertTrue(add_dialog.parents_store[0][3])

        # lvm -- allow secting other parents
        add_dialog.devices_combo.set_active_id("lvm")
        # it is not possible to the emmit toggle programmatically, we need to call the signal handler manually and
        # set the value in the TreeStore to True
        add_dialog.on_cell_toggled(None, 1)
        add_dialog.parents_store[1][2] = True

        self.assertTrue(add_dialog.parents_store[1][3])

        # deselect second parent
        add_dialog.parents_store[1][2] = False
        add_dialog.on_cell_toggled(None, 1)

        self.assertFalse(add_dialog.parents_store[1][3])

    def test_fs_chooser(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, parent_device, free_device,
                               [("free", free_device)], self.supported_filesystems,
                               [], True)  # with installer_mode=True

        # swap -- mountpoint entry shouldn't be visible, label entry should be visible
        add_dialog.filesystems_combo.set_active_id("swap")
        self.assertEqual(add_dialog.filesystems_combo.get_active_id(), "swap")
        self.assertFalse(add_dialog.mountpoint_entry.get_visible())
        self.assertTrue(add_dialog.label_entry.get_visible())

        # lvmpv -- both mountpoint and label entries shouldn't be visible
        add_dialog.filesystems_combo.set_active_id("lvmpv")
        self.assertEqual(add_dialog.filesystems_combo.get_active_id(), "lvmpv")
        self.assertFalse(add_dialog.mountpoint_entry.get_visible())
        self.assertFalse(add_dialog.label_entry.get_visible())

        # ext4 -- mountpoint and label entries should be visible
        add_dialog.filesystems_combo.set_active_id("ext4")
        self.assertEqual(add_dialog.filesystems_combo.get_active_id(), "ext4")
        self.assertTrue(add_dialog.mountpoint_entry.get_visible())
        self.assertTrue(add_dialog.label_entry.get_visible())

    def test_fs_chooser_biosboot(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        _filesystems = self.supported_filesystems[:]
        _filesystems.append(formats.biosboot.BIOSBoot())
        _filesystems.append(formats.fs.BTRFS())

        add_dialog = AddDialog(self.parent_window, parent_device, free_device,
                               [("free", free_device)], _filesystems,
                               [], True)  # with installer_mode=True

        # switch from biosboot to btrfs and ext4 (rhbz#1881472)
        add_dialog.filesystems_combo.set_active_id("biosboot")
        self.assertEqual(add_dialog.filesystems_combo.get_active_id(), "biosboot")
        add_dialog.filesystems_combo.set_active_id("btrfs")
        self.assertEqual(add_dialog.filesystems_combo.get_active_id(), "btrfs")
        add_dialog.filesystems_combo.set_active_id("biosboot")
        self.assertEqual(add_dialog.filesystems_combo.get_active_id(), "biosboot")
        add_dialog.filesystems_combo.set_active_id("ext4")
        self.assertEqual(add_dialog.filesystems_combo.get_active_id(), "ext4")

    def test_md_type(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, parent_device, free_device,
                               [("free", free_device), ("free", self._get_free_device())],
                               self.supported_filesystems, [])

        add_dialog.devices_combo.set_active_id("mdraid")

        # select partition --> filesystem chooser should be visible
        add_dialog.md_type_combo.set_active_id("partition")
        self.assertTrue(add_dialog.filesystems_combo.get_visible())

    def test_raid_type(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device, size=Size("8 GiB"))

        add_dialog = AddDialog(self.parent_window, parent_device, free_device,
                               [("free", free_device), ("free", self._get_free_device(size=Size("4 GiB")))],
                               self.supported_filesystems, [])

        add_dialog.devices_combo.set_active_id("mdraid")

        self.assertEqual(len(add_dialog.parents_store), 2)
        # select second parent --> raid combo should be visible
        add_dialog.on_cell_toggled(None, 1)
        add_dialog.parents_store[1][2] = True
        self.assertTrue(add_dialog._raid_chooser.get_visible())
        self.assertEqual(add_dialog._raid_chooser.selected_level.name, "raid0")  # linear is default value for mdraid

        # raid0 type is selected --> we should have 2 size areas, both with max size 4 GiB (smaller free space size)
        self.assertEqual(add_dialog.size_area.max_size, Size("8 GiB"))

        # raid0 is selected --> advanced options (chunk size) should be visible
        self.assertIsNotNone(add_dialog.advanced)

        # select raid1 --> advanced options (chunk size) should be disappear
        add_dialog._raid_chooser.selected_level = raid.RAID1
        self.assertIsNone(add_dialog.advanced)

        # back to raid0 just to be sure
        add_dialog._raid_chooser.selected_level = raid.RAID0
        self.assertIsNotNone(add_dialog.advanced)

    @patch("blivetgui.dialogs.message_dialogs.ErrorDialog", error_dialog)
    def test_mountpoint_validity_check(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, parent_device, free_device,
                               [("free", free_device)], self.supported_filesystems, ["/root"], True)

        # reset mock
        self.error_dialog.reset_mock()

        # valid mountpoint
        add_dialog.mountpoint_entry.set_text("/home")
        add_dialog.validate_user_input()
        self.assertFalse(self.error_dialog.called)  # passphrase specified --> no error
        self.error_dialog.reset_mock()

        # invalid mountpoint
        mnt = "home"
        add_dialog.mountpoint_entry.set_text(mnt)
        add_dialog.validate_user_input()
        self.error_dialog.assert_any_call(add_dialog, _("\"{0}\" is not a valid mountpoint.").format(mnt), False)
        self.error_dialog.reset_mock()

        # duplicate mountpoint
        mnt = "/root"
        add_dialog.mountpoint_entry.set_text(mnt)
        add_dialog.validate_user_input()
        self.error_dialog.assert_any_call(add_dialog, _("Selected mountpoint \"{0}\" is already set for another device.").format(mnt), False)
        self.error_dialog.reset_mock()

    @patch("blivetgui.dialogs.message_dialogs.ErrorDialog", error_dialog)
    def test_name_validity_check(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, parent_device, free_device,
                               [("free", free_device)], self.supported_filesystems, [])

        add_dialog.devices_combo.set_active_id("lvm")  # select device type that has a name option

        # valid name
        name = "aaaaa"
        add_dialog.name_entry.set_text(name)
        add_dialog.validate_user_input()
        self.assertFalse(self.error_dialog.called)  # passphrase specified --> no error
        self.error_dialog.reset_mock()

        # invalid name
        name = "?*#%@"
        add_dialog.name_entry.set_text(name)
        add_dialog.validate_user_input()
        self.error_dialog.assert_any_call(add_dialog, _("\"{0}\" is not a valid name.").format(name), True)
        self.error_dialog.reset_mock()

    @patch("blivetgui.dialogs.message_dialogs.ErrorDialog", error_dialog)
    def test_label_validity_check(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, parent_device, free_device,
                               [("free", free_device)], self.supported_filesystems, [])

        add_dialog.devices_combo.set_active_id("partition")  # select device type that has a label option
        add_dialog.filesystems_combo.set_active_id("ext4")

        # valid label for ext4
        label = "a" * 5
        add_dialog.label_entry.set_text(label)
        add_dialog.validate_user_input()
        self.assertFalse(self.error_dialog.called)  # passphrase specified --> no error
        self.error_dialog.reset_mock()

        # invalid label for ext4
        label = "a" * 50
        add_dialog.label_entry.set_text(label)
        add_dialog.validate_user_input()
        self.error_dialog.assert_any_call(add_dialog, _("\"{0}\" is not a valid label.").format(label), True)
        self.error_dialog.reset_mock()

    def test_partition_selection(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, parent_device, free_device,
                               [("free", free_device)], self.supported_filesystems, [], True)

        fstype = next((fs.type for fs in supported_filesystems()), None)
        if fstype is None:
            self.skipTest("No supported filesystems found.")

        label = "label"
        size = Size("1 GiB")
        mountpoint = "/home"
        password = "password"

        add_dialog.devices_combo.set_active_id("partition")
        add_dialog.filesystems_combo.set_active_id(fstype)
        add_dialog.size_area.main_chooser.selected_size = size
        add_dialog.label_entry.set_text(label)
        add_dialog.mountpoint_entry.set_text(mountpoint)
        add_dialog._encryption_chooser.encrypt = True
        add_dialog._encryption_chooser._passphrase_entry.set_text(password)

        selection = add_dialog.get_selection()

        self.assertEqual(selection.device_type, "partition")
        self.assertEqual(selection.size_selection.total_size, size)
        self.assertEqual(selection.filesystem, fstype)
        self.assertTrue(selection.name in (None, ""))
        self.assertEqual(selection.label, label)
        self.assertEqual(selection.mountpoint, mountpoint)
        self.assertTrue(selection.encrypt)
        self.assertEqual(selection.passphrase, password)
        self.assertEqual(selection.encryption_sector_size, 0)
        self.assertEqual(selection.size_selection.parents[0].parent_device, parent_device)
        self.assertEqual(selection.size_selection.parents[0].selected_size, size)
        self.assertIsNone(selection.raid_level)

    def test_lvm_selection(self):
        parent_device1 = self._get_parent_device()
        parent_device2 = self._get_parent_device()
        free_device1 = self._get_free_device(parent=parent_device1)
        free_device2 = self._get_free_device(parent=parent_device2)

        add_dialog = AddDialog(self.parent_window, parent_device1, free_device1,
                               [("free", free_device1), ("free", free_device2)],
                               self.supported_filesystems, [], True)

        name = "name"
        size1 = Size("4 GiB")
        size2 = Size("6 GiB")

        add_dialog.devices_combo.set_active_id("lvm")

        # select second free space
        add_dialog.on_cell_toggled(None, 1)
        add_dialog.parents_store[1][2] = True

        add_dialog.size_area.main_chooser.selected_size = size1 + size2

        add_dialog.name_entry.set_text(name)

        selection = add_dialog.get_selection()

        self.assertEqual(selection.device_type, "lvm")
        self.assertEqual(selection.size_selection.total_size, size1 + size2)
        self.assertEqual(selection.filesystem, None)
        self.assertEqual(selection.name, name)
        self.assertTrue(selection.label in (None, ""))
        self.assertTrue(selection.mountpoint in (None, ""))
        self.assertFalse(selection.encrypt)
        self.assertTrue(selection.passphrase in (None, ""))
        self.assertIsNone(selection.raid_level)

    def test_md_selection(self):
        parent_device1 = self._get_parent_device()
        parent_device2 = self._get_parent_device()
        free_device1 = self._get_free_device(parent=parent_device1)
        free_device2 = self._get_free_device(parent=parent_device2)

        add_dialog = AddDialog(self.parent_window, parent_device1, free_device1,
                               [("free", free_device1), ("free", free_device2)],
                               self.supported_filesystems, [], True)

        fstype = next((fs.type for fs in supported_filesystems()), None)
        if fstype is None:
            self.skipTest("No supported filesystems found.")

        raidtype = "raid0"
        size = Size("4 GiB")
        name = "name"

        add_dialog.devices_combo.set_active_id("mdraid")

        # select second free space
        add_dialog.on_cell_toggled(None, 1)
        add_dialog.parents_store[1][2] = True

        add_dialog._raid_chooser._combobox_raid.set_active_id(raidtype)

        # raid 0 --> second size area should be updated
        add_dialog.size_area._parent_area.choosers[0].selected_size = size

        add_dialog.name_entry.set_text(name)

        add_dialog.md_type_combo.set_active_id("partition")
        add_dialog.filesystems_combo.set_active_id(fstype)

        selection = add_dialog.get_selection()

        self.assertEqual(selection.device_type, "mdraid")
        self.assertEqual(selection.size_selection.total_size, 2 * size)
        self.assertEqual(selection.filesystem, fstype)
        self.assertEqual(selection.name, name)
        self.assertTrue(selection.label in (None, ""))
        self.assertTrue(selection.mountpoint in (None, ""))
        self.assertFalse(selection.encrypt)
        self.assertTrue(selection.passphrase in (None, ""))
        self.assertEqual(selection.size_selection.parents[0].parent_device, parent_device1)
        self.assertEqual(selection.size_selection.parents[0].selected_size, size)
        self.assertEqual(selection.size_selection.parents[1].parent_device, parent_device2)
        self.assertEqual(selection.size_selection.parents[1].selected_size, size)
        self.assertEqual(selection.raid_level, raidtype)

    def test_btrfs_selection(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device, size=Size("8 GiB"), is_free_region=False,
                                            is_empty_disk=True)

        add_dialog = AddDialog(self.parent_window, parent_device, free_device,
                               [("free", free_device)], self.supported_filesystems, [])

        add_dialog.devices_combo.set_active_id("btrfs volume")

        name = "name"

        add_dialog.name_entry.set_text(name)

        selection = add_dialog.get_selection()

        self.assertEqual(selection.device_type, "btrfs volume")
        self.assertEqual(selection.size_selection.total_size, free_device.size)
        self.assertTrue(selection.filesystem in (None, ""))
        self.assertEqual(selection.name, name)
        self.assertTrue(selection.label in (None, ""))
        self.assertTrue(selection.mountpoint in (None, ""))
        self.assertFalse(selection.encrypt)
        self.assertTrue(selection.passphrase in (None, ""))
        self.assertEqual(selection.size_selection.parents[0].parent_device, parent_device)
        self.assertEqual(selection.size_selection.parents[0].selected_size, free_device.size)
        self.assertEqual(selection.raid_level, "single")

    def test_parents_max_size_limit(self):
        parent_device1 = self._get_parent_device(size=Size("8 TiB"))
        free_device1 = self._get_free_device(parent=parent_device1, size=parent_device1.size)

        # simple case -- partition
        add_dialog = AddDialog(self.parent_window, parent_device1, free_device1,
                               [("free", free_device1)], self.supported_filesystems, [], True)

        add_dialog.devices_combo.set_active_id("partition")
        # select "unformatted" just to be sure there is no filesystem size limit
        add_dialog.filesystems_combo.set_active_id("unformatted")

        # partition max size should me limited to disklabel max size limit
        limit = parent_device1.format.parted_disk.maxPartitionLength * parent_device1.format.sector_size
        self.assertEqual(add_dialog.size_area.main_chooser.max_size, limit)

        # more complicated case -- LVM with two parents
        parent_device2 = self._get_parent_device(size=Size("1 GiB"))
        free_device2 = self._get_free_device(parent=parent_device2, size=parent_device2.size)

        add_dialog = AddDialog(self.parent_window, parent_device1, free_device1,
                               [("free", free_device1), ("free", free_device2)],
                               self.supported_filesystems, [], True)

        add_dialog.devices_combo.set_active_id("lvm")
        # select "unformatted" just to be sure there is no filesystem size limit
        add_dialog.filesystems_combo.set_active_id("unformatted")

        # select second free space
        add_dialog.on_cell_toggled(None, 1)
        add_dialog.parents_store[1][2] = True

        # LVM limit should be disklabel limit (from first parent) + 1 GiB (from second parent)
        limit = free_device2.size + parent_device1.format.parted_disk.maxPartitionLength * parent_device1.format.sector_size
        self.assertEqual(add_dialog.size_area.main_chooser.max_size, limit)


if __name__ == "__main__":
    unittest.main()
