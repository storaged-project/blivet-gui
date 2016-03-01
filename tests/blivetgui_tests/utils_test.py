# -*- coding: utf-8 -*-

import unittest
from unittest.mock import MagicMock, patch

from blivetgui.blivet_utils import BlivetUtils, FreeSpaceDevice

from blivet.size import Size


class FreeSpaceDeviceTest(unittest.TestCase):

    def test_free_basic(self):
        free = FreeSpaceDevice(free_size=Size("8 GiB"), dev_id=0, start=0, end=1, parents=[MagicMock(type="disk")], logical=True)

        self.assertTrue(free.is_logical)
        self.assertFalse(free.is_extended)
        self.assertFalse(free.is_primary)
        self.assertEqual(len(free.children), 0)
        self.assertEqual(free.type, "free space")
        self.assertIsNotNone(free.format)
        self.assertIsNone(free.format.type)
        self.assertEqual(free.disk, free.parents[0])

    def test_free_type(self):
        disk = MagicMock(type="disk", kids=0, is_disk=True, format=MagicMock(type="disklabel"))
        free = FreeSpaceDevice(free_size=Size("8 GiB"), dev_id=0, start=0, end=1, parents=[disk])

        self.assertTrue(free.is_empty_disk)
        self.assertFalse(free.is_uninitialized_disk)
        self.assertFalse(free.is_free_region)

        disk = MagicMock(type="disk", kids=0, is_disk=True, format=MagicMock(type=None))
        free = FreeSpaceDevice(free_size=Size("8 GiB"), dev_id=0, start=0, end=1, parents=[disk])

        self.assertTrue(free.is_uninitialized_disk)
        self.assertFalse(free.is_empty_disk)
        self.assertFalse(free.is_free_region)

        disk = MagicMock(type="disk", kids=1, is_disk=True, format=MagicMock(type="disklabel"))
        free = FreeSpaceDevice(free_size=Size("8 GiB"), dev_id=0, start=0, end=1, parents=[disk])

        self.assertTrue(free.is_free_region)
        self.assertFalse(free.is_empty_disk)
        self.assertFalse(free.is_uninitialized_disk)

    def test_free_disk(self):
        # free space on a disk
        disk = MagicMock(type="disk", kids=0, is_disk=True, format=MagicMock(type=None))
        free = FreeSpaceDevice(free_size=Size("8 GiB"), dev_id=0, start=0, end=1, parents=[disk])
        self.assertEqual(free.disk, disk)

        # free space in a vg
        parent = MagicMock(type="lvmvg", kids=0, is_disk=False, format=MagicMock(type=None),
                           parents=[MagicMock(type="partition", kids=1, is_disk=False, parents=[disk],
                                    format=MagicMock(type="lvmpv"))])
        free = FreeSpaceDevice(free_size=Size("8 GiB"), dev_id=0, start=0, end=1, parents=[parent])
        self.assertEqual(free.disk, disk)

    def test_free_protected(self):
        disk = MagicMock(type="disk", kids=0, is_disk=True, format=MagicMock(type=None))
        free = FreeSpaceDevice(free_size=Size("8 GiB"), dev_id=0, start=0, end=1, parents=[disk])

        self.assertEqual(free.protected, disk.protected)


class BlivetUtilsTest(unittest.TestCase):

    @patch("blivetgui.blivet_utils.BlivetUtils._has_snapshots", lambda device: True)
    def test_resizable(self):
        device = MagicMock(type="", size=Size("1 GiB"))
        device.format = MagicMock(exists=True)
        device.format.return_value = None

        # swap is not resizable
        device.format.configure_mock(type="swap")
        res = BlivetUtils.device_resizable(MagicMock(), device)
        self.assertFalse(res.resizable)
        self.assertIsNone(res.error)
        self.assertEqual(res.min_size, Size("1 MiB"))
        self.assertEqual(res.max_size, Size("1 GiB"))

        # resizable device
        device.configure_mock(resizable=True, max_size=Size("2 GiB"), min_size=Size("500 MiB"))
        device.format.configure_mock(resizable=True, type="ext4")
        res = BlivetUtils.device_resizable(MagicMock(), device)
        self.assertTrue(res.resizable)
        self.assertIsNone(res.error)
        self.assertEqual(res.min_size, Size("500 MiB"))
        self.assertEqual(res.max_size, Size("2 GiB"))

        # resizable device and non-resizable format
        device.configure_mock(resizable=True, max_size=Size("2 GiB"), min_size=Size("500 MiB"))
        device.format.configure_mock(resizable=False, type="ext4")
        res = BlivetUtils.device_resizable(MagicMock(), device)
        self.assertFalse(res.resizable)
        self.assertIsNone(res.error)
        self.assertEqual(res.min_size, Size("1 MiB"))
        self.assertEqual(res.max_size, Size("1 GiB"))

        # LV with snapshot -> not resizable
        device.configure_mock(type="lvmlv", resizable=True, max_size=Size("2 GiB"), min_size=Size("500 MiB"))
        device.format.configure_mock(resizable=True, type="ext4")
        res = BlivetUtils.device_resizable(MagicMock(), device)
        self.assertFalse(res.resizable)
        self.assertIsNotNone(res.error)
        self.assertEqual(res.min_size, Size("1 MiB"))
        self.assertEqual(res.max_size, Size("1 GiB"))


if __name__ == "__main__":
    unittest.main()
