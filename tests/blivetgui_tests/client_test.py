# -*- coding: utf-8 -*-

import unittest
from unittest.mock import MagicMock

from blivetgui.communication.client import BlivetGUIClient, ClientProxyObject
from blivetgui.communication.proxy_utils import ProxyID, ProxyDataContainer

from blivet.size import Size


class BlivetGUIClientTest(unittest.TestCase):

    def test_convert_answer(self):
        # string (shouldn't be converted at all)
        msg = "abcdef"
        converted_answer = BlivetGUIClient._answer_convertTo_object(MagicMock(), msg)
        self.assertEqual(msg, converted_answer)

        # blivet.size.Size (is picklable too)
        msg = Size("8 GiB")
        converted_answer = BlivetGUIClient._answer_convertTo_object(MagicMock(), msg)
        self.assertEqual(msg, converted_answer)

        # ProxyID object
        test_dict = {}
        msg = ProxyID()
        converted_answer = BlivetGUIClient._answer_convertTo_object(MagicMock(id_dict=test_dict), msg)
        self.assertTrue(isinstance(converted_answer, ClientProxyObject))
        self.assertEqual(converted_answer.proxy_id, msg)  # pylint: disable=no-member

    def test_convert_args(self):
        # 'normal' arguments
        args = ["abcdef", 1, 1.01, True, None, Size("8 GiB")]
        converted_args = BlivetGUIClient._args_convertTo_id(MagicMock(), args)
        self.assertEqual(converted_args, args)

        # ClientProxyObject (id of object should be returned)
        args = [ClientProxyObject(MagicMock(), ProxyID())]
        converted_args = BlivetGUIClient._args_convertTo_id(MagicMock(), args)
        self.assertTrue(isinstance(converted_args[0], ProxyID))
        self.assertEqual(converted_args, [arg.proxy_id for arg in args])

        # ProxyDataContainer
        args = [ProxyDataContainer(data1="abcdef", data2=Size("8 GiB"), data3=ClientProxyObject(MagicMock(), ProxyID()))]
        converted_args = BlivetGUIClient._args_convertTo_id(MagicMock(), args)
        self.assertEqual(converted_args[0].data1, args[0].data1)
        self.assertEqual(converted_args[0].data2, args[0].data2)
        self.assertTrue(isinstance(converted_args[0].data3, ProxyID))
        self.assertEqual(converted_args[0].data3, args[0].data3.proxy_id)

if __name__ == "__main__":
    unittest.main()
