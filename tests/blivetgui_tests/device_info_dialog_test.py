import os
import unittest
from unittest.mock import MagicMock

import parted

from blivet.size import Size

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk

from blivetgui.dialogs.device_info_dialog import DeviceInformationDialog


def _mock_device(dev_type, name="test", size=Size("2 GiB"), **kwargs):
    """ Create a mock device with common defaults """
    fmt = kwargs.pop("format", MagicMock(type=None, exists=True, status=False, mountable=False))
    parents = kwargs.pop("parents", [])

    device = MagicMock(type=dev_type, size=size, path="/dev/test", exists=True,
                       format=fmt, parents=parents, **kwargs)
    device.configure_mock(name=name)
    return device


@unittest.skipUnless("DISPLAY" in os.environ.keys(), "requires X server")
class StratisDeviceInfoTest(unittest.TestCase):

    def _run_dialog(self, device):
        dialog = DeviceInformationDialog(parent_window=None, device=device,
                                         client=MagicMock(), installer_mode=False)
        labels = [child.get_label() for child in dialog.grid.get_children()
                  if isinstance(child, Gtk.Label)]
        dialog.destroy()

        return labels

    def _get_label(self, labels, text):
        """ Return label that contains given text """
        matching = [label for label in labels if text in label]
        self.assertEqual(len(matching), 1)
        return matching[0]

    def test_stratis_pool(self):
        pool = _mock_device("stratis pool", name="testpool", encrypted=True,
                            overprovisioning=False, free_space=Size("1 GiB"),
                            fs_limit=100)

        labels = self._run_dialog(pool)

        # dialog header with the device type
        header = self._get_label(labels, "<b>")
        self.assertIn("Stratis Pool", header)
        self.assertIn("testpool", header)

        # stratis pool specific information
        info = self._get_label(labels, "Encrypted")
        self.assertIn("Yes", info)
        self.assertIn("Overprovisioning", info)
        self.assertIn("No", info)
        self.assertIn(str(Size("1 GiB")), info)
        self.assertIn("100", info)
        self.assertNotIn("Blockdevs", info)  # blockdevs are listed in the parents info

    def test_stratis_pool_unencrypted(self):
        pool = _mock_device("stratis pool", name="testpool", encrypted=False,
                            overprovisioning=True, free_space=Size("1 GiB"),
                            fs_limit=100)

        labels = self._run_dialog(pool)

        info = self._get_label(labels, "Encrypted")
        self.assertIn("No", info)
        self.assertIn("Yes", info)  # overprovisioning enabled

    def test_stratis_filesystem(self):
        parent_pool = MagicMock(exists=True, size=Size("2 GiB"), type="stratis pool")
        parent_pool.configure_mock(name="testpool")

        filesystem = _mock_device("stratis filesystem", name="testpool/testfs",
                                  size=Size("1 GiB"), used_size=Size("256 MiB"),
                                  pool=parent_pool, parents=[parent_pool])

        labels = self._run_dialog(filesystem)

        # dialog header with the device type
        header = self._get_label(labels, "<b>")
        self.assertIn("Stratis Filesystem", header)
        self.assertIn("testfs", header)

        # stratis filesystem specific information
        info = self._get_label(labels, "<i>Pool:")
        self.assertIn("testpool", info)
        self.assertIn(str(Size("256 MiB")), info)

        # no format information for stratis filesystems; all information
        # about the filesystem is part of the stratis filesystem info
        self.assertNotIn("Device format", labels)

    def test_device_format_info(self):
        # format information is displayed for other device types
        device = _mock_device("partition", name="sda1", part_type=parted.PARTITION_NORMAL,
                              parted_partition=None,
                              format=MagicMock(type="ext4", exists=True, status=False,
                                               mountable=False, uuid="test-uuid",
                                               label=None))

        labels = self._run_dialog(device)

        self._get_label(labels, "Device format")
        fmt_info = self._get_label(labels, "ext4")
        self.assertIn("test-uuid", fmt_info)


if __name__ == "__main__":
    unittest.main()
