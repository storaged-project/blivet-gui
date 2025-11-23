import unittest
from unittest.mock import MagicMock

from blivetgui.dialogs.size_chooser import SizeChooser, ParentChooser, ParentArea, SizeArea

import os

from blivet import size
from blivet.size import Size, unit_str
from blivet.devicelibs.raid import Single, Linear, RAID0, RAID1


@unittest.skipUnless("DISPLAY" in os.environ.keys(), "requires X server")
class SizeAreaTest(unittest.TestCase):

    def _mock_device(self, name="vda1", fmt_type=None):
        dev = MagicMock()
        fmt = MagicMock(type=fmt_type)
        dev.configure_mock(name=name, format=fmt)

        return dev

    def test_10_basic(self):
        """ Test basic SizeArea functionality """

        parents = [MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0))]

        # -- Partition -> no advanced selection
        size_area = SizeArea(device_type="partition", parents=parents,
                             min_limit=Size("1 MiB"), max_limit=Size("1 GiB"),
                             raid_type=None)

        # we need to get the checkbutton from builder
        checkbutton_manual = size_area._builder.get_object("checkbutton_manual")

        self.assertTrue(size_area.main_chooser.get_sensitive())
        self.assertFalse(checkbutton_manual.get_sensitive())
        self.assertFalse(checkbutton_manual.get_active())
        self.assertIsNone(size_area._parent_area)

        self.assertEqual(size_area.min_size, Size("1 MiB"))
        self.assertEqual(size_area.max_size, Size("1 GiB"))

        # try to update min size of all parents
        size_area.set_parents_min_size(Size("2 MiB"))
        self.assertEqual(size_area.min_size, Size("2 MiB"))
        self.assertEqual(size_area.parents[0].min_size, Size("2 MiB"))

        selection = size_area.get_selection()
        self.assertEqual(selection.total_size, size_area.main_chooser.selected_size)
        self.assertEqual(len(selection.parents), 1)
        self.assertEqual(selection.parents[0].parent_device, parents[0].device)
        self.assertEqual(selection.parents[0].selected_size, size_area.main_chooser.selected_size)

    def test_20_advanced_allowed(self):
        """ Test SizeArea functionality with ParentArea allowed """

        # -- Btrfs volume, no raid -> advanced allowed
        parents = [MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0)),
                   MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0))]

        size_area = SizeArea(device_type="btrfs volume", parents=parents,
                             min_limit=Size("1 MiB"), max_limit=Size("1 GiB"),
                             raid_type=Single)

        # we need to get the checkbutton from builder
        checkbutton_manual = size_area._builder.get_object("checkbutton_manual")

        self.assertTrue(size_area.main_chooser.get_sensitive())
        self.assertTrue(checkbutton_manual.get_sensitive())
        self.assertFalse(checkbutton_manual.get_active())
        self.assertIsNone(size_area._parent_area)

        # now select advanced
        checkbutton_manual.set_active(True)
        self.assertIsNotNone(size_area._parent_area)
        self.assertFalse(size_area.main_chooser.get_sensitive())

        selection = size_area.get_selection()
        self.assertEqual(selection.total_size, Size("2 GiB"))  # Single raid, total size is just sum of parents
        self.assertEqual(len(selection.parents), 2)
        self.assertEqual(selection.parents[0].parent_device, parents[0].device)
        self.assertEqual(selection.parents[0].selected_size, Size("1 GiB"))
        self.assertEqual(selection.parents[1].parent_device, parents[1].device)
        self.assertEqual(selection.parents[1].selected_size, Size("1 GiB"))

        # setting min size with advanced enabled sets min size for all choosers
        # resulting min size is then sum of the min sizes (with 'single' raid)
        size_area.set_parents_min_size(Size("2 MiB"))
        self.assertEqual(size_area.min_size, Size("4 MiB"))
        self.assertTrue(all(p.min_size == Size("2 MiB") for p in size_area.parents))

        size_area.set_parents_min_size(Size("1 MiB"))  # set it back for next test

        # now deselect it
        checkbutton_manual.set_active(False)
        self.assertIsNone(size_area._parent_area)
        self.assertTrue(size_area.main_chooser.get_sensitive())

        # single, main chooser max should be 2 GiB and min should be 2 MiB
        self.assertEqual(size_area.main_chooser.max_size, sum(p.max_size for p in parents))
        self.assertEqual(size_area.main_chooser.min_size, sum(p.min_size for p in parents))

        selection = size_area.get_selection()
        self.assertEqual(selection.total_size, size_area.main_chooser.selected_size)
        self.assertEqual(len(selection.parents), 2)
        self.assertEqual(selection.parents[0].parent_device, parents[0].device)
        self.assertEqual(selection.parents[0].selected_size, size_area.main_chooser.selected_size // 2)
        self.assertEqual(selection.parents[1].parent_device, parents[1].device)
        self.assertEqual(selection.parents[1].selected_size, size_area.main_chooser.selected_size // 2)

    def test_30_advanced_enforced(self):
        """ Test SizeArea functionality with ParentArea enforced """

        # -- MDRAID, raid1 -> advanced enforced
        parents = [MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0)),
                   MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0))]

        size_area = SizeArea(device_type="mdraid", parents=parents,
                             min_limit=Size("1 MiB"), max_limit=Size("1 GiB"),
                             raid_type=RAID1)

        # we need to get the checkbutton from builder
        checkbutton_manual = size_area._builder.get_object("checkbutton_manual")

        self.assertFalse(size_area.main_chooser.get_sensitive())
        self.assertFalse(checkbutton_manual.get_sensitive())
        self.assertTrue(checkbutton_manual.get_active())
        self.assertIsNotNone(size_area._parent_area)

        # raid1, main chooser max should be 1 GiB and min should be 1 MiB
        self.assertEqual(size_area.main_chooser.max_size, min(p.max_size for p in parents))
        self.assertEqual(size_area.main_chooser.min_size, min(p.min_size for p in parents))

        # setting min size with advanced enabled sets min size for all choosers
        # with raid1 resulting min size will still be 2 MiB (because it shows
        # 'usable' min size)
        size_area.set_parents_min_size(Size("2 MiB"))
        self.assertEqual(size_area.min_size, Size("2 MiB"))

        selection = size_area.get_selection()
        self.assertEqual(selection.total_size, Size("1 GiB"))  # RAID1 with two 1 GiB parents
        self.assertEqual(selection.parents[0].parent_device, parents[0].device)
        self.assertEqual(selection.parents[0].selected_size, Size("1 GiB"))
        self.assertEqual(selection.parents[1].parent_device, parents[1].device)
        self.assertEqual(selection.parents[1].selected_size, Size("1 GiB"))

    def test_40_basic_limits(self):
        """ Test SizeArea limits functionality without ParentArea """

        parents = [MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0)),
                   MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0))]

        size_area = SizeArea(device_type="lvm", parents=parents,
                             min_limit=Size(1), max_limit=Size("200 GiB"),
                             raid_type=None)

        # min size is based on both min size of the parents and limits
        # limits are smaller here, so parents' min size win
        self.assertEqual(size_area.min_size, sum(p.min_size for p in parents))

        # max size is based on both max size of the parents and limits
        # limits are bigger here, so parents' max size win
        self.assertEqual(size_area.max_size, sum(p.max_size for p in parents))

        # set min limits for parents -- this would happen e.g. when selecting
        # encryption ('parent partitions' needs to be bigger because of the
        # luks container)
        size_area.set_parents_min_size(Size("3 MiB"))

        self.assertEqual(size_area.min_size, Size("6 MiB"))  # 2 parents each min 3 MiB
        self.assertEqual(size_area.main_chooser.min_size, Size("6 MiB"))
        for parent in size_area.parents:
            self.assertEqual(parent.min_size, Size("3 MiB"))

        # now set 'global' min limit for the device -- this would happen e.g.
        # when changing filesystem type to btrfs (final btrfs volume has to be
        # at least 256 MiB big)
        size_area.min_size_limit = Size("256 MiB")
        self.assertEqual(size_area.min_size, Size("256 MiB"))
        self.assertEqual(size_area.main_chooser.min_size, Size("256 MiB"))

        # update parent min size to something smaller than current limit
        # min_size_limit is bigger so it should win
        size_area.set_parents_min_size(Size("10 MiB"))
        self.assertEqual(size_area.min_size, Size("256 MiB"))

        # update parent min size to something bigger than current limit
        size_area.set_parents_min_size(Size("200 MiB"))  # 2*200 > 256
        self.assertEqual(size_area.min_size, Size("400 MiB"))

        # now just try to set 'global' limit to something smaller
        # parent limit should win
        size_area.min_size_limit = Size("300 MiB")
        self.assertEqual(size_area.min_size, Size("400 MiB"))

        # ---------------------------------------------------------------------#
        # same for max size but there is no option to set max size for all
        # parents (because it depends on selected parent and its free space)
        # only setting max limit is supported
        size_area.max_size_limit = Size("500 MiB")
        self.assertEqual(size_area.max_size, Size("500 MiB"))
        self.assertEqual(size_area.main_chooser.max_size, Size("500 MiB"))

        # ---------------------------------------------------------------------#
        # invalid limits
        with self.assertRaises(ValueError):
            size_area.min_size_limit = Size("100 TiB")  # bigger than max size

        with self.assertRaises(ValueError):
            size_area.min_size_limit = Size(0)

        with self.assertRaises(ValueError):
            size_area.max_size_limit = Size(1)  # smaller tnan min size

        with self.assertRaises(ValueError):
            size_area.max_size_limit = Size(-10)  # smaller tnan min size

    def test_45_basic_limits_combined(self):
        """ Test SizeArea limits functionality without ParentArea """

        parents = [MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0)),
                   MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0))]

        size_area = SizeArea(device_type="lvm", parents=parents,
                             min_limit=Size(1), max_limit=Size("200 GiB"),
                             raid_type=None)

        # changing both limits at once
        size_area.set_size_limits(Size("100 MiB"), Size("1 GiB"))
        self.assertEqual(size_area.min_size, Size("100 MiB"))
        self.assertEqual(size_area.max_size, Size("1 GiB"))

        size_area.set_size_limits(Size("2 MiB"), Size("10 MiB"))
        self.assertEqual(size_area.min_size, Size("2 MiB"))
        self.assertEqual(size_area.max_size, Size("10 MiB"))

        size_area.set_size_limits(Size("100 MiB"), Size("200 MiB"))
        self.assertEqual(size_area.min_size, Size("100 MiB"))
        self.assertEqual(size_area.max_size, Size("200 MiB"))

        size_area.set_size_limits(Size("2 MiB"), Size("4 MiB"))
        self.assertEqual(size_area.min_size, Size("2 MiB"))
        self.assertEqual(size_area.max_size, Size("4 MiB"))

        size_area.set_size_limits(Size("10 MiB"), Size("10 MiB"))
        self.assertEqual(size_area.min_size, Size("10 MiB"))
        self.assertEqual(size_area.max_size, Size("10 MiB"))

        with self.assertRaises(ValueError):
            size_area.set_size_limits(Size("100 MiB"), Size("20 MiB"))

    def test_50_advanced_limits(self):
        """ Test SizeArea limits functionality with ParentArea """

        parents = [MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0)),
                   MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0))]

        size_area = SizeArea(device_type="lvmlv", parents=parents,
                             min_limit=Size(1), max_limit=Size("200 GiB"),
                             raid_type=Linear)

        # select advanced
        checkbutton_manual = size_area._builder.get_object("checkbutton_manual")
        checkbutton_manual.set_active(True)
        self.assertIsNotNone(size_area._parent_area)  # just to be sure

        # min size is based on both min size of the parents and limits
        # limits are smaller here, so parents' min size win
        self.assertEqual(size_area.min_size, sum(p.min_size for p in parents))

        # max size is based on both max size of the parents and limits
        # limits are bigger here, so parents' max size win
        self.assertEqual(size_area.max_size, sum(p.max_size for p in parents))

        # set same min size for all parents
        size_area.set_parents_min_size(Size("5 MiB"))

        self.assertEqual(size_area.min_size, Size("10 MiB"))  # 2 parents each min 5 MiB and Linear raid level
        for parent in size_area.parents:
            self.assertEqual(parent.min_size, Size("5 MiB"))
        for chooser in size_area._parent_area.choosers:
            self.assertEqual(chooser.min_size, Size("5 MiB"))

        # now set 'global' limit -- in this case, no UI elements are changed,
        # because this would be very hard for multiple parents with size choosers
        # and with different raid levels etc.; validation of user input should
        # fail instead
        size_area.min_size_limit = Size("256 MiB")

        valid, _reason = size_area.validate_user_input()
        self.assertTrue(valid)  # valid now, because default is max size

        self.assertEqual(size_area.min_size, Size("10 MiB"))  # min size shouldn't change
        for chooser in size_area._parent_area.choosers:
            chooser.selected_size = chooser.min_size  # set min size for all choosers
        self.assertEqual(size_area.main_chooser.selected_size, Size("10 MiB"))

        valid, _reason = size_area.validate_user_input()
        self.assertFalse(valid)  # too small, invalid

        # same for max limit; just set min_size_limit back
        size_area.min_size_limit = Size("1 MiB")

        max_pre = size_area.max_size
        size_area.max_size_limit = Size("500 MiB")
        self.assertEqual(size_area.max_size, max_pre)  # max size shouldn't change

        for chooser in size_area._parent_area.choosers:
            chooser.selected_size = chooser.max_size

        valid, _reason = size_area.validate_user_input()
        self.assertFalse(valid)  # invalid now, because max size > limit

        for chooser in size_area._parent_area.choosers:
            chooser.selected_size = chooser.min_size  # set min size for all choosers

        valid, _reason = size_area.validate_user_input()
        self.assertTrue(valid)  # valid now

    def test_50_advanced_limits_raid(self):
        """ Test SizeArea limits functionality with ParentArea with RAID """

        parents = [MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0)),
                   MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0))]

        size_area = SizeArea(device_type="lvmlv", parents=parents,
                             min_limit=Size(1), max_limit=Size("200 GiB"),
                             raid_type=RAID1)

        # advanced should be preselected
        self.assertIsNotNone(size_area._parent_area)

        # min size is based on both min size of the parents and limits
        # limits are smaller here, so parents' min size win (and it isn't sum
        # of all parents because of RAID1)
        self.assertEqual(size_area.min_size, min(p.min_size for p in parents))

        # max size is based on both max size of the parents and limits
        # limits are bigger here, so parents' max size win
        self.assertEqual(size_area.max_size, min(p.max_size for p in parents))

        # set same min size for all parents
        size_area.set_parents_min_size(Size("255 MiB"))

        self.assertEqual(size_area.min_size, Size("255 MiB"))  # 2 parents each min 2555 MiB and RAID1
        for parent in size_area.parents:
            self.assertEqual(parent.min_size, Size("255 MiB"))
        for chooser in size_area._parent_area.choosers:
            self.assertEqual(chooser.min_size, Size("255 MiB"))

        # now set 'global' limit -- in this case, no UI elements are changed,
        # because this would be very hard for multiple parents with size choosers
        # and with different raid levels etc.; validation of user input should
        # fail instead
        size_area.min_size_limit = Size("256 MiB")

        valid, _reason = size_area.validate_user_input()
        self.assertTrue(valid)  # valid now, because default is max size

        self.assertEqual(size_area.min_size, Size("255 MiB"))  # min size shouldn't change
        for chooser in size_area._parent_area.choosers:
            chooser.selected_size = chooser.min_size  # set min size for all choosers
        self.assertEqual(size_area.main_chooser.selected_size, Size("255 MiB"))

        valid, _reason = size_area.validate_user_input()
        self.assertFalse(valid)  # too small, invalid

    def test_60_reserved_size(self):
        """ Test SizeArea reserved size functionality without ParentArea """

        parents = [MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0)),
                   MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0))]

        size_area = SizeArea(device_type="lvm", parents=parents,
                             min_limit=Size(1), max_limit=Size("200 GiB"),
                             raid_type=None)

        # now set reserved size to 2 MiB
        size_area.set_parents_reserved_size(Size("2 MiB"))

        for parent in parents:
            self.assertEqual(parent.reserved_size, Size("2 MiB"))

        # min size should be 6 MiB now -- 2 * min_size + 2 * reserved_size
        self.assertEqual(size_area.min_size, Size("6 MiB"))

        # now set reserved size back to 0
        size_area.set_parents_reserved_size(Size(0))

        for parent in parents:
            self.assertEqual(parent.reserved_size, Size(0))

        # min size should be 2 MiB now -- just 2 * min_size
        self.assertEqual(size_area.min_size, Size("2 MiB"))

    def test_60_reserved_size_advanced(self):
        """ Test SizeArea reserved size functionality with ParentArea """

        parents = [MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0)),
                   MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0))]

        size_area = SizeArea(device_type="lvm", parents=parents,
                             min_limit=Size(1), max_limit=Size("200 GiB"),
                             raid_type=None)

        # select advanced
        checkbutton_manual = size_area._builder.get_object("checkbutton_manual")
        checkbutton_manual.set_active(True)
        self.assertIsNotNone(size_area._parent_area)  # just to be sure

        # now set reserved size to 2 MiB
        size_area.set_parents_reserved_size(Size("2 MiB"))

        for parent in parents:
            self.assertEqual(parent.reserved_size, Size("2 MiB"))

        # 'total' min size should be 6 MiB now -- 2 * min_size + 2 * reserved_size
        self.assertEqual(size_area.min_size, Size("6 MiB"))

        # min size per parent should 3 MiB -- 1 MiB for min_size and 2 MiB for reserved_size
        for chooser in size_area._parent_area.choosers:
            self.assertEqual(chooser.reserved_size, Size("2 MiB"))
            self.assertEqual(chooser.min_size, Size("3 MiB"))

        # now set reserved size back to 0
        size_area.set_parents_reserved_size(Size(0))

        for parent in parents:
            self.assertEqual(parent.reserved_size, Size(0))

        # 'total' min size should be 2 MiB now -- just 2 * min_size
        self.assertEqual(size_area.min_size, Size("2 MiB"))

        # min size per parent should 1 MiB -- just 1 MiB for min_size
        for chooser in size_area._parent_area.choosers:
            self.assertEqual(chooser.reserved_size, Size(0))
            self.assertEqual(chooser.min_size, Size("1 MiB"))

    def test_70_parent_allocation(self):
        """ Test allocating size on parents without ParentArea """

        # -- same size parents
        parents = [MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0)),
                   MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0))]

        size_area = SizeArea(device_type="lvm", parents=parents,
                             min_limit=Size(1), max_limit=Size("200 GiB"),
                             raid_type=None)

        # select maximum --> both parents should have max_size selected
        size_area.main_chooser.selected_size = Size("2 GiB")
        ret = size_area._get_parents_allocation()
        self.assertEqual(ret[0].parent_device, parents[0].device)
        self.assertEqual(ret[0].selected_size, parents[0].max_size)
        self.assertEqual(ret[1].parent_device, parents[1].device)
        self.assertEqual(ret[1].selected_size, parents[1].max_size)

        # -- two parents 1 GiB and 2 GiB
        parents = [MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0)),
                   MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("2 GiB"),
                             reserved_size=Size(0))]

        size_area = SizeArea(device_type="lvm", parents=parents,
                             min_limit=Size(1), max_limit=Size("200 GiB"),
                             raid_type=None)

        # select 2 GiB --> 1 GiB on both should be selected
        size_area.main_chooser.selected_size = Size("2 GiB")
        ret = size_area._get_parents_allocation()
        self.assertEqual(ret[0].parent_device, parents[0].device)
        self.assertEqual(ret[0].selected_size, parents[0].max_size)
        self.assertEqual(ret[1].parent_device, parents[1].device)
        self.assertEqual(ret[1].selected_size, Size("1 GiB"))

        # select 100 MiB --> 50 MiB on both should be selected
        size_area.main_chooser.selected_size = Size("100 MiB")
        ret = size_area._get_parents_allocation()
        self.assertEqual(ret[0].parent_device, parents[0].device)
        self.assertEqual(ret[0].selected_size, Size("50 MiB"))
        self.assertEqual(ret[1].parent_device, parents[1].device)
        self.assertEqual(ret[1].selected_size, Size("50 MiB"))

        # -- three parents 1 GiB, 2 GiB and 5 GiB
        parents = [MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0)),
                   MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("2 GiB"),
                             reserved_size=Size(0)),
                   MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("5 GiB"),
                             reserved_size=Size(0))]

        size_area = SizeArea(device_type="lvm", parents=parents,
                             min_limit=Size(1), max_limit=Size("200 GiB"),
                             raid_type=None)

        # select 3 GiB --> 1 GiB on both should be selected
        size_area.main_chooser.selected_size = Size("3 GiB")
        ret = size_area._get_parents_allocation()
        selected_sizes = [r.selected_size for r in ret]

        # with 3 parents result might be in different order, so just check
        # sequence of the sizes and that none of the parents has bigger selected
        # size than its max size
        self.assertListEqual(selected_sizes, [Size("1 GiB"), Size("1 GiB"), Size("1 GiB")])
        for parent in parents:
            for r in ret:
                if parent.device == r.parent_device:
                    self.assertLessEqual(r.selected_size, parent.max_size)

        # select 1 GiB --> 1/3 GiB on all should be selected (one will be 1/3 + rest)
        size_area.main_chooser.selected_size = Size("1 GiB")
        ret = size_area._get_parents_allocation()
        selected_sizes = [r.selected_size for r in ret]

        # with 3 parents result might be in different order, so just check
        # sequence of the sizes and that none of the parents has bigger selected
        # size than its max size
        self.assertListEqual(selected_sizes, [Size("1 GiB") / 3, Size("1 GiB") / 3, Size("1 GiB") - 2 * Size("1 GiB") / 3])
        for parent in parents:
            for r in ret:
                if parent.device == r.parent_device:
                    self.assertLessEqual(r.selected_size, parent.max_size)

        # select 7 GiB --> 1, 2 and 4 GiB should be selected
        size_area.main_chooser.selected_size = Size("7 GiB")
        ret = size_area._get_parents_allocation()
        selected_sizes = [r.selected_size for r in ret]

        # with 3 parents result might be in different order, so just check
        # sequence of the sizes and that none of the parents has bigger selected
        # size than its max size
        self.assertListEqual(selected_sizes, [Size("1 GiB"), Size("2 GiB"), Size("4 GiB")])
        for parent in parents:
            for r in ret:
                if parent.device == r.parent_device:
                    self.assertLessEqual(r.selected_size, parent.max_size)

        # -- just some crazy corner case
        parents = [MagicMock(device=self._mock_device(), min_size=Size(1), max_size=Size("1 GiB"),
                             reserved_size=Size(0)),
                   MagicMock(device=self._mock_device(), min_size=Size(1), max_size=Size("1 GiB"),
                             reserved_size=Size(0))]

        size_area = SizeArea(device_type="lvm", parents=parents,
                             min_limit=Size(1), max_limit=Size("200 GiB"),
                             raid_type=None)

        # select 3 and see how it will be divided between 2 devices
        size_area.main_chooser.selected_size = Size(3)
        ret = size_area._get_parents_allocation()
        selected_sizes = [r.selected_size for r in ret]
        self.assertListEqual(selected_sizes, [Size(1), Size(2)])

    def test_75_parent_allocation_overprovisioning(self):
        """ Test allocating size on parents without ParentArea with overprovisioning """

        # -- same size parents
        parents = [MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0)),
                   MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0))]

        size_area = SizeArea(device_type="lvm", parents=parents,
                             min_limit=Size(1), max_limit=Size("200 GiB"),
                             raid_type=None, overprovisioning=True)

        # select maximum (bigger than parents) --> both parents should have max_limit selected
        size_area.main_chooser.selected_size = Size("200 GiB")
        ret = size_area.get_selection()
        self.assertEqual(len(ret.parents), 2)
        self.assertEqual(ret.parents[0].parent_device, parents[0].device)
        self.assertEqual(ret.parents[0].selected_size, Size("200 GiB"))
        self.assertEqual(ret.parents[1].parent_device, parents[1].device)
        self.assertEqual(ret.parents[1].selected_size, Size("200 GiB"))


@unittest.skipUnless("DISPLAY" in os.environ.keys(), "requires X server")
class ParentAreaTest(unittest.TestCase):

    def _mock_device(self, name="vda1", fmt_type=None):
        dev = MagicMock()
        fmt = MagicMock(type=fmt_type)
        dev.configure_mock(name=name, format=fmt)

        return dev

    def test_10_basic(self):
        """ Test basic ParentArea functionality """

        # -- MDRAID
        main_chooser = MagicMock()
        parents = [MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0)),
                   MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0))]

        parent_area = ParentArea(device_type="mdraid", parents=parents, raid_type=RAID0,
                                 main_chooser=main_chooser)

        # two choosers, both should be selected (and not selectable) with given min and max size
        self.assertEqual(len(parent_area.choosers), 2)
        self.assertListEqual(parent_area.choosers, parent_area.selected_choosers)

        for idx, chooser in enumerate(parent_area.choosers):
            self.assertTrue(chooser.selected)
            self.assertFalse(chooser.checkbutton_use.get_sensitive())
            self.assertTrue(chooser.size_chooser.get_sensitive())
            self.assertEqual(chooser.min_size, parents[idx].min_size)
            self.assertEqual(chooser.max_size, parents[idx].max_size)
            self.assertEqual(chooser.selected_size, parents[idx].max_size)

        # test area size limits
        self.assertEqual(parent_area.total_max, sum(p.max_size for p in parents))
        self.assertEqual(parent_area.total_min, sum(p.min_size for p in parents))
        self.assertEqual(parent_area.total_size, sum(p.max_size for p in parents))

        # -- LVM (with both free space and lvmpv parents)
        main_chooser = MagicMock()
        parents = [MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0)),
                   MagicMock(device=self._mock_device(fmt_type="lvmpv"), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0))]

        parent_area = ParentArea(device_type="lvm", parents=parents, raid_type=None,
                                 main_chooser=main_chooser)

        # two choosers, both should be selected (and not selectable) with given min and max size
        self.assertEqual(len(parent_area.choosers), 2)
        self.assertListEqual(parent_area.choosers, parent_area.selected_choosers)

        for idx, chooser in enumerate(parent_area.choosers):
            self.assertTrue(chooser.selected)
            self.assertFalse(chooser.checkbutton_use.get_sensitive())
            self.assertEqual(chooser.min_size, parents[idx].min_size)
            self.assertEqual(chooser.max_size, parents[idx].max_size)
            self.assertEqual(chooser.selected_size, parents[idx].max_size)

        # test area size limits
        self.assertEqual(parent_area.total_max, sum(p.max_size for p in parents))
        self.assertEqual(parent_area.total_min, sum(p.min_size for p in parents))
        self.assertEqual(parent_area.total_size, sum(p.max_size for p in parents))

        # size should be selectable just for the free space, not for the PV
        self.assertTrue(parent_area.choosers[0].size_chooser.get_sensitive())
        self.assertFalse(parent_area.choosers[1].size_chooser.get_sensitive())

    def test_20_parent_selection(self):
        """ Test ParentArea functionality when (de)selecting some parents """

        main_chooser = MagicMock()
        parents = [MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"), reserved_size=Size(0)),
                   MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"), reserved_size=Size(0)),
                   MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"), reserved_size=Size(0))]

        # RAID LV is the only device type that allows changing parent selection
        parent_area = ParentArea(device_type="lvmlv", parents=parents, raid_type=RAID0,
                                 main_chooser=main_chooser)

        # three choosers, all should be selected (and selectable) with given min and max size
        self.assertEqual(len(parent_area.choosers), 3)

        for idx, chooser in enumerate(parent_area.choosers):
            self.assertTrue(chooser.selected)
            self.assertTrue(chooser.checkbutton_use.get_sensitive())
            self.assertEqual(chooser.min_size, parents[idx].min_size)
            self.assertEqual(chooser.max_size, parents[idx].max_size)
            self.assertEqual(chooser.selected_size, parents[idx].max_size)

        # test area size limits
        self.assertEqual(parent_area.total_max, sum(p.max_size for p in parents))
        self.assertEqual(parent_area.total_min, sum(p.min_size for p in parents))
        self.assertEqual(parent_area.total_size, sum(p.max_size for p in parents))

        # try to deselect first parent
        # after it, shouldn't be possible to deselect more parents -> not enough
        # members for RAID0
        parent_area.choosers[0].selected = False
        self.assertEqual(parent_area.total_max, sum(p.max_size for p in parents[1:]))
        self.assertEqual(parent_area.total_min, sum(p.min_size for p in parents[1:]))
        self.assertEqual(parent_area.total_size, sum(p.max_size for p in parents[1:]))

        self.assertFalse(parent_area.choosers[1].parent_selectable)
        self.assertFalse(parent_area.choosers[2].parent_selectable)

        # select first parent again, everything should be back to normal
        parent_area.choosers[0].selected = True
        self.assertTrue(parent_area.choosers[1].parent_selectable)
        self.assertTrue(parent_area.choosers[2].parent_selectable)

    def test_30_size_selection(self):
        """ Test ParentArea functionality when changing size of some parents """

        main_chooser = MagicMock()
        parents = [MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0)),
                   MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0))]

        parent_area = ParentArea(device_type="mdraid", parents=parents, raid_type=RAID0,
                                 main_chooser=main_chooser)

        # change size of first chooser, second should be automatically adjusted
        parent_area.choosers[0].selected_size = Size("500 MiB")
        self.assertEqual(parent_area.choosers[1].selected_size, Size("500 MiB"))

    def test_40_main_update(self):
        """ Test updating values of main chooser in SizeArea """

        # -- MDRAID
        main_chooser = SizeChooser(max_size=Size("2 GiB"), min_size=Size("1 MiB"))
        parents = [MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0)),
                   MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0))]

        parent_area = ParentArea(device_type="mdraid", parents=parents, raid_type=RAID1,
                                 main_chooser=main_chooser)

        # raid1, main chooser max should be 1 GiB and min should be 1 MiB
        self.assertEqual(parent_area.main_chooser.max_size, min(p.max_size for p in parents))
        self.assertEqual(parent_area.main_chooser.min_size, min(p.min_size for p in parents))

        # set new size, parent area should be updated
        parent_area.choosers[0].selected_size = Size("500 MiB")
        self.assertEqual(parent_area.main_chooser.selected_size, Size("500 MiB"))

        # -- LVM RAID
        main_chooser = SizeChooser(max_size=Size("3 GiB"), min_size=Size("1 MiB"))
        parents = [MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"), reserved_size=Size(0)),
                   MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"), reserved_size=Size(0)),
                   MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"), reserved_size=Size(0))]

        parent_area = ParentArea(device_type="lvmlv", parents=parents, raid_type=RAID0,
                                 main_chooser=main_chooser)

        # raid0, main chooser max should be 3 GiB and min should be 3 MiB
        self.assertEqual(parent_area.main_chooser.max_size, sum(p.max_size for p in parents))
        self.assertEqual(parent_area.main_chooser.min_size, sum(p.min_size for p in parents))

        # deselect one parent -- max should be 2 GiB and min should be 2 MiB
        parent_area.choosers[0].selected = False
        self.assertEqual(parent_area.main_chooser.max_size, sum(p.max_size for p in parents[1:]))
        self.assertEqual(parent_area.main_chooser.min_size, sum(p.min_size for p in parents[1:]))

    def test_50_selected(self):
        """ Test if widget returns what user selected """

        # -- MDRAID, simple selection, all parents, just size adjusted
        main_chooser = MagicMock()
        parents = [MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0)),
                   MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0))]

        parent_area = ParentArea(device_type="mdraid", parents=parents, raid_type=RAID0,
                                 main_chooser=main_chooser)

        parent_area.choosers[0].selected_size = Size("500 MiB")
        selection = parent_area.get_selection()
        self.assertEqual(selection.total_size, Size("1000 MiB"))  # RAID 0 with two 500 MiB parents
        self.assertEqual(selection.parents[0].parent_device, parents[0].device)
        self.assertEqual(selection.parents[0].selected_size, Size("500 MiB"))
        self.assertEqual(selection.parents[1].parent_device, parents[1].device)
        self.assertEqual(selection.parents[1].selected_size, Size("500 MiB"))

        # -- Btrfs volume,  size can be changed separately for all parents
        main_chooser = MagicMock()
        parents = [MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0)),
                   MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                             reserved_size=Size(0))]

        parent_area = ParentArea(device_type="btrfs volume", parents=parents, raid_type=Single,
                                 main_chooser=main_chooser)

        parent_area.choosers[0].selected_size = Size("500 MiB")
        parent_area.choosers[1].selected_size = Size("750 MiB")
        selection = parent_area.get_selection()
        self.assertEqual(selection.total_size, Size("1250 MiB"))  # single with 500 MiB and 750 MiB parents
        self.assertEqual(selection.parents[0].parent_device, parents[0].device)
        self.assertEqual(selection.parents[0].selected_size, Size("500 MiB"))
        self.assertEqual(selection.parents[1].parent_device, parents[1].device)
        self.assertEqual(selection.parents[1].selected_size, Size("750 MiB"))

        # -- LVM RAID, allows parent selection
        main_chooser = MagicMock()
        parents = [MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"), reserved_size=Size(0)),
                   MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"), reserved_size=Size(0)),
                   MagicMock(device=self._mock_device(), min_size=Size("1 MiB"), max_size=Size("1 GiB"), reserved_size=Size(0))]

        parent_area = ParentArea(device_type="lvmlv", parents=parents, raid_type=RAID0,
                                 main_chooser=main_chooser)

        parent_area.choosers[0].selected = False
        parent_area.choosers[1].selected_size = Size("500 MiB")
        selection = parent_area.get_selection()
        self.assertEqual(selection.total_size, Size("1000 MiB"))  # RAID0 with two 500 MiB parents
        self.assertEqual(selection.parents[0].parent_device, parents[1].device)
        self.assertEqual(selection.parents[0].selected_size, Size("500 MiB"))
        self.assertEqual(selection.parents[1].parent_device, parents[2].device)
        self.assertEqual(selection.parents[1].selected_size, Size("500 MiB"))


@unittest.skipUnless("DISPLAY" in os.environ.keys(), "requires X server")
class ParentChooserTest(unittest.TestCase):

    def test_10_basic(self):
        """ Test basic ParentChooser functionality """
        parent = MagicMock()
        parent.configure_mock(name="vda")
        free = MagicMock()

        chooser = ParentChooser(parent=parent, free_space=free,
                                min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                                reserved_size=Size(0), selected=True, parent_selectable=False,
                                size_selectable=True)
        self.assertEqual(chooser.min_size, Size("1 MiB"))
        self.assertEqual(chooser.max_size, Size("1 GiB"))

        # checkbutton should be selected and insensitive
        self.assertTrue(chooser.checkbutton_use.get_active())
        self.assertFalse(chooser.checkbutton_use.get_sensitive())

        # size chooser should be sensitive
        self.assertTrue(chooser.size_chooser.get_sensitive())

    def test_20_selection(self):
        """ Test (de)selecting parent """
        parent = MagicMock()
        parent.configure_mock(name="vda")
        free = MagicMock()

        chooser = ParentChooser(parent=parent, free_space=free,
                                min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                                reserved_size=Size(0), selected=True, parent_selectable=True,
                                size_selectable=True)

        # checkbutton should be selected and sensitive
        self.assertTrue(chooser.checkbutton_use.get_active())
        self.assertTrue(chooser.checkbutton_use.get_sensitive())

        # deselect -- size chooser should be insensitive and set to 0
        chooser.selected = False

        self.assertFalse(chooser.checkbutton_use.get_active())
        self.assertFalse(chooser.size_chooser.get_sensitive())
        self.assertEqual(chooser.size_chooser.min_size, 0)
        self.assertEqual(chooser.size_chooser.selected_size, 0)

        # and select again -- size chooser should be sensitive and set to max
        chooser.selected = True

        self.assertTrue(chooser.checkbutton_use.get_active())
        self.assertTrue(chooser.size_chooser.get_sensitive())
        self.assertEqual(chooser.size_chooser.min_size, chooser.min_size)
        self.assertEqual(chooser.size_chooser.selected_size, chooser.max_size)

        # and now deselect and select again using the button
        chooser.checkbutton_use.set_active(False)
        self.assertFalse(chooser.selected)

        chooser.checkbutton_use.set_active(True)
        self.assertTrue(chooser.selected)

    def test_30_size_selection(self):
        """ Test changing size selection """
        parent = MagicMock()
        parent.configure_mock(name="vda")
        free = MagicMock()

        chooser = ParentChooser(parent=parent, free_space=free,
                                min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                                reserved_size=Size(0), selected=True, parent_selectable=False,
                                size_selectable=True)

        # by default max size should be selected
        self.assertEqual(chooser.selected_size, Size("1 GiB"))

        # select some different size
        chooser.selected_size = Size("500 MiB")
        self.assertEqual(chooser.selected_size, Size("500 MiB"))

    def test_40_limits(self):
        """ Test setting limits (min/max size) """
        parent = MagicMock()
        parent.configure_mock(name="vda")
        free = MagicMock()

        chooser = ParentChooser(parent=parent, free_space=free,
                                min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                                reserved_size=Size(0), selected=True, parent_selectable=False,
                                size_selectable=True)

        # select max size and set new max size bigger (selection shouldn't change)
        chooser.selected_size = chooser.max_size
        size_before = chooser.selected_size
        chooser.max_size = Size("2 GiB")
        self.assertEqual(chooser.size_chooser.max_size, Size("2 GiB"))
        self.assertEqual(chooser.selected_size, size_before)

        # select max size and set new max size smaller (selection should be adjusted)
        chooser.selected_size = chooser.max_size
        chooser.max_size = Size("500 MiB")
        self.assertEqual(chooser.size_chooser.max_size, Size("500 MiB"))
        self.assertEqual(chooser.selected_size, Size("500 MiB"))

        # select min size and set new min size smaller (selection shouldn't change)
        chooser.selected_size = chooser.min_size
        size_before = chooser.selected_size
        chooser.min_size = Size("1 KiB")
        self.assertEqual(chooser.size_chooser.min_size, Size("1 KiB"))
        self.assertEqual(chooser.selected_size, size_before)

        # select min size and set new min size bigger (selection should be adjusted)
        chooser.selected_size = chooser.min_size
        chooser.min_size = Size("2 MiB")
        self.assertEqual(chooser.size_chooser.min_size, Size("2 MiB"))
        self.assertEqual(chooser.selected_size, Size("2 MiB"))

    def test_50_signals(self):
        """ Test connecting signals and signal handling """
        parent = MagicMock()
        parent.configure_mock(name="vda")
        free = MagicMock()

        chooser = ParentChooser(parent=parent, free_space=free,
                                min_size=Size("1 MiB"), max_size=Size("1 GiB"),
                                reserved_size=Size(0), selected=True, parent_selectable=True,
                                size_selectable=True)

        parent_handler = MagicMock()
        size_handler1 = MagicMock()
        size_handler2 = MagicMock()

        chooser.connect("parent-toggled", parent_handler)
        chooser.connect("size-changed", size_handler1)
        chooser.connect("size-changed", size_handler2)

        # parent selection
        chooser.checkbutton_use.set_active(False)
        parent_handler.assert_called_with(False)

        # size selection
        chooser.size_chooser._scale.set_value(512)
        size_handler1.assert_called_with(Size("512 MiB"))
        size_handler2.assert_called_with(Size("512 MiB"))


@unittest.skipUnless("DISPLAY" in os.environ.keys(), "requires X server")
class SizeChooserAreaTest(unittest.TestCase):

    def setUp(self):
        self.size_chooser = SizeChooser(max_size=Size("100 GiB"), min_size=Size("1 MiB"))

    def test_10_unit_change(self):
        original_size = self.size_chooser.selected_size

        for idx, unit in enumerate(self.size_chooser.available_units):
            self.size_chooser._unit_chooser.set_active(idx)
            self.assertEqual(unit_str(unit), unit_str(self.size_chooser.selected_unit))

            new_size = Size(str(self.size_chooser._spin.get_value()) + " " + unit_str(unit))
            self.assertEqual(original_size, new_size)

    def test_20_scale_spin(self):
        old_value = self.size_chooser._scale.get_value()
        new_value = old_value // 2

        self.size_chooser._scale.set_value(new_value)
        self.assertEqual(new_value, self.size_chooser._spin.get_value())

        self.size_chooser._spin.set_value(old_value)
        self.assertEqual(old_value, self.size_chooser._scale.get_value())

    def test_30_get_size(self):
        selected_size = Size(str(self.size_chooser._spin.get_value()) + " " + unit_str(self.size_chooser.selected_unit))
        self.assertEqual(selected_size, self.size_chooser.selected_size)

    def test_40_set_size(self):
        selected_size = (self.size_chooser.max_size - self.size_chooser.min_size) // 2
        self.size_chooser.selected_size = selected_size
        self.assertEqual(selected_size, self.size_chooser.selected_size)

        with self.assertRaises(ValueError):
            self.size_chooser.selected_size = self.size_chooser.min_size - 1  # not between min and max

        with self.assertRaises(ValueError):
            self.size_chooser.selected_size = self.size_chooser.max_size + 1  # not between min and max

    def test_50_set_limits(self):
        self.size_chooser.min_size = Size("2 MiB")
        self.assertEqual(self.size_chooser.min_size, Size("2 MiB"))

        with self.assertRaises(ValueError):
            self.size_chooser.min_size = self.size_chooser.max_size + 1  # bigger than max

        self.size_chooser.max_size = Size("200 GiB")
        self.assertEqual(self.size_chooser.max_size, Size("200 GiB"))

        with self.assertRaises(ValueError):
            self.size_chooser.max_size = self.size_chooser.min_size - 1  # smaller than min

        self.size_chooser.selected_size = Size("50 GiB")  # selection should be preserved
        self.size_chooser.update_size_limits(min_size=Size("5 MiB"), max_size=Size("75 GiB"))
        self.assertEqual(self.size_chooser.min_size, Size("5 MiB"))
        self.assertEqual(self.size_chooser.max_size, Size("75 GiB"))
        self.assertEqual(self.size_chooser.selected_size, Size("50 GiB"))

    def test_60_widget_status(self):
        self.size_chooser.hide()
        for widget in self.size_chooser.widgets:
            if hasattr(widget, "get_visible"):
                self.assertFalse(widget.get_visible())

        self.size_chooser.show()
        for widget in self.size_chooser.widgets:
            if hasattr(widget, "get_visible"):
                self.assertTrue(widget.get_visible())

        self.size_chooser.set_sensitive(False)
        for widget in self.size_chooser.widgets:
            if hasattr(widget, "get_sensitive"):
                self.assertFalse(widget.get_sensitive())

        self.size_chooser.set_sensitive(True)
        for widget in self.size_chooser.widgets:
            if hasattr(widget, "get_sensitive"):
                self.assertTrue(widget.get_sensitive())

    def test_70_signals(self):
        unit_handler = MagicMock()
        size_handler1 = MagicMock()
        size_handler2 = MagicMock()

        self.size_chooser.connect("unit-changed", unit_handler)
        self.size_chooser.connect("size-changed", size_handler1)
        self.size_chooser.connect("size-changed", size_handler2, "foo")

        with self.assertRaises(ValueError):
            self.size_chooser.connect("non-existing-signal", None)

        # parent selection
        self.size_chooser._unit_chooser.set_active(self.size_chooser.available_units.index(size.KiB))
        unit_handler.assert_called_with(size.KiB)

        # size selection
        old_value = self.size_chooser._scale.get_value()
        new_value = old_value // 2
        self.size_chooser._scale.set_value(new_value)

        size_handler1.assert_called_with(self.size_chooser.selected_size)
        size_handler2.assert_called_with(self.size_chooser.selected_size, "foo")

    def test_80_selection(self):
        self.size_chooser.selected_size = Size("125 MiB")

        selection = self.size_chooser.get_selection()
        self.assertEqual(selection, Size("125 MiB"))

    def test_90_available_units(self):
        # max device size is 100 GiB (100 GiB - 1 MiB), units up to GiB should
        # be available and default should be GiB
        chooser = SizeChooser(max_size=Size("100 GiB"), min_size=Size("1 MiB"))
        self.assertCountEqual(chooser.available_units,
                              [size.B, size.KB, size.KiB, size.MB, size.MiB, size.GB, size.GiB])
        self.assertEqual(chooser.default_unit, size.GiB)

        # max device size is 3 GiB, units up to GiB should
        # be available and default should be MiB
        chooser = SizeChooser(max_size=Size("3 GiB"), min_size=Size("1 MiB"))
        self.assertCountEqual(chooser.available_units,
                              [size.B, size.KB, size.KiB, size.MB, size.MiB, size.GB, size.GiB])
        self.assertEqual(chooser.default_unit, size.MiB)

        # max device size is 10 MiB, units up to MiB should
        # be available and default should be MiB
        chooser = SizeChooser(max_size=Size("11 MiB"), min_size=Size("1 MiB"))
        self.assertCountEqual(chooser.available_units,
                              [size.B, size.KB, size.KiB, size.MB, size.MiB])
        self.assertEqual(chooser.default_unit, size.MiB)

        # max device size is 10 KiB, units up to KiB should
        # be available and default should be KiB
        chooser = SizeChooser(max_size=Size("11 KiB"), min_size=Size("1 KiB"))
        self.assertCountEqual(chooser.available_units, [size.B, size.KB, size.KiB])
        self.assertEqual(chooser.default_unit, size.KiB)

        # min and max device size is same, units should depend on the max size
        chooser = SizeChooser(max_size=Size("11 KiB"), min_size=Size("11 KiB"))
        self.assertCountEqual(chooser.available_units, [size.B, size.KB, size.KiB])
        self.assertEqual(chooser.default_unit, size.KiB)

        # max size is just 1 B bigger than min size -> only B should be available
        chooser = SizeChooser(max_size=Size("11 KiB") + Size("1 B"), min_size=Size("11 KiB"))
        self.assertCountEqual(chooser.available_units, [size.B])
        self.assertEqual(chooser.default_unit, size.B)

        # max size is just 2 B bigger than min size -> only B should be available
        chooser = SizeChooser(max_size=Size("11 KiB") + Size("2 B"), min_size=Size("11 KiB"))
        self.assertCountEqual(chooser.available_units, [size.B])
        self.assertEqual(chooser.default_unit, size.B)


if __name__ == "__main__":
    unittest.main()
