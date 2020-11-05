# -*- coding: utf-8 -*-

import unittest

from blivetgui.communication.proxy_utils import ProxyID, ProxyDataContainer


class ProxyUtilsTest(unittest.TestCase):

    def test_proxy_id(self):
        """
        Set the proxy id1 id1 id1 id1 id2.

        Args:
            self: (todo): write your description
        """
        # test unique ID
        id1 = ProxyID()
        id2 = ProxyID()

        self.assertNotEqual(id1.id, id2.id)

    def test_proxy_data_container(self):
        """
        Test for proxy container.

        Args:
            self: (todo): write your description
        """
        container = ProxyDataContainer(a="a", b="b", c="c")

        # __iter__
        args = []

        for item in container:
            args.append(item)

        self.assertEqual(sorted(args), ["a", "b", "c"])

        # __getitem__
        self.assertEqual(container["a"], "a")

        # __setitem__
        container["a"] = 1
        self.assertEqual(container["a"], 1)

        # __getattr__
        self.assertEqual(container.b, "b")

        with self.assertRaises(AttributeError):
            container.d  # pylint: disable=W0104


if __name__ == "__main__":
    unittest.main()
