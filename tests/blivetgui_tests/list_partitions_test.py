# -*- coding: utf-8 -*-

import unittest
from unittest.mock import MagicMock

from blivetgui.list_partitions import ListPartitions

class ListPartitionsTest(unittest.TestCase):

    def setUp(self):
        self.blivet_gui = MagicMock(kickstart_mode=False)

        self.list_partitions = ListPartitions(self.blivet_gui)

    def test_allow_delete(self):
        # do not allow deleting free space and non-leaf devices
        device = MagicMock(type="free space")
        self.assertFalse(self.list_partitions._allow_delete_device(device))
        device = MagicMock(type="partition", isleaf=False)
        self.assertFalse(self.list_partitions._allow_delete_device(device))

        # unformatted leaves can be deleted
        device = MagicMock(type="partition", isleaf=True, format=MagicMock(type=None))
        self.assertTrue(self.list_partitions._allow_delete_device(device))

        # only non-active swap can be deleted
        device = MagicMock(type="partition", isleaf=True, format=MagicMock(type="swap", status=True))
        self.assertFalse(self.list_partitions._allow_delete_device(device))
        device = MagicMock(type="partition", isleaf=True, format=MagicMock(type="swap", status=False))
        self.assertTrue(self.list_partitions._allow_delete_device(device))

        # only unmounted devices can be deleted
        device = MagicMock(type="partition", isleaf=True, format=MagicMock(type="lvmpv", mountable=False))
        self.assertTrue(self.list_partitions._allow_delete_device(device))
        device = MagicMock(type="partition", isleaf=True, format=MagicMock(type="ext4", mountable=True, status=False))
        self.assertTrue(self.list_partitions._allow_delete_device(device))
        device = MagicMock(type="partition", isleaf=True, format=MagicMock(type="ext4", mountable=True, status=True))
        self.assertFalse(self.list_partitions._allow_delete_device(device))

        # in kickstart mode, allow delete all leaves
        self.list_partitions.kickstart_mode=True
        device = MagicMock(type="partition", isleaf=True, format=MagicMock(type="swap", status=True))
        self.assertTrue(self.list_partitions._allow_delete_device(device))
        device = MagicMock(type="partition", isleaf=True, format=MagicMock(type="ext4", mountable=True, status=True))
        self.assertTrue(self.list_partitions._allow_delete_device(device))
        device = MagicMock(type="partition", isleaf=False)
        self.assertFalse(self.list_partitions._allow_delete_device(device))