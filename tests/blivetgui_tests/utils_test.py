import unittest
from unittest.mock import MagicMock, PropertyMock, patch

from blivetgui.blivet_utils import BlivetUtils, FreeSpaceDevice
from blivetgui.i18n import _

from blivet import formats
from blivet.size import Size
from blivet.formats.fslib import FSResize


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
        disk = MagicMock(type="disk", children=[], is_disk=True, format=MagicMock(type="disklabel"))
        free = FreeSpaceDevice(free_size=Size("8 GiB"), dev_id=0, start=0, end=1, parents=[disk])

        self.assertTrue(free.is_empty_disk)
        self.assertFalse(free.is_uninitialized_disk)
        self.assertFalse(free.is_free_region)

        disk = MagicMock(type="disk", children=[], is_disk=True, format=MagicMock(type=None))
        free = FreeSpaceDevice(free_size=Size("8 GiB"), dev_id=0, start=0, end=1, parents=[disk])

        self.assertTrue(free.is_uninitialized_disk)
        self.assertFalse(free.is_empty_disk)
        self.assertFalse(free.is_free_region)

        disk = MagicMock(type="disk", children=[MagicMock()], is_disk=True, format=MagicMock(type="disklabel"))
        free = FreeSpaceDevice(free_size=Size("8 GiB"), dev_id=0, start=0, end=1, parents=[disk])

        self.assertTrue(free.is_free_region)
        self.assertFalse(free.is_empty_disk)
        self.assertFalse(free.is_uninitialized_disk)

    def test_free_disk(self):
        # free space on a disk
        disk = MagicMock(type="disk", children=[], is_disk=True, format=MagicMock(type=None))
        free = FreeSpaceDevice(free_size=Size("8 GiB"), dev_id=0, start=0, end=1, parents=[disk])
        self.assertEqual(free.disk, disk)

        # free space in a vg
        parent = MagicMock(type="lvmvg", children=[], is_disk=False, format=MagicMock(type=None),
                           parents=[MagicMock(type="partition", children=[MagicMock()], is_disk=False, parents=[disk],
                                    format=MagicMock(type="lvmpv"))])
        free = FreeSpaceDevice(free_size=Size("8 GiB"), dev_id=0, start=0, end=1, parents=[parent])
        self.assertEqual(free.disk, disk)

    def test_free_protected(self):
        disk = MagicMock(type="disk", children=[], is_disk=True, format=MagicMock(type=None))
        free = FreeSpaceDevice(free_size=Size("8 GiB"), dev_id=0, start=0, end=1, parents=[disk])

        self.assertEqual(free.protected, disk.protected)


class BlivetUtilsTest(unittest.TestCase):

    def test_resizable(self):
        with patch("blivetgui.blivet_utils.BlivetUtils.blivet_reset", lambda _: True):
            storage = BlivetUtils()
        device = MagicMock(type="", size=Size("1 GiB"), protected=False, format_immutable=False, children=[])
        device.format = MagicMock(exists=True, system_mountpoint=None)
        device.format.return_value = None

        # swap is not resizable
        device.format.configure_mock(type="swap")
        res = storage.device_resizable(device)
        self.assertFalse(res.resizable)
        self.assertEqual(res.error, _("Resizing of swap format is currently not supported"))
        self.assertEqual(res.min_size, Size("1 MiB"))
        self.assertEqual(res.max_size, Size("1 GiB"))

        # mounted device, format doesn't support online resize: not resizable
        device.format.configure_mock(type="ext4", system_mountpoint="/", _resize_support=0)
        res = storage.device_resizable(device)
        self.assertFalse(res.resizable)
        self.assertEqual(res.error, _("Mounted devices cannot be resized"))
        self.assertEqual(res.min_size, Size("1 MiB"))
        self.assertEqual(res.max_size, Size("1 GiB"))

        # mounted device, format does support online resize: resizable
        device.configure_mock(resizable=True, max_size=Size("2 GiB"), min_size=Size("500 MiB"))
        device.format.configure_mock(type="ext4", system_mountpoint="/", _resize_support=FSResize.ONLINE_GROW)
        res = storage.device_resizable(device)
        self.assertTrue(res.resizable)
        self.assertIsNone(res.error)
        self.assertEqual(res.min_size, Size("500 MiB"))
        self.assertEqual(res.max_size, Size("2 GiB"))

        # resizable device
        device.configure_mock(resizable=True, max_size=Size("2 GiB"), min_size=Size("500 MiB"))
        device.format.configure_mock(resizable=True, type="ext4", system_mountpoint=None)
        res = storage.device_resizable(device)
        self.assertTrue(res.resizable)
        self.assertIsNone(res.error)
        self.assertEqual(res.min_size, Size("500 MiB"))
        self.assertEqual(res.max_size, Size("2 GiB"))

        # resizable device and non-resizable format
        device.configure_mock(resizable=True, max_size=Size("2 GiB"), min_size=Size("500 MiB"))
        device.format.configure_mock(resizable=False, type="ext4")
        res = storage.device_resizable(device)
        self.assertFalse(res.resizable)
        self.assertEqual(res.error, _("Format is not resizable after updating its size limit information."))
        self.assertEqual(res.min_size, Size("1 MiB"))
        self.assertEqual(res.max_size, Size("1 GiB"))

        # LV with snapshot -> not resizable
        with patch("blivetgui.blivet_utils.BlivetUtils._has_snapshots", lambda _, device: True):
            device.configure_mock(type="lvmlv", resizable=True, max_size=Size("2 GiB"), min_size=Size("500 MiB"))
            device.format.configure_mock(resizable=True, type="ext4")
            res = storage.device_resizable(device)
            self.assertFalse(res.resizable)
            self.assertIsNotNone(res.error)
            self.assertEqual(res.min_size, Size("1 MiB"))
            self.assertEqual(res.max_size, Size("1 GiB"))

        # LUKS2 -> not resizable
        device.configure_mock(type="luks/dm-crypt", resizable=True, max_size=Size("2 GiB"), min_size=Size("500 MiB"),
                              raw_device=MagicMock(format=MagicMock(luks_version="luks2")))
        device.format.configure_mock(resizable=True, type="ext4", system_mountpoint=None)
        res = storage.device_resizable(device)
        self.assertFalse(res.resizable)
        self.assertEqual(res.error, _("Resizing of LUKS2 devices is currently not supported."))
        self.assertEqual(res.min_size, Size("1 MiB"))
        self.assertEqual(res.max_size, Size("1 GiB"))

    def test_fs_supported_for_creation(self):
        # Missing resize/label/info utilities must not prevent creating a filesystem.
        ext4 = formats.get_format("ext4")
        with patch.object(type(ext4), "formattable", new_callable=PropertyMock, return_value=True), \
             patch.object(type(ext4), "utils_available", new_callable=PropertyMock, return_value=False):
            self.assertFalse(ext4.supported)
            self.assertTrue(BlivetUtils._fs_supported_for_creation(ext4))

        # Formats that are not supported by blivet must stay unavailable.
        for fs_type in ("hfs+", "stratis xfs"):
            fmt = formats.get_format(fs_type)
            with patch.object(type(fmt), "formattable", new_callable=PropertyMock, return_value=True):
                self.assertFalse(BlivetUtils._fs_supported_for_creation(fmt))

        # Architecture-specific filesystems must keep their architecture checks.
        efi = formats.get_format("efi")
        with patch.object(type(efi), "formattable", new_callable=PropertyMock, return_value=True), \
             patch("blivetgui.blivet_utils.arch.is_efi", return_value=False):
            self.assertFalse(BlivetUtils._fs_supported_for_creation(efi))

        macefi = formats.get_format("macefi")
        with patch.object(type(macefi), "formattable", new_callable=PropertyMock, return_value=True), \
             patch("blivetgui.blivet_utils.arch.is_efi", return_value=True), \
             patch("blivetgui.blivet_utils.arch.is_mactel", return_value=False):
            self.assertFalse(BlivetUtils._fs_supported_for_creation(macefi))

        # GFS2 follows flags.gfs2 instead of the _supported attribute.
        gfs2 = formats.get_format("gfs2")
        with patch.object(type(gfs2), "formattable", new_callable=PropertyMock, return_value=True), \
             patch("blivetgui.blivet_utils.blivet_flags.gfs2", False):
            self.assertFalse(BlivetUtils._fs_supported_for_creation(gfs2))


if __name__ == "__main__":
    unittest.main()
