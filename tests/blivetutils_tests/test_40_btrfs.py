import unittest

import blivet

from blivetgui.communication.proxy_utils import ProxyDataContainer

from .blivetutilstestcase import BlivetUtilsTestCase
from .test_20_partitioning import PartitioningTestToolkit


SIZE_DELTA = blivet.size.Size("2 MiB")


class BtrfsTestToolkit(PartitioningTestToolkit):
    pass


class BlivetUtilsBtrfsTest(BlivetUtilsTestCase, BtrfsTestToolkit):

    def test_10_btrfs_volume_single(self):
        """ Test that we can create a single-device Btrfs volume """

        # initialize disk
        blivet_disk = self.get_blivet_device(self.vdevs[0])
        self.create_part_table(blivet_disk, "gpt")
        free = self.get_next_free_space(blivet_disk)

        # create the btrfs volume
        parent_selection = [ProxyDataContainer(parent_device=free.parents[0],
                                               free_space=free,
                                               selected_size=free.size)]
        size_selection = ProxyDataContainer(total_size=free.size,
                                            parents=parent_selection)
        user_input = ProxyDataContainer(device_type="btrfs volume",
                                        size_selection=size_selection,
                                        name="test_btrfs",
                                        label=None,
                                        encrypt=False,
                                        passphrase=None,
                                        encryption_type=None,
                                        encryption_sector_size=0,
                                        mountpoint=None,
                                        raid_level=None)

        ret = self.blivet_utils.add_device(user_input)
        self.assertTrue(ret.success)
        self.assertIsNone(ret.message)
        self.assertIsNone(ret.exception)
        self.assertIsNone(ret.traceback)

        # check the actions
        # partition create + btrfs format + btrfs volume create
        self.assertEqual(len(ret.actions), 3)

        # partition create action
        actions = [ac for ac in ret.actions if ac.is_create and ac.is_device and ac.device.type == "partition"]
        self.assertEqual(len(actions), 1)

        part = actions[0].device
        self.assertEqual(part.type, "partition")
        self.assertEqual(part.format.type, "btrfs")

        # btrfs format create action
        actions = [ac for ac in ret.actions if ac.is_create and ac.is_format and ac.format.type == "btrfs"]
        self.assertEqual(len(actions), 1)

        # btrfs volume create action
        actions = [ac for ac in ret.actions if ac.is_create and ac.is_device and ac.device.type == "btrfs volume"]
        self.assertEqual(len(actions), 1)

        btrfs_vol = actions[0].device
        self.assertIsNotNone(btrfs_vol)
        self.assertEqual(btrfs_vol.type, "btrfs volume")
        self.assertEqual(len(btrfs_vol.parents), 1)
        self.assertAlmostEqual(btrfs_vol.size, free.size, delta=SIZE_DELTA)
        self.assertEqual(btrfs_vol.format.type, "btrfs")
        self.assertEqual(btrfs_vol.format.label, "test_btrfs")

    def test_20_btrfs_volume_multi(self):
        """ Test that we can create a multi-device Btrfs volume """

        # initialize two disks
        blivet_disk1 = self.get_blivet_device(self.vdevs[0])
        blivet_disk2 = self.get_blivet_device(self.vdevs[1])
        self.create_part_table(blivet_disk1, "gpt")
        self.create_part_table(blivet_disk2, "gpt")
        free1 = self.get_next_free_space(blivet_disk1)
        free2 = self.get_next_free_space(blivet_disk2)

        # create the btrfs volume with raid1 for both data and metadata
        parent_selection = [ProxyDataContainer(parent_device=free1.parents[0],
                                               free_space=free1,
                                               selected_size=free1.size),
                            ProxyDataContainer(parent_device=free2.parents[0],
                                               free_space=free2,
                                               selected_size=free2.size)]
        size_selection = ProxyDataContainer(total_size=free1.size + free2.size,
                                            parents=parent_selection)
        user_input = ProxyDataContainer(device_type="btrfs volume",
                                        size_selection=size_selection,
                                        name="test_btrfs_raid",
                                        label=None,
                                        mountpoint=None,
                                        encrypt=False,
                                        passphrase=None,
                                        encryption_type=None,
                                        encryption_sector_size=0,
                                        raid_level="single")

        ret = self.blivet_utils.add_device(user_input)
        self.assertTrue(ret.success)
        self.assertIsNone(ret.message)
        self.assertIsNone(ret.exception)
        self.assertIsNone(ret.traceback)

        # check the actions
        # 2x partition create + 2x btrfs format + 1x btrfs volume create
        self.assertEqual(len(ret.actions), 5)

        # partition create actions
        actions = [ac for ac in ret.actions if ac.is_create and ac.is_device and ac.device.type == "partition"]
        self.assertEqual(len(actions), 2)

        for part in [ac.device for ac in actions]:
            self.assertEqual(part.type, "partition")
            self.assertEqual(part.format.type, "btrfs")

        # btrfs format create actions
        actions = [ac for ac in ret.actions if ac.is_create and ac.is_format and ac.format.type == "btrfs"]
        self.assertEqual(len(actions), 2)

        # btrfs volume create action
        actions = [ac for ac in ret.actions if ac.is_create and ac.is_device and ac.device.type == "btrfs volume"]
        self.assertEqual(len(actions), 1)

        btrfs_vol = actions[0].device
        self.assertIsNotNone(btrfs_vol)

        self.assertEqual(btrfs_vol.type, "btrfs volume")
        self.assertEqual(len(btrfs_vol.parents), 2)
        self.assertEqual(btrfs_vol.data_level.name, "single")
        self.assertEqual(btrfs_vol.metadata_level.name, "single")
        self.assertAlmostEqual(btrfs_vol.size, free1.size + free2.size, delta=SIZE_DELTA)
        self.assertEqual(btrfs_vol.format.type, "btrfs")
        self.assertEqual(btrfs_vol.format.label, "test_btrfs_raid")

    def test_30_btrfs_volume_encrypted(self):
        """ Test that we can create an encrypted Btrfs volume """

        # initialize disk
        blivet_disk = self.get_blivet_device(self.vdevs[0])
        self.create_part_table(blivet_disk, "gpt")
        free = self.get_next_free_space(blivet_disk)

        # create encrypted btrfs volume
        parent_selection = [ProxyDataContainer(parent_device=free.parents[0],
                                               free_space=free,
                                               selected_size=free.size)]
        size_selection = ProxyDataContainer(total_size=free.size,
                                            parents=parent_selection)
        user_input = ProxyDataContainer(device_type="btrfs volume",
                                        size_selection=size_selection,
                                        name="encrypted_btrfs",
                                        label=None,
                                        mountpoint=None,
                                        encrypt=True,
                                        passphrase="password",
                                        encryption_type="luks2",
                                        encryption_sector_size=512,
                                        raid_level=None)

        ret = self.blivet_utils.add_device(user_input)
        self.assertTrue(ret.success)
        self.assertIsNone(ret.message)
        self.assertIsNone(ret.exception)
        self.assertIsNone(ret.traceback)

        # check the actions
        # partition + luks format + luks device + btrfs format + btrfs volume
        self.assertEqual(len(ret.actions), 5)

        # partition create action
        actions = [ac for ac in ret.actions if ac.is_create and ac.is_device and ac.device.type == "partition"]
        self.assertEqual(len(actions), 1)
        part = actions[0].device

        # luks format create action
        actions = [ac for ac in ret.actions if ac.is_create and ac.is_format and ac.format.type == "luks"]
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].device, part)

        # luks device create action
        actions = [ac for ac in ret.actions if ac.is_create and ac.is_device and ac.device.type == "luks/dm-crypt"]
        self.assertEqual(len(actions), 1)
        luks_dev = actions[0].device
        self.assertEqual(len(luks_dev.parents), 1)
        self.assertEqual(luks_dev.parents[0], part)

        # btrfs format on luks device
        actions = [ac for ac in ret.actions if ac.is_create and ac.is_format and ac.format.type == "btrfs"]
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].device, luks_dev)

        # btrfs volume on luks device
        actions = [ac for ac in ret.actions if ac.is_create and ac.is_device and ac.device.type == "btrfs volume"]
        self.assertEqual(len(actions), 1)
        btrfs_vol = actions[0].device
        self.assertEqual(len(btrfs_vol.parents), 1)
        self.assertEqual(btrfs_vol.parents[0], luks_dev)

    def test_40_btrfs_subvolume(self):
        """ Test that we can create Btrfs subvolumes """

        # initialize disk
        blivet_disk = self.get_blivet_device(self.vdevs[0])
        self.create_part_table(blivet_disk, "gpt")
        free = self.get_next_free_space(blivet_disk)

        # first create a btrfs volume
        parent_selection = [ProxyDataContainer(parent_device=free.parents[0],
                                               free_space=free,
                                               selected_size=free.size)]
        size_selection = ProxyDataContainer(total_size=free.size,
                                            parents=parent_selection)
        user_input = ProxyDataContainer(device_type="btrfs volume",
                                        size_selection=size_selection,
                                        name="test_vol",
                                        label=None,
                                        mountpoint=None,
                                        encrypt=False,
                                        passphrase=None,
                                        encryption_type=None,
                                        encryption_sector_size=0,
                                        raid_level=None)

        ret = self.blivet_utils.add_device(user_input)
        self.assertTrue(ret.success)

        # get the btrfs volume device
        btrfs_vol_actions = [ac for ac in ret.actions if ac.is_create and ac.is_device and ac.device.type == "btrfs volume"]
        self.assertEqual(len(btrfs_vol_actions), 1)
        btrfs_vol = btrfs_vol_actions[0].device

        # now create a subvolume on it
        parent_selection = [ProxyDataContainer(parent_device=btrfs_vol,
                                               selected_size=btrfs_vol.size)]
        size_selection = ProxyDataContainer(total_size=btrfs_vol.size,
                                            parents=parent_selection)
        user_input = ProxyDataContainer(device_type="btrfs subvolume",
                                        size_selection=size_selection,
                                        name="home",
                                        mountpoint=None)

        ret = self.blivet_utils.add_device(user_input)

        self.assertTrue(ret.success)
        self.assertIsNone(ret.message)
        self.assertIsNone(ret.exception)
        self.assertIsNone(ret.traceback)

        # check the action - only one for subvolume create
        self.assertEqual(len(ret.actions), 1)

        action = ret.actions[0]
        self.assertTrue(action.is_create)
        self.assertTrue(action.is_device)

        subvol = action.device
        self.assertEqual(subvol.type, "btrfs subvolume")
        self.assertEqual(len(subvol.parents), 1)
        self.assertEqual(subvol.parents[0], btrfs_vol)
        self.assertEqual(subvol.format.type, "btrfs")

    def test_50_btrfs_delete_volume(self):
        """ Test deleting a Btrfs volume """

        # create a btrfs volume first
        blivet_disk = self.get_blivet_device(self.vdevs[0])
        self.create_part_table(blivet_disk, "gpt")
        free = self.get_next_free_space(blivet_disk)

        parent_selection = [ProxyDataContainer(parent_device=free.parents[0],
                                               free_space=free,
                                               selected_size=free.size)]
        size_selection = ProxyDataContainer(total_size=free.size,
                                            parents=parent_selection)
        user_input = ProxyDataContainer(device_type="btrfs volume",
                                        size_selection=size_selection,
                                        name="to_delete",
                                        label=None,
                                        mountpoint=None,
                                        encrypt=False,
                                        passphrase=None,
                                        encryption_type=None,
                                        encryption_sector_size=0,
                                        raid_level=None)

        ret = self.blivet_utils.add_device(user_input)
        self.assertTrue(ret.success)

        # get the btrfs volume
        btrfs_vol_actions = [ac for ac in ret.actions if ac.is_create and ac.is_device and ac.device.type == "btrfs volume"]
        self.assertEqual(len(btrfs_vol_actions), 1)
        btrfs_vol = btrfs_vol_actions[0].device

        # get the partition
        part_actions = [ac for ac in ret.actions if ac.is_create and ac.is_device and ac.device.type == "partition"]
        self.assertEqual(len(part_actions), 1)

        # delete the btrfs volume without deleting the partition
        ret = self.blivet_utils.delete_device(btrfs_vol, delete_parents=False)
        self.assertTrue(ret.success)
        self.assertIsNone(ret.message)
        self.assertIsNone(ret.exception)
        self.assertIsNone(ret.traceback)

        # should have actions to destroy btrfs format and volume
        self.assertGreaterEqual(len(ret.actions), 2)

        # check for btrfs volume destroy action
        actions = [ac for ac in ret.actions if ac.is_destroy and ac.is_device and ac.device.type == "btrfs volume"]
        self.assertEqual(len(actions), 1)

        # now delete with parents
        self.reset()
        blivet_disk = self.get_blivet_device(self.vdevs[0])
        self.create_part_table(blivet_disk, "gpt")
        free = self.get_next_free_space(blivet_disk)

        parent_selection = [ProxyDataContainer(parent_device=free.parents[0],
                                               free_space=free,
                                               selected_size=free.size)]
        size_selection = ProxyDataContainer(total_size=free.size,
                                            parents=parent_selection)
        user_input = ProxyDataContainer(device_type="btrfs volume",
                                        size_selection=size_selection,
                                        name="to_delete2",
                                        label=None,
                                        mountpoint=None,
                                        encrypt=False,
                                        passphrase=None,
                                        encryption_type=None,
                                        encryption_sector_size=0,
                                        raid_level=None)

        ret = self.blivet_utils.add_device(user_input)
        self.assertTrue(ret.success)

        btrfs_vol_actions = [ac for ac in ret.actions if ac.is_create and ac.is_device and ac.device.type == "btrfs volume"]
        btrfs_vol = btrfs_vol_actions[0].device

        # delete with parents
        ret = self.blivet_utils.delete_device(btrfs_vol, delete_parents=True)

        self.assertTrue(ret.success)

        # should have actions to destroy both volume and partition
        actions = [ac for ac in ret.actions if ac.is_destroy and ac.is_device]
        device_types = {ac.device.type for ac in actions}
        self.assertIn("btrfs volume", device_types)
        self.assertIn("partition", device_types)


if __name__ == "__main__":
    unittest.main()
