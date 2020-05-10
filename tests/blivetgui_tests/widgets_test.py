# -*- coding: utf-8 -*-

import os
import unittest

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk

from blivet.devicelibs.raid import RAID0, RAID1, RAID5, Single, Linear
from blivet.devicelibs import crypto
from blivetgui.dialogs.widgets import RaidChooser, EncryptionChooser
from blivetgui.i18n import _


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


@unittest.skipUnless("DISPLAY" in os.environ.keys(), "requires X server")
class EncryptionChooserTest(unittest.TestCase):

    def test_encrypt_validity_check(self):
        encrypt_chooser = EncryptionChooser()

        # passphrases specified and matches
        encrypt_chooser.encrypt = True
        encrypt_chooser._passphrase_entry.set_text("aaaaa")
        encrypt_chooser._repeat_entry.set_text("aaaaa")
        succ, msg = encrypt_chooser.validate_user_input()
        self.assertTrue(succ)
        self.assertIsNone(msg)

        # passphrases specified but don't match
        encrypt_chooser.encrypt = True
        encrypt_chooser._passphrase_entry.set_text("aaaaa")
        encrypt_chooser._repeat_entry.set_text("bbbb")
        succ, msg = encrypt_chooser.validate_user_input()
        self.assertFalse(succ)
        self.assertEqual(msg, _("Provided passphrases do not match."))

        # no passphrase specified
        encrypt_chooser.encrypt = True
        encrypt_chooser._passphrase_entry.set_text("")
        succ, msg = encrypt_chooser.validate_user_input()
        self.assertFalse(succ)
        self.assertEqual(msg, _("Passphrase not specified."))

    def test_encryption_selection(self):
        encrypt_chooser = EncryptionChooser()

        encrypt_chooser.encrypt = True
        encrypt_chooser._passphrase_entry.set_text("aaaaa")
        encrypt_chooser._repeat_entry.set_text("aaaaa")

        user_input = encrypt_chooser.get_selection()
        self.assertEqual(user_input.encrypt, True)
        self.assertEqual(user_input.passphrase, "aaaaa")
        self.assertEqual(user_input.encryption_type, crypto.DEFAULT_LUKS_VERSION)

    def test_encryption_chooser(self):
        encrypt_chooser = EncryptionChooser()

        encrypt_chooser.encrypt = True
        self.assertTrue(encrypt_chooser._passphrase_entry.get_visible())
        self.assertTrue(encrypt_chooser._repeat_entry.get_visible())

        # check the encrypt check, passphrase entries should be hidden
        encrypt_chooser.encrypt = False
        self.assertFalse(encrypt_chooser._passphrase_entry.get_visible())
        self.assertFalse(encrypt_chooser._repeat_entry.get_visible())

    def test_passphrase_entry(self):
        encrypt_chooser = EncryptionChooser()

        encrypt_chooser.encrypt = True

        # passphrases don't match -> error icon
        encrypt_chooser._passphrase_entry.set_text("aa")
        encrypt_chooser._repeat_entry.set_text("bb")
        self.assertEqual(encrypt_chooser._repeat_entry.get_icon_name(Gtk.EntryIconPosition.SECONDARY), "dialog-error-symbolic")

        # passphrases match -> ok icon
        encrypt_chooser._repeat_entry.set_text("aa")
        self.assertEqual(encrypt_chooser._repeat_entry.get_icon_name(Gtk.EntryIconPosition.SECONDARY), "emblem-ok-symbolic")


if __name__ == "__main__":
    unittest.main()
