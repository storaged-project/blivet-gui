import unittest
from unittest.mock import patch

from blivetgui.dialogs.helpers import is_name_valid, is_label_valid, is_mountpoint_valid
from blivetgui.i18n import _


class DialogHelpersTest(unittest.TestCase):

    def test_name_valid(self):
        with patch("blivetgui.dialogs.helpers.lvm.is_lvm_name_valid", return_value=False):
            valid = is_name_valid("lvmvg", "test")
            self.assertFalse(valid)

        with patch("blivetgui.dialogs.helpers.lvm.is_lvm_name_valid", return_value=True):
            valid = is_name_valid("lvmvg", "test")
            self.assertTrue(valid)

        with patch("blivetgui.dialogs.helpers.btrfs.is_btrfs_name_valid", return_value=False):
            valid = is_name_valid("btrfs volume", "test")
            self.assertFalse(valid)

        with patch("blivetgui.dialogs.helpers.btrfs.is_btrfs_name_valid", return_value=True):
            valid = is_name_valid("btrfs volume", "test")
            self.assertTrue(valid)

    def test_label_valid(self):
        with patch("blivetgui.dialogs.helpers.Ext2FSLabeling.label_format_ok", return_value=False):
            valid = is_label_valid("ext4", "test")
            self.assertFalse(valid)

        with patch("blivetgui.dialogs.helpers.Ext2FSLabeling.label_format_ok", return_value=True):
            valid = is_label_valid("ext4", "test")
            self.assertTrue(valid)

    def test_mountpoint_valid(self):
        # valid mount point
        valid, msg = is_mountpoint_valid([], "/", None)
        self.assertTrue(valid)
        self.assertIsNone(msg)

        # invalid path
        valid, msg = is_mountpoint_valid([], "test", None)
        self.assertFalse(valid)
        self.assertEqual(msg, _("\"{0}\" is not a valid mountpoint.").format("test"))

        # same mount point as before (valid)
        valid, msg = is_mountpoint_valid(["/"], "/", "/")
        self.assertTrue(valid)
        self.assertIsNone(msg)

        # mount point already in use
        valid, msg = is_mountpoint_valid(["/"], "/", None)
        self.assertFalse(valid)
        self.assertEqual(msg, _("Selected mountpoint \"{0}\" is already set for another device.").format("/"))


if __name__ == "__main__":
    unittest.main()
