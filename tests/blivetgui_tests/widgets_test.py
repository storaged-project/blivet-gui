# -*- coding: utf-8 -*-

import os
import unittest

from blivet.devicelibs.raid import RAID0, RAID1, RAID5, Single, Linear

from blivetgui.dialogs.widgets import RaidChooser


@unittest.skipUnless("DISPLAY" in os.environ.keys(), "requires X server")
class RaidChooserTest(unittest.TestCase):

    def test_10_update(self):
        chooser = RaidChooser()
        chooser.supported_raids = {"mdraid": [RAID0, RAID1, RAID5, Linear],
                                   "lvmlv": [RAID0, RAID1, RAID5, Linear],
                                   "btrfs volume": [RAID0, RAID1, RAID5, Single]}

        # mdraid with 2 parents -> raid0, raid1 and linear should be available
        # and autoselect should select raid0
        # chooser should be visible and sensitive
        chooser.update("mdraid", 2)
        self.assertEqual(len(chooser._liststore_raid), 3)
        self.assertListEqual([RAID0, RAID1, Linear], [row[1] for row in chooser._liststore_raid])

        chooser.autoselect("mdraid")
        self.assertEqual(chooser.selected_level, RAID0)
        self.assertTrue(chooser.get_visible())
        self.assertTrue(chooser.get_sensitive())

        # btrfs with 3 parents -> raid0, raid1, raid5 and single should be available
        # and autoselect should select single
        # chooser should be visible and sensitive
        chooser.update("btrfs volume", 3)
        self.assertEqual(len(chooser._liststore_raid), 4)
        self.assertListEqual([RAID0, RAID1, RAID5, Single], [row[1] for row in chooser._liststore_raid])

        chooser.autoselect("btrfs volume")
        self.assertEqual(chooser.selected_level, Single)
        self.assertTrue(chooser.get_visible())
        self.assertTrue(chooser.get_sensitive())

        # lvmlv with 1 parent -> only linear should be available
        # and autoselect should select linear
        # chooser should be visible and insensitive
        chooser.update("lvmlv", 1)
        self.assertEqual(len(chooser._liststore_raid), 1)
        self.assertListEqual([Linear], [row[1] for row in chooser._liststore_raid])

        chooser.autoselect("lvmlv")
        self.assertEqual(chooser.selected_level, Linear)
        self.assertTrue(chooser.get_visible())
        self.assertFalse(chooser.get_sensitive())

        # partition with 1 parent -> no levels and None should be autoselected
        # chooser should be invisible and insensitive
        chooser.update("partition", 1)
        self.assertEqual(len(chooser._liststore_raid), 0)

        chooser.autoselect("partition")
        self.assertEqual(chooser.selected_level, None)
        self.assertFalse(chooser.get_visible())
        self.assertFalse(chooser.get_sensitive())

    def test_20_selection(self):
        chooser = RaidChooser()
        chooser.supported_raids = {"mdraid": [RAID0, RAID1, RAID5, Linear]}
        chooser.update("mdraid", 2)

        # raid5 not supported for 2 devices
        with self.assertRaises(ValueError):
            chooser.selected_level = RAID5

        chooser.selected_level = RAID1
        self.assertEqual(chooser.selected_level, RAID1)


if __name__ == "__main__":
    unittest.main()
