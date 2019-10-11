import os
import unittest
from collections import namedtuple

import blivet

from gi.repository import BlockDev

from blivetgui.communication.proxy_utils import ProxyDataContainer

from blivetutilstestcase import BlivetUtilsTestCase

from test_10_disks import DisksTestToolkit


SIZE_DELTA = blivet.size.Size("2 MiB")


PartSpec = namedtuple("PartSpec", ["start", "size", "ptype"])


class PartitioningTestToolkit(DisksTestToolkit):

    def get_next_free_space(self, disk, min_size=blivet.size.Size("10 MiB"), logical=False):
        children = self.blivet_utils.get_disk_children(disk)
        if logical:
            free = next((p for p in children.logicals if p.type == "free space" and
                         p.size >= min_size), None)
        else:
            free = next((p for p in children.partitions if p.type == "free space" and
                         p.size >= min_size), None)
        self.assertIsNotNone(free)
        return free

    def get_free_spaces(self, disk, min_size=blivet.size.Size("10 MiB")):
        children = self.blivet_utils.get_disk_children(disk)
        return [p for p in children.partitions if p.type == "free space" and
                p.size >= min_size]

    def get_partitions(self, disk):
        children = self.blivet_utils.get_disk_children(disk)
        return [p for p in children.partitions if p.type == "partition"]

    def create_partition(self, free_space, size=None, fstype="ext4", label=None, ptype="primary"):
        if size is None:
            size = free_space.size

        # create "user input" for the new partition
        parent_selection = ProxyDataContainer(parent_device=free_space.parents[0],
                                              free_space=free_space,
                                              selected_size=size)
        size_selection = ProxyDataContainer(total_size=size,
                                            parents=[parent_selection])
        user_input = ProxyDataContainer(device_type="partition",
                                        size_selection=size_selection,
                                        filesystem=fstype,
                                        name=None,
                                        label=label,
                                        mountpoint=None,
                                        encrypt=False,
                                        passphrase=None,
                                        raid_level=None,
                                        advanced={"parttype": ptype})

        ret = self.blivet_utils.add_device(user_input)

        self.assertTrue(ret.success)
        self.assertIsNone(ret.message)
        self.assertIsNone(ret.exception)
        self.assertIsNone(ret.traceback)

        return ret.actions

    def create_preexisting(self, disk, table_type, partitions):
        table = BlockDev.PartTableType.MSDOS if table_type == "msdos" else BlockDev.PartTableType.GPT
        BlockDev.part_create_table(disk, table)

        for part in partitions:
            BlockDev.part_create_part(disk, part.ptype, part.start, part.size, BlockDev.PartAlign.OPTIMAL)

    def clean_up_preexisting(self, disk, partitions):
        for i in range(len(partitions)):
            BlockDev.part_delete_part(disk, "%s%d" % (disk, i + 1))
        os.system("wipefs -a %s > /dev/null" % disk)


class BlivetUtilsDisksTest(BlivetUtilsTestCase, PartitioningTestToolkit):

    @classmethod
    def setUpClass(cls):
        plugins = BlockDev.plugin_specs_from_names(("part",))
        if not BlockDev.is_initialized():
            BlockDev.init(plugins, None)
        else:
            BlockDev.reinit(plugins, False, None)

        super().setUpClass()

    def _check_part_actions(self, actions, blivet_part):
        # there should be two actions --> one for partition and another one for fs
        self.assertEqual(len(actions), 2)

        part_ac = next((ac for ac in actions if ac.is_device), None)
        self.assertIsNotNone(part_ac)

        fmt_ac = next((ac for ac in actions if ac.is_format), None)
        self.assertIsNotNone(fmt_ac)

        self.assertIsNotNone(blivet_part)
        self.assertIsInstance(blivet_part, blivet.devices.PartitionDevice)
        self.assertIsNotNone(blivet_part.format)
        self.assertIsInstance(blivet_part.format, blivet.formats.fs.Ext4FS)

    def _create_and_check_multiple_partitions(self, disk, num_parts):
        blivet_parts = []
        for i in range(num_parts):
            free = self.get_next_free_space(disk)
            part_size = free.size / (num_parts - i)  # all partitions have same size
            actions = self.create_partition(free, part_size, label=str(i))

            # and a new device should be added
            blivet_part = self.get_blivet_device(self.vdevs[0] + str(i + 1))  # vda1-num_parts
            self.assertIsNotNone(blivet_part)
            blivet_parts.append(blivet_part)

            self._check_part_actions(actions, blivet_part)

        return blivet_parts

    def test_10_msdos_basic(self):
        """ Test that we can create a single partition on MSDOS partition table """

        blivet_disk = self.get_blivet_device(self.vdevs[0])

        # create disklabel on the disk
        self.create_part_table(blivet_disk, "msdos")

        # get first free space on the disk and create partition on it
        free = self.get_next_free_space(blivet_disk)
        actions = self.create_partition(free)

        # a new device should be added
        blivet_part = self.get_blivet_device(self.vdevs[0] + "1")  # vda1
        self.assertTrue(blivet_part.is_primary)
        self.assertAlmostEqual(blivet_part.size, free.size, delta=SIZE_DELTA)

        self._check_part_actions(actions, blivet_part)

        # get children of the disk -- it should now be only one partition
        children = self.blivet_utils.get_disk_children(blivet_disk)
        self.assertEqual(len(children.partitions), 1)
        self.assertEqual(children.partitions[0], blivet_part)
        self.assertFalse(children.extended)
        self.assertFalse(children.logicals)

    def test_20_msdos_multiple(self):
        """ Test that we can create multiple partitions on MSDOS partition table """

        blivet_disk = self.get_blivet_device(self.vdevs[0])

        # create disklabel on the disk
        self.create_part_table(blivet_disk, "msdos")

        num_parts = 4
        blivet_parts = self._create_and_check_multiple_partitions(blivet_disk, num_parts)
        for part in blivet_parts:
            self.assertAlmostEqual(part.size, blivet_disk.size / num_parts, delta=SIZE_DELTA)

        # get children of the disk -- it should now have 4 primary partitions
        children = self.blivet_utils.get_disk_children(blivet_disk)
        self.assertEqual(len(children.partitions), num_parts)
        self.assertCountEqual(children.partitions, blivet_parts)
        self.assertFalse(children.extended)
        self.assertFalse(children.logicals)

        # check order of the partitions using the fs label set when creating them
        sorted_parts = sorted(blivet_parts, key=lambda p: p.parted_partition.geometry.start)
        self.assertCountEqual([p.format.label for p in sorted_parts],
                              [str(i) for i in range(num_parts)])

    def test_30_msdos_extended(self):
        """ Test that we can create an extended partition on MSDOS partition table """

        blivet_disk = self.get_blivet_device(self.vdevs[0])

        # create disklabel on the disk
        self.create_part_table(blivet_disk, "msdos")

        # get first free space on the disk and create partition on it
        free = self.get_next_free_space(blivet_disk)
        actions = self.create_partition(free, ptype="extended")

        # only 1 action -- no format for extended partition
        self.assertEqual(len(actions), 1)
        self.assertTrue(actions[0].is_device)
        self.assertTrue(actions[0].is_create)

        blivet_part = self.get_blivet_device(self.vdevs[0] + "1")  # vda1
        self.assertIsNotNone(blivet_part)
        self.assertIsInstance(blivet_part, blivet.devices.PartitionDevice)
        self.assertTrue(blivet_part.is_extended)
        self.assertAlmostEqual(blivet_part.size, free.size, delta=SIZE_DELTA)

        # get next free space, it should be in the extended partition, and
        # create a new logical partition on it
        free = self.get_next_free_space(blivet_disk, logical=True)
        self.assertTrue(free.is_logical)

        actions = self.create_partition(free, size=free.size / 2, ptype="logical")

        blivet_part = self.get_blivet_device(self.vdevs[0] + "5")  # vda5 (first logical)
        self.assertTrue(blivet_part.is_logical)
        self.assertAlmostEqual(blivet_part.size, free.size / 2, delta=SIZE_DELTA)

        self._check_part_actions(actions, blivet_part)

    def test_35_msdos_preexisting_position(self):
        """ Test that we can create partitions on disk with a preexisting partition in correct order """

        blivet_disk = self.get_blivet_device(self.vdevs[1])

        # create preexisting partition in the middle of the disk and keep some space after it
        start1 = blivet_disk.size / 2
        size1 = blivet_disk.size / 4
        parts = [PartSpec(start=start1, size=size1, ptype=BlockDev.PartType.NORMAL)]
        self.create_preexisting(blivet_disk.path, "msdos", parts)
        self.addCleanup(self.clean_up_preexisting, blivet_disk.path, parts)

        # reset blivet
        self.reset()
        blivet_disk = self.get_blivet_device(self.vdevs[1])

        free = self.get_free_spaces(blivet_disk)
        self.assertEqual(len(free), 2)

        # add partition to the first free space
        size2 = free[0].size / 4
        actions1 = self.create_partition(free[0], size=size2, label="1")

        blivet_part1 = self.get_blivet_device(self.vdevs[1] + "2")  # vda2
        self.assertTrue(blivet_part1.is_primary)
        self.assertAlmostEqual(blivet_part1.size, size2, delta=SIZE_DELTA)
        self.assertAlmostEqual(blivet_part1.parted_partition.geometry.start,
                               free[0].start, delta=SIZE_DELTA)
        self._check_part_actions(actions1, blivet_part1)

        # and now to the second one
        size3 = free[1].size
        actions2 = self.create_partition(free[1], size=size3, label="3")

        blivet_part2 = self.get_blivet_device(self.vdevs[1] + "3")  # vda3
        self.assertTrue(blivet_part2.is_primary)
        self.assertAlmostEqual(blivet_part2.size, size3, delta=SIZE_DELTA)
        self.assertAlmostEqual(blivet_part2.parted_partition.geometry.start,
                               free[1].start, delta=SIZE_DELTA)
        self._check_part_actions(actions2, blivet_part2)

        blivet_parts = self.get_partitions(blivet_disk)
        self.assertEqual(len(blivet_parts), 3)
        sorted_parts = sorted(blivet_parts, key=lambda p: p.parted_partition.geometry.start)
        self.assertEqual(sorted_parts[0].format.label, "1")
        self.assertIsNone(sorted_parts[1].format.type)  # we created this one using libblockdev without FS
        self.assertEqual(sorted_parts[2].format.label, "3")

    def test_40_gpt_basic(self):
        """ Test that we can create a single partition on GPT partition table """

        blivet_disk = self.get_blivet_device(self.vdevs[0])

        # create disklabel on the disk
        self.create_part_table(blivet_disk, "gpt")

        # get first free space on the disk and create partition on it
        free = self.get_next_free_space(blivet_disk)
        actions = self.create_partition(free)

        # a new device should be added
        blivet_part = self.get_blivet_device(self.vdevs[0] + "1")  # vda1

        self.assertAlmostEqual(blivet_part.size, blivet_disk.size, delta=SIZE_DELTA)

        # check created actions
        self._check_part_actions(actions, blivet_part)

    def test_50_gpt_multiple(self):
        """ Test that we can create multiple partitions on GPT partition table """

        blivet_disk = self.get_blivet_device(self.vdevs[0])

        # create disklabel on the disk
        self.create_part_table(blivet_disk, "gpt")

        num_parts = 10
        blivet_parts = self._create_and_check_multiple_partitions(blivet_disk, num_parts)

        for part in blivet_parts:
            self.assertAlmostEqual(part.size, blivet_disk.size / num_parts, delta=SIZE_DELTA)

        # get children of the disk -- it should now have 10 "primary" partitions
        children = self.blivet_utils.get_disk_children(blivet_disk)
        self.assertEqual(len(children.partitions), num_parts)
        self.assertCountEqual(children.partitions, blivet_parts)
        self.assertFalse(children.extended)
        self.assertFalse(children.logicals)

        # check order of the partitions using the fs label set when creating them
        sorted_parts = sorted(blivet_parts, key=lambda p: p.parted_partition.geometry.start)
        self.assertCountEqual([p.format.label for p in sorted_parts],
                              [str(i) for i in range(num_parts)])


if __name__ == "__main__":
    unittest.main()
