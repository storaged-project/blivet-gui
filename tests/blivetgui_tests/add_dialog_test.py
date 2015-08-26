# -*- coding: utf-8 -*-

import unittest
from unittest.mock import Mock, MagicMock, patch

from blivetgui.dialogs.size_chooser import SizeChooserArea, SUPPORTED_UNITS
from blivetgui.dialogs.add_dialog import AdvancedOptions, AddDialog

import os

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk

from blivet.size import Size

@unittest.skipUnless("DISPLAY" in os.environ.keys(), "requires X server")
class SizeChooserAreaTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.size_area = SizeChooserArea(dialog_type="add", device_name="sda", max_size=Size("100 GiB"),
                                        min_size=Size("1 MiB"), update_clbk=lambda x: None)

    def test_unit_change(self):
        original_size = self.size_area.get_selected_size()

        for idx, unit in enumerate(SUPPORTED_UNITS):
            self.size_area.unit_chooser.set_active(idx)
            self.assertEqual(unit, self.size_area.selected_unit)

            new_size = Size(str(self.size_area.spin_size.get_value()) + " " + unit)
            self.assertEqual(original_size, new_size)

    def test_scale_spin(self):
        old_value = self.size_area.scale.get_value()
        new_value = old_value // 2

        self.size_area.scale.set_value(new_value)
        self.assertEqual(new_value, self.size_area.spin_size.get_value())

        self.size_area.spin_size.set_value(old_value)
        self.assertEqual(old_value, self.size_area.scale.get_value())

    def test_get_size(self):
        selected_size = Size(str(self.size_area.spin_size.get_value()) + " " + self.size_area.selected_unit)
        self.assertEqual(selected_size, self.size_area.get_selected_size())

    def test_set_size(self):
        selected_size = (self.size_area.max_size - self.size_area.min_size) // 2
        self.size_area.set_selected_size(selected_size)
        self.assertEqual(selected_size, self.size_area.get_selected_size())

    def test_widget_status(self):
        self.size_area.hide()
        for widget in self.size_area.widgets:
            self.assertFalse(widget.get_visible())

        self.size_area.show()
        for widget in self.size_area.widgets:
            self.assertTrue(widget.get_visible())

        self.size_area.set_sensitive(False)
        for widget in self.size_area.widgets:
            self.assertFalse(widget.get_sensitive())

        self.size_area.set_sensitive(True)
        for widget in self.size_area.widgets:
            self.assertTrue(widget.get_sensitive())

@unittest.skipUnless("DISPLAY" in os.environ.keys(), "requires X server")
class AdvancedOptionsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.add_dialog = Mock(show_widgets=Mock(return_value=True), hide_widgets=Mock(return_value=True))

    def test_lvm_options(self):
        # test lvm options are displayed for lvm/lvmvg type
        parent_device = Mock(type="disk", format=Mock(labelType="gpt", extendedPartition=None))
        free_device = Mock(isLogical=False, size=Size("8 GiB"))

        advanced_options = AdvancedOptions(add_dialog=self.add_dialog, device_type="lvm",
            parent_device=parent_device, free_device=free_device)

        self.assertFalse(hasattr(advanced_options, "partition_combo"))
        self.assertTrue(hasattr(advanced_options, "pesize_combo"))

        advanced_options = AdvancedOptions(add_dialog=self.add_dialog, device_type="lvmvg",
            parent_device=parent_device, free_device=free_device)

        self.assertFalse(hasattr(advanced_options, "partition_combo"))
        self.assertTrue(hasattr(advanced_options, "pesize_combo"))

    def test_allowed_pesize(self):
        # test allowed pesize options based on free space available
        parent_device = Mock(type="disk", format=Mock(labelType="gpt", extendedPartition=None))

        # only 8 MiB free space, allow only 2 and 4 MiB PE Size
        free_device = Mock(isLogical=False, size=Size("8 MiB"))
        advanced_options = AdvancedOptions(add_dialog=self.add_dialog, device_type="lvm",
            parent_device=parent_device, free_device=free_device)

        pesizes = [i[0] for i in advanced_options.pesize_combo.get_model()]
        self.assertEqual(["2 MiB", "4 MiB"], pesizes)

        # enough free space, allow up to 64 MiB PE Size
        free_device = Mock(isLogical=False, size=Size("1 GiB"))
        advanced_options = AdvancedOptions(add_dialog=self.add_dialog, device_type="lvm",
            parent_device=parent_device, free_device=free_device)

        pesizes = [i[0] for i in advanced_options.pesize_combo.get_model()]
        self.assertEqual(["2 MiB", "4 MiB", "8 MiB", "16 MiB", "32 MiB", "64 MiB"], pesizes)

    def test_partition_options(self):
        # test partition options are displayed for partition type

        parent_device = Mock(type="disk", format=Mock(labelType="msdos", extendedPartition=None))
        free_device = Mock(isLogical=False)

        advanced_options = AdvancedOptions(add_dialog=self.add_dialog, device_type="partition",
            parent_device=parent_device, free_device=free_device)

        self.assertTrue(hasattr(advanced_options, "partition_combo"))
        self.assertFalse(hasattr(advanced_options, "pesize_combo"))

    def test_normal_partition(self):
        # "standard" situation -- disk with msdos part table, no existing extended partition
        # → both "primary and extended" types should be allowed

        parent_device = Mock(type="disk", format=Mock(labelType="msdos", extendedPartition=None))
        free_device = Mock(isLogical=False)

        advanced_options = AdvancedOptions(add_dialog=self.add_dialog, device_type="partition",
            parent_device=parent_device, free_device=free_device)

        part_types = advanced_options.partition_combo.get_model()

        self.assertEqual(len(part_types), 2)
        self.assertEqual(part_types[0][1], "primary")
        self.assertEqual(part_types[1][1], "extended")

    def test_logical_partition(self):
        # adding partition to free space inside extended partition -> only "logical allowed"

        parent_device = Mock(type="disk", format=Mock(labelType="msdos", extendedPartition=Mock()))
        free_device = Mock(isLogical=True)

        advanced_options = AdvancedOptions(add_dialog=self.add_dialog, device_type="partition",
            parent_device=parent_device, free_device=free_device)

        part_types = advanced_options.partition_combo.get_model()

        self.assertEqual(len(part_types), 1)
        self.assertEqual(part_types[0][1], "logical")

    def test_extended_partition(self):
        # extended partition already exists -> allow only "primary" type

        parent_device = Mock(type="disk", format=Mock(labelType="msdos", extendedPartition=Mock()))
        free_device = Mock(isLogical=False)

        advanced_options = AdvancedOptions(add_dialog=self.add_dialog, device_type="partition",
            parent_device=parent_device, free_device=free_device)

        part_types = advanced_options.partition_combo.get_model()

        self.assertEqual(len(part_types), 1)
        self.assertEqual(part_types[0][1], "primary")

    def test_gpt_partitions(self):
        # adding partition on gpt disk -> only "primary" type allowed
        parent_device = Mock(type="disk", format=Mock(labelType="gpt", extendedPartition=None))
        free_device = Mock(isLogical=False)

        advanced_options = AdvancedOptions(add_dialog=self.add_dialog, device_type="partition",
            parent_device=parent_device, free_device=free_device)

        part_types = advanced_options.partition_combo.get_model()

        self.assertEqual(len(part_types), 1)
        self.assertEqual(part_types[0][1], "primary")

@unittest.skipUnless("DISPLAY" in os.environ.keys(), "requires X server")
class AddDialogTest(unittest.TestCase):

    error_dialog = MagicMock()

    @classmethod
    def setUpClass(cls):
        cls.parent_window = MagicMock(spec=Gtk.Window)
        cls.supported_fs = ["ext4", "xfs", "swap"]

    @property
    def supported_raids(self):
        single = MagicMock()
        single.configure_mock(name="single", min_members=1)
        linear = MagicMock()
        linear.configure_mock(name="linear", min_members=1)
        raid0 = MagicMock()
        raid0.configure_mock(name="raid0", min_members=2)
        raid1 = MagicMock()
        raid1.configure_mock(name="raid1", min_members=2)
        raid5 = MagicMock()
        raid5.configure_mock(name="raid5", min_members=3)

        return {"btrfs volume" : (single, raid0, raid1), "mdraid" : (linear, raid0, raid1)}

    def _get_free_device(self, size=Size("8 GiB"), logical=False, parent=None, region=True):
        if not parent:
            parent = MagicMock()
            parent.configure_mock(name="vda", size=size, type="disk")

        return MagicMock(type="free_space", size=size, isLogical=logical, parents=[parent], isFreeRegion=region,
                         isUninitializedDisk=not region)

    def _get_parent_device(self, name=None, dtype="disk", size=Size("8 GiB"), ftype="disklabel"):
        if not name:
            if dtype == "disk":
                name = "vda"
            else:
                name = "fedora"

        dev = MagicMock()
        dev.configure_mock(name=name, type=dtype, size=size, format=MagicMock(type=ftype))

        return dev

    @patch("blivetgui.dialogs.add_dialog.AddDialog.set_transient_for", lambda dialog, window: True)
    def test_allowed_device_types(self):
        # disk with disklabel and enough free space, other disks available
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, "disk", parent_device, free_device, [],
                               [free_device, self._get_free_device()], self.supported_raids, self.supported_fs, [])

        types = sorted([i[1] for i in add_dialog.devices_combo.get_model()])

        self.assertTrue(sorted(["partition", "lvm", "lvmpv", "btrfs volume", "mdraid"]) == types)
        self.assertTrue(add_dialog.devices_combo.get_sensitive())

        # disk with disklabel and not enough free space, no other disks available
        parent_device = self._get_parent_device(size=Size("200 MiB"))
        free_device = self._get_free_device(size=parent_device.size, parent=parent_device)

        add_dialog = AddDialog(self.parent_window, "disk", parent_device, free_device, [],
                               [free_device], self.supported_raids, self.supported_fs, [])

        types = sorted([i[1] for i in add_dialog.devices_combo.get_model()])

        self.assertTrue(sorted(["partition", "lvm", "lvmpv"]) == types)
        self.assertTrue(add_dialog.devices_combo.get_sensitive())

        # lvmpv
        parent_device = self._get_parent_device(dtype="lvmpv", ftype=None)
        free_device = parent_device

        add_dialog = AddDialog(self.parent_window, "lvmpv", parent_device, free_device, [],
                               [free_device], self.supported_raids, self.supported_fs, [])

        types = sorted([i[1] for i in add_dialog.devices_combo.get_model()])

        self.assertTrue(sorted(["lvmvg"]) == types)
        self.assertFalse(add_dialog.devices_combo.get_sensitive())

        # btrfs as partition table
        parent_device = self._get_parent_device(dtype="disk", ftype=None)
        free_device = self._get_free_device(size=parent_device.size, parent=parent_device)

        add_dialog = AddDialog(self.parent_window, "disk", parent_device, free_device, [],
                               [free_device], self.supported_raids, self.supported_fs, [])

        types = sorted([i[1] for i in add_dialog.devices_combo.get_model()])

        self.assertTrue(sorted(["btrfs volume"]) == types)
        self.assertFalse(add_dialog.devices_combo.get_sensitive())

    @patch("blivetgui.dialogs.add_dialog.AddDialog.set_transient_for", lambda dialog, window: True)
    def test_partition_widgets(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, "disk", parent_device, free_device, [],
                               [free_device], self.supported_raids, self.supported_fs, [])

        add_dialog.devices_combo.set_active_id("partition")
        self.assertEqual(add_dialog._get_selected_device_type(), "partition")

        self.assertIsNone(add_dialog.free_type_chooser)
        self.assertTrue(add_dialog.filesystems_combo.get_visible())
        self.assertFalse(add_dialog.name_entry.get_visible())
        self.assertTrue(add_dialog.encrypt_check.get_visible())
        self.assertFalse(add_dialog.raid_combo.get_visible())
        self.assertTrue(len(add_dialog.size_areas) == 1)
        self.assertIsNotNone(add_dialog.advanced)
        self.assertFalse(add_dialog.md_type_combo.get_visible())

    @patch("blivetgui.dialogs.add_dialog.AddDialog.set_transient_for", lambda dialog, window: True)
    def test_lvm_widgets(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, "disk", parent_device, free_device, [],
                               [free_device], self.supported_raids, self.supported_fs, [])

        add_dialog.devices_combo.set_active_id("lvm")
        self.assertEqual(add_dialog._get_selected_device_type(), "lvm")

        self.assertIsNone(add_dialog.free_type_chooser)
        self.assertFalse(add_dialog.filesystems_combo.get_visible())
        self.assertTrue(add_dialog.name_entry.get_visible())
        self.assertTrue(add_dialog.encrypt_check.get_visible())
        self.assertFalse(add_dialog.raid_combo.get_visible())
        self.assertTrue(len(add_dialog.size_areas) == 1)
        self.assertIsNotNone(add_dialog.advanced)
        self.assertFalse(add_dialog.md_type_combo.get_visible())

    @patch("blivetgui.dialogs.add_dialog.AddDialog.set_transient_for", lambda dialog, window: True)
    def test_lvmpv_widgets(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, "disk", parent_device, free_device, [],
                               [free_device], self.supported_raids, self.supported_fs, [])

        add_dialog.devices_combo.set_active_id("lvmpv")
        self.assertEqual(add_dialog._get_selected_device_type(), "lvmpv")

        self.assertIsNone(add_dialog.free_type_chooser)
        self.assertFalse(add_dialog.filesystems_combo.get_visible())
        self.assertFalse(add_dialog.name_entry.get_visible())
        self.assertTrue(add_dialog.encrypt_check.get_visible())
        self.assertFalse(add_dialog.raid_combo.get_visible())
        self.assertTrue(len(add_dialog.size_areas) == 1)
        self.assertIsNone(add_dialog.advanced)
        self.assertFalse(add_dialog.md_type_combo.get_visible())

    @patch("blivetgui.dialogs.add_dialog.AddDialog.set_transient_for", lambda dialog, window: True)
    def test_btrfsvolume_widgets(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, "disk", parent_device, free_device, [],
                               [free_device], self.supported_raids, self.supported_fs, [])

        add_dialog.devices_combo.set_active_id("btrfs volume")
        self.assertEqual(add_dialog._get_selected_device_type(), "btrfs volume")

        self.assertIsNotNone(add_dialog.free_type_chooser)
        self.assertFalse(add_dialog.filesystems_combo.get_visible())
        self.assertTrue(add_dialog.name_entry.get_visible())
        self.assertFalse(add_dialog.encrypt_check.get_visible())
        self.assertFalse(add_dialog.raid_combo.get_visible())
        self.assertTrue(len(add_dialog.size_areas) == 1)
        self.assertIsNone(add_dialog.advanced)
        self.assertFalse(add_dialog.md_type_combo.get_visible())

    @patch("blivetgui.dialogs.add_dialog.AddDialog.set_transient_for", lambda dialog, window: True)
    def test_mdraid_widgets(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, "disk", parent_device, free_device, [],
                               [free_device, self._get_free_device()], self.supported_raids, self.supported_fs, [])

        add_dialog.devices_combo.set_active_id("mdraid")
        self.assertEqual(add_dialog._get_selected_device_type(), "mdraid")

        self.assertIsNone(add_dialog.free_type_chooser)
        self.assertTrue(add_dialog.filesystems_combo.get_visible())
        self.assertTrue(add_dialog.name_entry.get_visible())
        self.assertFalse(add_dialog.encrypt_check.get_visible())
        self.assertFalse(add_dialog.raid_combo.get_visible())
        self.assertTrue(len(add_dialog.size_areas) == 1)
        self.assertIsNone(add_dialog.advanced)
        self.assertTrue(add_dialog.md_type_combo.get_visible())

    @patch("blivetgui.dialogs.add_dialog.AddDialog.set_transient_for", lambda dialog, window: True)
    def test_partition_parents(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, "disk", parent_device, free_device, [],
                               [free_device, self._get_free_device(), self._get_free_device()],
                               self.supported_raids, self.supported_fs, [])
        add_dialog.devices_combo.set_active_id("partition")

        # partition allows only one parent -- make sure we have the right one and it is selected
        self.assertEqual(len(add_dialog.parents_store), 1)
        self.assertEqual(add_dialog.parents_store[0][0], parent_device)
        self.assertEqual(add_dialog.parents_store[0][1], free_device)
        self.assertTrue(add_dialog.parents_store[0][2])
        self.assertTrue(add_dialog.parents_store[0][3])
        self.assertEqual(add_dialog.parents_store[0][5], "disk")

    @patch("blivetgui.dialogs.add_dialog.AddDialog.set_transient_for", lambda dialog, window: True)
    def test_lvm_parents(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, "disk", parent_device, free_device, [],
                               [free_device, self._get_free_device(), self._get_free_device()],
                               self.supported_raids, self.supported_fs, [])
        add_dialog.devices_combo.set_active_id("lvm")

        # lvm allows multiple parents -- make sure we have all available and the right one is selected
        self.assertEqual(len(add_dialog.parents_store), 3)
        self.assertEqual(add_dialog.parents_store[0][0], parent_device)
        self.assertEqual(add_dialog.parents_store[0][1], free_device)
        self.assertTrue(add_dialog.parents_store[0][2])
        self.assertFalse(add_dialog.parents_store[1][2]) # other two free devices shouldn't be selected
        self.assertFalse(add_dialog.parents_store[2][2])

    @patch("blivetgui.dialogs.add_dialog.AddDialog.set_transient_for", lambda dialog, window: True)
    def test_parents_update(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, "disk", parent_device, free_device, [],
                               [free_device, self._get_free_device(), self._get_free_device()],
                               self.supported_raids, self.supported_fs, [])

        # partition -- only one parent
        add_dialog.devices_combo.set_active_id("partition")
        self.assertEqual(len(add_dialog.parents_store), 1)

        # lvm -- all available parents
        add_dialog.devices_combo.set_active_id("lvm")
        self.assertEqual(len(add_dialog.parents_store), 3)

    @patch("blivetgui.dialogs.add_dialog.AddDialog.set_transient_for", lambda dialog, window: True)
    def test_parents_selection(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, "disk", parent_device, free_device, [],
                               [free_device, self._get_free_device(), self._get_free_device()],
                               self.supported_raids, self.supported_fs, [])

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
        self.assertEqual(len(add_dialog.size_areas), 2) # two parents --> two size areas

        # deselect second parent
        add_dialog.parents_store[1][2] = False
        add_dialog.on_cell_toggled(None, 1)

        self.assertFalse(add_dialog.parents_store[1][3])
        self.assertEqual(len(add_dialog.size_areas), 1) # only one size area again

    @patch("blivetgui.dialogs.add_dialog.AddDialog.set_transient_for", lambda dialog, window: True)
    def test_fs_chooser(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, "disk", parent_device, free_device, [],
                               [free_device], self.supported_raids, self.supported_fs, [], True) # with kickstart_mode=True

        # we have all supported fs in the combo
        self.assertEqual(len(add_dialog.filesystems_combo.get_model()), len(self.supported_fs))

        # swap -- mountpoint and label entries shouldn't be visible
        add_dialog.filesystems_combo.set_active(self.supported_fs.index("swap"))
        self.assertEqual(add_dialog.filesystems_combo.get_active_text(), "swap")
        self.assertFalse(add_dialog.mountpoint_entry.get_visible())
        self.assertFalse(add_dialog.label_entry.get_visible())

        # ext4 -- mountpoint and label entries should be visible
        add_dialog.filesystems_combo.set_active(self.supported_fs.index("ext4"))
        self.assertEqual(add_dialog.filesystems_combo.get_active_text(), "ext4")
        self.assertTrue(add_dialog.mountpoint_entry.get_visible())
        self.assertTrue(add_dialog.label_entry.get_visible())

    @patch("blivetgui.dialogs.add_dialog.AddDialog.set_transient_for", lambda dialog, window: True)
    def test_encrypt_check(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, "disk", parent_device, free_device, [],
                               [free_device], self.supported_raids, self.supported_fs, [])

        min_size = add_dialog.size_areas[0][0].min_size # device minimal size before update
        # check the encrypt check, passphrase entry should be visible and 2 MiB should be added to device min size
        add_dialog.encrypt_check.set_active(True)
        self.assertTrue(add_dialog.pass_entry.get_visible())
        self.assertEqual(add_dialog.size_areas[0][0].min_size, min_size + Size("2 MiB"))

        # check the encrypt check, passphrase entry should be hidden and min size should be back to original min size
        add_dialog.encrypt_check.set_active(False)
        self.assertFalse(add_dialog.pass_entry.get_visible())
        self.assertEqual(add_dialog.size_areas[0][0].min_size, min_size)

    @patch("blivetgui.dialogs.add_dialog.AddDialog.set_transient_for", lambda dialog, window: True)
    def test_md_type(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, "disk", parent_device, free_device, [],
                               [free_device, self._get_free_device()], self.supported_raids, self.supported_fs, [])

        add_dialog.devices_combo.set_active_id("mdraid")

        # mdraid -- raid type combo should be visible
        self.assertTrue(add_dialog.md_type_combo.get_visible())

        # select partition --> filesystem chooser should be visible
        add_dialog.md_type_combo.set_active_id("partition")
        self.assertTrue(add_dialog.filesystems_combo.get_visible())
        # select lvmpv --> filesystem chooser should be hidden
        add_dialog.md_type_combo.set_active_id("lvmpv")
        self.assertFalse(add_dialog.filesystems_combo.get_visible())

    @patch("blivetgui.dialogs.add_dialog.AddDialog.set_transient_for", lambda dialog, window: True)
    def test_raid_type(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device, size=Size("8 GiB"))

        add_dialog = AddDialog(self.parent_window, "disk", parent_device, free_device, [],
                               [free_device, self._get_free_device(size=Size("4 GiB"))], self.supported_raids,
                               self.supported_fs, [])

        add_dialog.devices_combo.set_active_id("mdraid")
        # select second parent --> raid combo should be visible
        add_dialog.on_cell_toggled(None, 1)
        add_dialog.parents_store[1][2] = True
        self.assertTrue(add_dialog.raid_combo.get_visible())
        self.assertEqual(add_dialog.raid_combo.get_active_id(), "linear") # linear is default value for mdraid

        # only 2 parents --> only "linear", "raid1" and "raid0" should be available; "raid5" needs at least 3 parents
        # set_active_id returns True or False based on success --> it should return False for "raid5" and True otherwise
        self.assertTrue(add_dialog.raid_combo.set_active_id("raid0"))
        self.assertTrue(add_dialog.raid_combo.set_active_id("raid1"))
        self.assertFalse(add_dialog.raid_combo.set_active_id("raid5"))

        # raid1 type is selected --> we should have 2 size areas, both with max size 4 GiB (smaller free space size)
        self.assertEqual(len(add_dialog.size_areas), 2)
        self.assertEqual(add_dialog.size_areas[0][0].max_size, Size("4 GiB"))
        self.assertEqual(add_dialog.size_areas[1][0].max_size, Size("4 GiB"))

    @patch("blivetgui.dialogs.add_dialog.AddDialog.set_transient_for", lambda dialog, window: True)
    @patch("blivetgui.dialogs.message_dialogs.ErrorDialog", error_dialog)
    def test_encrypt_validity_check(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, "disk", parent_device, free_device, [],
                               [free_device], self.supported_raids, self.supported_fs, [])

        # passphrase specified
        add_dialog.encrypt_check.set_active(True)
        add_dialog.pass_entry.set_text("aaaaa")
        add_dialog.validate_user_input()
        self.assertFalse(self.error_dialog.called) # passphrase specified --> no error
        self.error_dialog.reset_mock()

        # no passphrase specified
        add_dialog.encrypt_check.set_active(True)
        add_dialog.pass_entry.set_text("")
        add_dialog.validate_user_input()
        self.error_dialog.assert_any_call(add_dialog, "Passphrase not specified.")
        self.error_dialog.reset_mock()

    @patch("blivetgui.dialogs.add_dialog.AddDialog.set_transient_for", lambda dialog, window: True)
    @patch("blivetgui.dialogs.message_dialogs.ErrorDialog", error_dialog)
    def test_mountpoint_validity_check(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, "disk", parent_device, free_device, [],
                               [free_device], self.supported_raids, self.supported_fs, [], True)

        # valid mountpoint
        add_dialog.mountpoint_entry.set_text("/home")
        add_dialog.validate_user_input()
        self.assertFalse(self.error_dialog.called) # passphrase specified --> no error
        self.error_dialog.reset_mock()

        # invalid mountpoint
        mnt = "home"
        add_dialog.mountpoint_entry.set_text(mnt)
        add_dialog.validate_user_input()
        add_dialog.validate_user_input()
        self.error_dialog.assert_any_call(add_dialog, "\"%s\" is not a valid mountpoint." % mnt)
        self.error_dialog.reset_mock()

        # duplicate mountpoint -- FIXME: need to fix mountpoint duplicate check first, see dialogs/hepers/check_mountpoint.py

    @patch("blivetgui.dialogs.add_dialog.AddDialog.set_transient_for", lambda dialog, window: True)
    @patch("blivetgui.dialogs.message_dialogs.ErrorDialog", error_dialog)
    def test_name_validity_check(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, "disk", parent_device, free_device, [],
                               [free_device], self.supported_raids, self.supported_fs, [])

        add_dialog.devices_combo.set_active_id("lvm") # select device type that has a name option

        # valid name
        name = "aaaaa"
        add_dialog.name_entry.set_text(name)
        add_dialog.validate_user_input()
        self.assertFalse(self.error_dialog.called) # passphrase specified --> no error
        self.error_dialog.reset_mock()

        # invalid name
        name = "?*#%@"
        add_dialog.name_entry.set_text(name)
        add_dialog.validate_user_input()
        self.error_dialog.assert_any_call(add_dialog, "\"%s\" is not a valid name." % name)
        self.error_dialog.reset_mock()

    @patch("blivetgui.dialogs.add_dialog.AddDialog.set_transient_for", lambda dialog, window: True)
    @patch("blivetgui.dialogs.message_dialogs.ErrorDialog", error_dialog)
    def test_label_validity_check(self):
        parent_device = self._get_parent_device()
        free_device = self._get_free_device(parent=parent_device)

        add_dialog = AddDialog(self.parent_window, "disk", parent_device, free_device, [],
                               [free_device], self.supported_raids, self.supported_fs, [])

        add_dialog.devices_combo.set_active_id("partition") # select device type that has a label option
        add_dialog.filesystems_combo.set_active_id("ext4")

        # valid label for ext4
        label = "a" * 5
        add_dialog.label_entry.set_text(label)
        add_dialog.validate_user_input()
        self.assertFalse(self.error_dialog.called) # passphrase specified --> no error
        self.error_dialog.reset_mock()

        # invalid label for ext4
        label = "a" * 50
        add_dialog.label_entry.set_text(label)
        add_dialog.validate_user_input()
        self.error_dialog.assert_any_call(add_dialog, "\"%s\" is not a valid label." % label)
        self.error_dialog.reset_mock()

if __name__ == "__main__":
    unittest.main()
