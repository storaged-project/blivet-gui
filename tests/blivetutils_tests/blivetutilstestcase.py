import glob
import os
import re
import shutil
import subprocess
import unittest

from blivetgui.blivet_utils import BlivetUtils


def run_command(command):
    res = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)

    out, err = res.communicate()
    if res.returncode != 0:
        output = out.decode().strip() + "\n\n" + err.decode().strip()
    else:
        output = out.decode().strip()
    return (res.returncode, output)


class BlivetUtilsTestToolkit(unittest.TestCase):

    vdevs = None
    blivet_utils = None

    def setUp(self):
        self.blivet_utils = BlivetUtils(exclusive_disks=self.vdevs)

        # check we are really working only with the targetcli disks
        disks = self.blivet_utils.get_disks()
        self.assertCountEqual(self.vdevs, [d.name for d in disks])

    def get_blivet_device(self, device_name):
        return self.blivet_utils.storage.devicetree.get_device_by_name(device_name)

    def reset(self):
        self.blivet_utils.blivet_reset()


@unittest.skipUnless(os.geteuid() == 0, "requires root access")
@unittest.skipUnless(shutil.which("targetcli"), "targetcli not found in $PATH")
class BlivetUtilsTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        orig_devs = {dev for dev in os.listdir("/dev") if re.match(r"sd[a-z]+$", dev)}

        test_dir = os.path.abspath(os.path.dirname(__file__))
        ret, _out = run_command("targetcli restoreconfig %s" % os.path.join(test_dir, "targetcli_config.json"))
        assert ret == 0
        _ret, _out = run_command("udevadm settle")

        devs = {dev for dev in os.listdir("/dev") if re.match(r'sd[a-z]+$', dev)}

        cls.vdevs = list(devs - orig_devs)

        # four new devices should be added
        assert len(cls.vdevs) == 4

        # let's be 100% sure that we pick a virtual ones
        for d in cls.vdevs:
            with open('/sys/block/%s/device/model' % d, encoding="utf-8") as model_file:
                assert model_file.read().strip() == 'blivetgui_test_'

    @classmethod
    def tearDownClass(cls):
        # remove the fake SCSI devices and their backing files
        _ret, _out = run_command("targetcli clearconfig confirm=True")
        for disk_file in glob.glob("/var/tmp/blivetgui_test_disk*"):
            os.unlink(disk_file)
