import unittest

import blivet

from blivetgui.communication.proxy_utils import ProxyDataContainer

from .blivetutilstestcase import BlivetUtilsTestCase
from .test_20_partitioning import PartitioningTestToolkit


SIZE_DELTA = blivet.size.Size("2 MiB")


class MDTestToolkit(PartitioningTestToolkit):
    pass


class BlivetUtilsMDRaidTest(BlivetUtilsTestCase, MDTestToolkit):

    def test_10_md_device(self):
        """ Test that we can create MD arrays """

        # initialize two disks
        blivet_disk1 = self.get_blivet_device(self.vdevs[0])
        blivet_disk2 = self.get_blivet_device(self.vdevs[1])
        self.create_part_table(blivet_disk1, "gpt")
        self.create_part_table(blivet_disk2, "gpt")
        free1 = self.get_next_free_space(blivet_disk1)
        free2 = self.get_next_free_space(blivet_disk2)

        # create the array
        parent_selection = [ProxyDataContainer(parent_device=free1.parents[0],
                                               free_space=free1,
                                               selected_size=free1.size),
                            ProxyDataContainer(parent_device=free2.parents[0],
                                               free_space=free2,
                                               selected_size=free2.size)]
        size_selection = ProxyDataContainer(total_size=free1.size + free2.size,
                                            parents=parent_selection)
        user_input = ProxyDataContainer(device_type="mdraid",
                                        size_selection=size_selection,
                                        filesystem="ext4",
                                        name=None,
                                        label=None,
                                        mountpoint=None,
                                        encrypt=False,
                                        passphrase=None,
                                        raid_level="raid1",
                                        advanced=None)

        ret = self.blivet_utils.add_device(user_input)

        self.assertTrue(ret.success)
        self.assertIsNone(ret.message)
        self.assertIsNone(ret.exception)
        self.assertIsNone(ret.traceback)

        # check the actions
        self.assertEqual(len(ret.actions), 6)

        # partition create actions
        actions = [ac for ac in ret.actions if ac.is_create and ac.is_device and ac.device.type == "partition"]
        self.assertEqual(len(actions), 2)

        for part in [ac.device for ac in actions]:
            self.assertEqual(part.type, "partition")
            self.assertEqual(part.format.type, "mdmember")

        # mdmember create actions
        actions = [ac for ac in ret.actions if ac.is_create and ac.is_format and ac.format.type == "mdmember"]
        self.assertEqual(len(actions), 2)

        # mdarray create action
        actions = [ac for ac in ret.actions if ac.is_create and ac.is_device and ac.device.type == "mdarray"]
        self.assertEqual(len(actions), 1)

        raid_dev = actions[0].device
        self.assertIsNotNone(raid_dev)

        self.assertEqual(raid_dev.type, "mdarray")
        self.assertEqual(len(raid_dev.parents), 2)
        self.assertEqual(raid_dev.total_devices, 2)
        self.assertEqual(raid_dev.total_devices, 2)
        self.assertEqual(raid_dev.level.name, "raid1")
        self.assertAlmostEqual(raid_dev.size, free1.size, delta=SIZE_DELTA)
        self.assertEqual(raid_dev.format.type, "ext4")

        # format create action
        actions = [ac for ac in ret.actions if ac.is_create and ac.is_format and ac.format.type == "ext4"]
        self.assertEqual(len(actions), 1)


if __name__ == "__main__":
    unittest.main()
