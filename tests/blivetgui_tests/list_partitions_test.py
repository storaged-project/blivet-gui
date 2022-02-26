# -*- coding: utf-8 -*-

import unittest
from unittest.mock import MagicMock

from blivet.size import Size

from blivetgui.list_partitions import ListPartitions
from blivetgui.gui_utils import locate_ui_file

import os

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk


@unittest.skipUnless("DISPLAY" in os.environ.keys(), "requires X server")
class ListPartitionsTest(unittest.TestCase):

    def setUp(self):

        _builder = Gtk.Builder()
        _builder.add_from_file(locate_ui_file("blivet-gui.ui"))

        self.blivet_gui = MagicMock(installer_mode=False, builder=_builder)

        self.list_partitions = ListPartitions(self.blivet_gui)

    def test_allow_delete(self):
        # do not allow deleting free space and non-leaf devices
        device = MagicMock(type="free space", protected=False)
        self.assertFalse(self.list_partitions._allow_delete_device(device))
        device = MagicMock(type="partition", isleaf=False, protected=False)
        self.assertFalse(self.list_partitions._allow_delete_device(device))

        # unformatted leaves can be deleted
        device = MagicMock(type="partition", isleaf=True, format=MagicMock(type=None), protected=False)
        self.assertTrue(self.list_partitions._allow_delete_device(device))
        self.assertFalse(self.list_partitions._allow_recursive_delete_device(device))

        # only non-active swap can be deleted
        device = MagicMock(type="partition", isleaf=True, format=MagicMock(type="swap", status=True), protected=False)
        self.assertFalse(self.list_partitions._allow_delete_device(device))
        device = MagicMock(type="partition", isleaf=True, format=MagicMock(type="swap", status=False), protected=False)
        self.assertTrue(self.list_partitions._allow_delete_device(device))

        # only unmounted devices can be deleted
        device = MagicMock(type="partition", isleaf=True, format=MagicMock(type="lvmpv", mountable=False), protected=False)
        self.assertTrue(self.list_partitions._allow_delete_device(device))
        device = MagicMock(type="partition", isleaf=True, format=MagicMock(type="ext4", mountable=True, status=False), protected=False)
        self.assertTrue(self.list_partitions._allow_delete_device(device))
        device = MagicMock(type="partition", isleaf=True, format=MagicMock(type="ext4", mountable=True, status=True), protected=False)
        self.assertFalse(self.list_partitions._allow_delete_device(device))

        # protected devices can't be deleteded
        device = MagicMock(type="partition", isleaf=True, protected=True)
        self.assertFalse(self.list_partitions._allow_delete_device(device))

        # devices with children (like vgs) can be deleted if children can be deleted
        lv = MagicMock(type="lvmlv", isleaf=True, format=MagicMock(type="ext4", mountable=True, status=False), protected=False)
        vg = MagicMock(type="lvmvg", isleaf=False, children=[lv], protected=False)
        self.assertFalse(self.list_partitions._allow_delete_device(vg))
        self.assertTrue(self.list_partitions._allow_recursive_delete_device(vg))

        # but of vg with mounted lv can't be deleted
        lv = MagicMock(type="lvmlv", isleaf=True, format=MagicMock(type="ext4", mountable=True, status=True), protected=False)
        vg = MagicMock(type="lvmvg", isleaf=False, children=[lv], protected=False)
        self.assertFalse(self.list_partitions._allow_delete_device(vg))
        self.assertFalse(self.list_partitions._allow_recursive_delete_device(vg))

    def test_allow_add(self):
        # do not allow adding on protected devices
        device = MagicMock(type="free space", protected=True)
        self.assertFalse(self.list_partitions._allow_add_device(device))

        # allow adding on free space and btrfs volumes
        device = MagicMock(type="free space", protected=False)
        self.assertTrue(self.list_partitions._allow_add_device(device))
        device = MagicMock(type="btrfs volume", protected=False)
        self.assertTrue(self.list_partitions._allow_add_device(device))

        # allow adding on empty lvmpv
        device = MagicMock(type="partition", protected=False, children=[], format=MagicMock(type="lvmpv"))
        self.assertTrue(self.list_partitions._allow_add_device(device))
        device = MagicMock(type="partition", protected=False, children=[MagicMock()], format=MagicMock(type="lvmpv"))
        self.assertFalse(self.list_partitions._allow_add_device(device))

        # allow adding lvm snapshots (if lv exists)
        device = MagicMock(type="lvmlv", protected=False, exists=True,
                           vg=MagicMock(free_space=Size("1 GiB"), pe_size=Size("4 MiB")))
        self.assertTrue(self.list_partitions._allow_add_device(device))
        device = MagicMock(type="lvmlv", protected=False, exists=False,
                           vg=MagicMock(free_space=Size("1 GiB"), pe_size=Size("4 MiB")))
        self.assertFalse(self.list_partitions._allow_add_device(device))

        # allow adding thin lvm snapshots (if thin lv exists)
        device = MagicMock(type="lvmthinlv", protected=False, exists=True, vg=MagicMock(free_space=Size("1 GiB"), pe_size=Size("4 MiB")))
        self.assertTrue(self.list_partitions._allow_add_device(device))
        device = MagicMock(type="lvmthinlv", protected=False, exists=False, vg=MagicMock(free_space=Size("1 GiB"), pe_size=Size("4 MiB")))
        self.assertFalse(self.list_partitions._allow_add_device(device))

        # do not allow adding on other devices
        device = MagicMock(type="mdarray", protected=False)
        self.assertFalse(self.list_partitions._allow_add_device(device))

    def test_allow_format(self):
        # do not allow to format protected devices
        device = MagicMock(type="partition", protected=True, is_extended=False, children=[],
                           format=MagicMock(type="ext4", status=False))
        self.assertFalse(self.list_partitions._allow_format_device(device))

        # do not allow to format extended partitions
        device = MagicMock(type="partition", protected=False, is_extended=True, children=[],
                           format=MagicMock(type="ext4", status=False))
        self.assertFalse(self.list_partitions._allow_format_device(device))

        # free space cannot be formatted
        device = MagicMock(type="free space", protected=False, children=[])
        self.assertFalse(self.list_partitions._allow_format_device(device))

        # devices with children cannot be resized
        device = MagicMock(type="partition", protected=False, is_extended=False, children=[MagicMock()],
                           format=MagicMock(type="ext4", status=False))
        self.assertFalse(self.list_partitions._allow_format_device(device))

        # active devices cannot be formatted
        device = MagicMock(type="partition", protected=False, is_extended=False, children=[],
                           format=MagicMock(type="ext4", status=True))
        self.assertFalse(self.list_partitions._allow_format_device(device))

        device = MagicMock(type="partition", protected=False, is_extended=False, children=[],
                           format=MagicMock(type="ext4", status=False))
        self.assertTrue(self.list_partitions._allow_format_device(device))

    def test_allow_resize(self):
        # protected devices and devices with immutable formats cannot be resized
        device = MagicMock(type="partition", protected=True, format_immutable=False, children=[], _resizable=True)
        self.assertFalse(self.list_partitions._allow_resize_device(device))
        device = MagicMock(type="partition", protected=False, format_immutable=True, children=[], _resizable=True)
        self.assertFalse(self.list_partitions._allow_resize_device(device))

        # devices with children cannot be resized
        device = MagicMock(type="partition", protected=False, format_immutable=False, children=[MagicMock()], _resizable=True)
        self.assertFalse(self.list_partitions._allow_resize_device(device))

        device = MagicMock(type="partition", protected=False, format_immutable=False, children=[], _resizable=False)
        self.assertFalse(self.list_partitions._allow_resize_device(device))

        device = MagicMock(type="partition", protected=False, format_immutable=False, children=[], _resizable=True)
        self.assertTrue(self.list_partitions._allow_resize_device(device))

    def test_allow_set_mountpoint(self):
        # not installer mode, do not allow to add
        device = MagicMock(type="partition", direct=True, format=MagicMock(type="ext4", mountable=True, status=False))
        self.assertFalse(self.list_partitions._allow_set_mountpoint(device))

        self.blivet_gui.installer_mode = True

        # same for non-existing snapshots
        device = MagicMock(type="lvmsnapshot", exists=False, direct=True,
                           format=MagicMock(type="ext4", mountable=True, status=False))
        self.assertFalse(self.list_partitions._allow_set_mountpoint(device))

        # but existing snapshots can be mounted
        device = MagicMock(type="lvmsnapshot", exists=True, direct=True,
                           format=MagicMock(type="ext4", mountable=True, status=False))
        self.assertTrue(self.list_partitions._allow_set_mountpoint(device))

        # devices that are not direct cannot be mounted
        device = MagicMock(type="partition", exists=True, direct=False,
                           format=MagicMock(type="ext4", mountable=True, status=False))
        self.assertFalse(self.list_partitions._allow_set_mountpoint(device))

        # unmountable filesystem cannot be mounted
        device = MagicMock(type="partition", exists=True, direct=True,
                           format=MagicMock(type="ext4", mountable=False, status=False))
        self.assertFalse(self.list_partitions._allow_set_mountpoint(device))

        # allow else
        device = MagicMock(type="partition", exists=True, direct=True,
                           format=MagicMock(type="ext4", mountable=True, status=False))
        self.assertTrue(self.list_partitions._allow_set_mountpoint(device))

    def test_allow_relabel(self):
        fmt = MagicMock(type="ext4", status=False)
        fmt.labeling.return_value = True
        fmt.relabels.return_value = True

        # do not allow to relabel protected devices
        device = MagicMock(type="partition", protected=True, format=fmt)
        self.assertFalse(self.list_partitions._allow_relabel_device(device))

        # do not allow to relabel active formats
        fmt.status = True
        device = MagicMock(type="partition", protected=False, format=fmt)
        self.assertFalse(self.list_partitions._allow_relabel_device(device))

        # allow if labeling and relabels
        fmt.status = False
        device = MagicMock(type="partition", protected=False, format=fmt)
        self.assertTrue(self.list_partitions._allow_relabel_device(device))

        # do not allow else
        fmt.labeling.return_value = False
        device = MagicMock(type="partition", protected=False, format=fmt)
        self.assertFalse(self.list_partitions._allow_relabel_device(device))

        fmt.labeling.return_value = True
        fmt.relabels.return_value = False
        device = MagicMock(type="partition", protected=False, format=fmt)
        self.assertFalse(self.list_partitions._allow_relabel_device(device))

    def test_allow_partition_table(self):
        # only allow on free space
        device = MagicMock(type="partition", protected=False)
        self.assertFalse(self.list_partitions._allow_set_partition_table(device))

        # always allow on unitialized disks
        device = MagicMock(type="free space", is_uninitialized_disk=True, is_empty_disk=True)
        self.assertTrue(self.list_partitions._allow_set_partition_table(device))

        # on empty disks allow if formatted with partition table
        device = MagicMock(type="free space", is_uninitialized_disk=False, is_empty_disk=True,
                           disk=MagicMock(format=MagicMock(type="disklabel")))
        self.assertTrue(self.list_partitions._allow_set_partition_table(device))
        device = MagicMock(type="free space", is_uninitialized_disk=False, is_empty_disk=True,
                           disk=MagicMock(format=MagicMock(type="ext4")))
        self.assertFalse(self.list_partitions._allow_set_partition_table(device))

    def test_add_to_store(self):

        # simple partition -- test if added to store correctly
        device = MagicMock(type="partition", size=Size("1 GiB"), path="/dev/vda1",
                           format=MagicMock(type="ext4", mountable=True, label="aaaaa"))
        device.configure_mock(name="vda1")

        mountpoints = {device.path: "/"}
        self.blivet_gui.client.remote_call.return_value = mountpoints
        it = self.list_partitions._add_to_store(device)
        self.assertEqual(self.list_partitions.partitions_list.get_value(it, 1), device.name)
        self.assertEqual(self.list_partitions.partitions_list.get_value(it, 2), device.type)
        self.assertEqual(self.list_partitions.partitions_list.get_value(it, 3), device.format.type)
        self.assertEqual(self.list_partitions.partitions_list.get_value(it, 4), str(device.size))
        self.assertEqual(self.list_partitions.partitions_list.get_value(it, 5), device.format.label)
        self.assertEqual(self.list_partitions.partitions_list.get_value(it, 6), ", ".join(mountpoints))

        # simple partition with multiple mountpoints
        mountpoints = {device.path: ["/", "/mnt"]}
        self.blivet_gui.client.remote_call.return_value = mountpoints
        self.assertEqual(self.list_partitions.partitions_list.get_value(it, 1), device.name)
        self.assertEqual(self.list_partitions.partitions_list.get_value(it, 6), ", ".join(mountpoints))

        # partition with unknown/unsupported filesystem
        fmt = MagicMock(type=None, mountable=False, label=None)
        fmt.configure_mock(name="exfat")
        device = MagicMock(type="partition", size=Size("1 GiB"), path="/dev/vda1",
                           format=fmt)
        device.configure_mock(name="vda1")
        it = self.list_partitions._add_to_store(device)
        self.assertEqual(self.list_partitions.partitions_list.get_value(it, 3), device.format.name)

        # lvmvg with long name -- name should be elipsized and type should be 'lvm'
        fmt = MagicMock(type=None, mountable=False, label=None)
        fmt.configure_mock(name="Unknown")
        device = MagicMock(type="lvmvg", size=Size("1 GiB"),
                           format=fmt)
        device.configure_mock(name="".join(["a" for i in range(20)]))

        it = self.list_partitions._add_to_store(device)
        self.assertEqual(self.list_partitions.partitions_list.get_value(it, 1), device.name)
        self.assertEqual(self.list_partitions.partitions_list.get_value(it, 2), "lvm")
        self.assertIsNone(self.list_partitions.partitions_list.get_value(it, 3))
        self.assertEqual(self.list_partitions.partitions_list.get_value(it, 4), str(device.size))
        self.assertEqual(self.list_partitions.partitions_list.get_value(it, 5), "")
        self.assertIsNone(self.list_partitions.partitions_list.get_value(it, 6))

        # child device of previously added device
        device = MagicMock(type="lvmlv", size=Size("1 GiB"),
                           format=MagicMock(type="ext4", mountable=True, label=60 * "a"))
        device.configure_mock(name="aaa")

        self.blivet_gui.client.remote_call.return_value = {}
        child_it = self.list_partitions._add_to_store(device, it)
        # check that 'child_it' is actually child of 'it'
        self.assertEqual(self.list_partitions.partitions_list[self.list_partitions.partitions_list.iter_children(it)][0],
                         self.list_partitions.partitions_list[child_it][0])
        self.assertEqual(self.list_partitions.partitions_list.get_value(child_it, 1), device.name)
        self.assertEqual(self.list_partitions.partitions_list.get_value(child_it, 2), "lvmlv")
        self.assertEqual(self.list_partitions.partitions_list.get_value(child_it, 3), device.format.type)
        self.assertEqual(self.list_partitions.partitions_list.get_value(child_it, 4), str(device.size))
        self.assertEqual(self.list_partitions.partitions_list.get_value(child_it, 5), 15 * "a" + "...")
        self.assertEqual(self.list_partitions.partitions_list.get_value(child_it, 6), "")


if __name__ == "__main__":
    unittest.main()
