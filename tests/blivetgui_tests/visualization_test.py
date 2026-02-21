import unittest
from unittest.mock import MagicMock

from blivet.size import Size

from blivetgui.visualization.rectangle import Rectangle

import os

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk


def _mock_device(dev_type, name="test", size=Size("10 GiB"), children=None, **kwargs):
    """ Create a mock device with common defaults """
    if children is None:
        children = []
    fmt = kwargs.pop("format", MagicMock(type=None, exists=True, status=False))
    is_disk = kwargs.pop("is_disk", False)
    protected = kwargs.pop("protected", False)
    parents = kwargs.pop("parents", [])

    device = MagicMock(type=dev_type, size=size, children=children,
                       format=fmt, is_disk=is_disk, protected=protected,
                       parents=parents, **kwargs)
    device.configure_mock(name=name)
    return device


@unittest.skipUnless("DISPLAY" in os.environ.keys(), "requires X server")
class RectangleChildCountTest(unittest.TestCase):

    def _create_rectangle(self, device):
        blivet_gui = MagicMock(auto_dev_updates_warning=False)
        rect = Rectangle("", None, 200, 50, device, blivet_gui)
        return rect

    def _get_label_text(self, rect):
        """ Extract the text from the label widget inside the rectangle """
        hbox = rect.get_child()
        for child in hbox.get_children():
            if isinstance(child, Gtk.Label):
                return child.get_text()
        return None

    def test_child_count(self):
        # VG with 3 LVs
        device = _mock_device("lvmvg", name="myvg", children=[MagicMock() for _ in range(3)])
        rect = self._create_rectangle(device)
        label = self._get_label_text(rect)
        self.assertIn("myvg", label)
        self.assertIn("3 logical volumes", label)

        # VG with one LV
        device = _mock_device("lvmvg", name="myvg", children=[MagicMock()])
        rect = self._create_rectangle(device)
        label = self._get_label_text(rect)
        self.assertIn("1 logical volume", label)

        # VG without LVs
        device = _mock_device("lvmvg", name="myvg", children=[])
        rect = self._create_rectangle(device)
        label = self._get_label_text(rect)
        self.assertIn("0 logical volumes", label)

        # btrfs volume
        children = [MagicMock() for _ in range(2)]
        device = _mock_device("btrfs volume", name="btrfs1", children=children,
                              subvolumes=[])
        rect = self._create_rectangle(device)
        label = self._get_label_text(rect)
        self.assertIn("btrfs1", label)
        self.assertIn("2 subvolumes", label)

        # other
        device = _mock_device("partition", name="sda1",
                              format=MagicMock(type="ext4", exists=True, status=False))
        rect = self._create_rectangle(device)
        label = self._get_label_text(rect)
        self.assertIn("sda1", label)
        self.assertNotIn("logical volume", label)
        self.assertNotIn("subvolume", label)
        self.assertNotIn("filesystem", label)


if __name__ == "__main__":
    unittest.main()
