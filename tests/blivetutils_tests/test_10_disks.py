import unittest

import blivet

from blivetgui.communication.proxy_utils import ProxyDataContainer

from .blivetutilstestcase import BlivetUtilsTestCase, BlivetUtilsTestToolkit


class DisksTestToolkit(BlivetUtilsTestToolkit):

    def create_part_table(self, disk, table="msdos"):
        ret = self.blivet_utils.create_disk_label(disk, table)

        self.assertTrue(ret.success)
        self.assertIsNone(ret.message)
        self.assertIsNone(ret.exception)
        self.assertIsNone(ret.traceback)

        return ret.actions

    def format_device(self, device, fstype="ext4", label=None, mountpoint=None):
        # prepare "user input" for editing (in this case formatting) a device
        user_input = ProxyDataContainer(edit_device=device, format=True,
                                        filesystem=fstype, label=label,
                                        mountpoint=mountpoint)

        ret = self.blivet_utils.format_device(user_input)
        self.assertTrue(ret.success)
        self.assertIsNone(ret.message)
        self.assertIsNone(ret.exception)
        self.assertIsNone(ret.traceback)

        return ret.actions


class BlivetUtilsDisksTest(BlivetUtilsTestCase, DisksTestToolkit):

    def test_10_empty_disks(self):
        # all disks are empty --> no "group" devices
        group_devices = self.blivet_utils.get_group_devices()
        self.assertDictEqual(group_devices, {"lvm": [], "raid": [], "btrfs": []})

        # disks are empty and without partition table --> no usable free space
        # should be reported (unpartitioned disks are not considered usable)
        free_devices = self.blivet_utils.get_free_info()
        self.assertEqual(len(free_devices), 0)

        # check "children" of the disks --> empty disks should report only
        # one special "free space" child
        for disk_name in self.vdevs:
            disk_device = self.get_blivet_device(disk_name)
            self.assertIsNotNone(disk_device)
            children = self.blivet_utils.get_disk_children(disk_device)
            self.assertIsNone(children.extended)
            self.assertIsNone(children.logicals)
            self.assertEqual(len(children.partitions), 1)

            # the only "partition" should be a free space with same size as the
            # disk and with that disks as the only parent
            self.assertEqual(children.partitions[0].type, "free space")
            self.assertTrue(children.partitions[0].is_uninitialized_disk)
            self.assertEqual(children.partitions[0].size, disk_device.size)
            self.assertEqual(len(children.partitions[0].parents), 1)
            self.assertEqual(children.partitions[0].parents[0], disk_device)

    def test_20_partition_table(self):
        blivet_disk = self.get_blivet_device(self.vdevs[0])
        label = "msdos"

        # create disklabel on the disk
        actions = self.create_part_table(blivet_disk, label)

        # check scheduled actions
        self.assertEqual(len(actions), 1)
        self.assertIsInstance(actions[0], blivet.deviceaction.ActionCreateFormat)

        self.assertEqual(actions[0].device, blivet_disk)
        self.assertTrue(actions[0].is_create)
        self.assertTrue(actions[0].is_format)

        # check that the device has been changed
        blivet_disk = self.get_blivet_device(self.vdevs[0])
        self.assertEqual(blivet_disk.format.type, "disklabel")
        self.assertEqual(blivet_disk.format.label_type, label)

        # get "children" of the disk, the only "partition" should be a free
        # space with same size as the disk and with that disks as the only parent
        children = self.blivet_utils.get_disk_children(blivet_disk)
        self.assertEqual(children.partitions[0].type, "free space")
        self.assertTrue(children.partitions[0].is_empty_disk)
        self.assertAlmostEqual(children.partitions[0].size, blivet_disk.size, delta=blivet.size.Size("1 MiB"))
        self.assertEqual(len(children.partitions[0].parents), 1)
        self.assertEqual(children.partitions[0].parents[0], blivet_disk)

    def test_30_raw_format(self):
        blivet_disk = self.get_blivet_device(self.vdevs[0])
        fs = "ext4"

        # format the disks to ext4
        actions = self.format_device(device=blivet_disk, fstype=fs)

        # check scheduled actions
        self.assertEqual(len(actions), 2)
        self.assertIsInstance(actions[0], blivet.deviceaction.ActionDestroyFormat)
        self.assertIsInstance(actions[1], blivet.deviceaction.ActionCreateFormat)

        self.assertEqual(actions[0].device, blivet_disk)
        self.assertTrue(actions[0].is_destroy)
        self.assertTrue(actions[0].is_format)

        self.assertEqual(actions[1].device, blivet_disk)
        self.assertTrue(actions[1].is_create)
        self.assertTrue(actions[1].is_format)

        # check that the device has been changed
        blivet_disk = self.get_blivet_device(self.vdevs[0])
        self.assertEqual(blivet_disk.format.type, fs)

        # get "children" of the disk, the only "partition" should be the disk itself
        children = self.blivet_utils.get_disk_children(blivet_disk)
        self.assertEqual(children.partitions[0].type, "disk")
        self.assertEqual(children.partitions[0].size, blivet_disk.size)
        self.assertEqual(len(children.partitions[0].parents), 0)
        self.assertEqual(children.partitions[0], blivet_disk)


if __name__ == "__main__":
    unittest.main()
