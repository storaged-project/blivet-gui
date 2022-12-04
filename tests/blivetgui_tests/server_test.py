# -*- coding: utf-8 -*-

import unittest
from unittest.mock import MagicMock

import pickle

from blivetgui.communication.server import BlivetUtilsServer, BlivetProxyObject
from blivetgui.communication.proxy_utils import ProxyID, ProxyDataContainer

from blivet.size import Size


class BlivetUtilsServerTest(unittest.TestCase):

    def test_pickle_answer(self):
        # string
        msg = "abcdef"
        pickled_msg = BlivetUtilsServer._pickle_answer(MagicMock(), msg)
        self.assertEqual(msg, pickle.loads(pickled_msg))

        # None
        msg = None
        pickled_msg = BlivetUtilsServer._pickle_answer(MagicMock(), msg)
        self.assertEqual(msg, pickle.loads(pickled_msg))

        # blivet.size.Size
        msg = Size("8 GiB")
        pickled_msg = BlivetUtilsServer._pickle_answer(MagicMock(), msg)
        self.assertEqual(msg, pickle.loads(pickled_msg))

        # list of multiple types
        msg = ["abcdef", 1, 1.01, True]
        pickled_msg = BlivetUtilsServer._pickle_answer(MagicMock(), msg)
        self.assertEqual(msg, pickle.loads(pickled_msg))

        # BlivetProxyObject
        msg = BlivetProxyObject(MagicMock(), ProxyID())
        pickled_msg = BlivetUtilsServer._pickle_answer(MagicMock(), msg)
        # BlivetProxyObject is not pickled, instead of it we pickle its id (ProxyID object)
        # we compare the id (int) of this id (ProxyID) with id of unpickled object
        self.assertEqual(msg.id.id, pickle.loads(pickled_msg).id)

        # unpicklable object
        test_dict = {}

        msg = MagicMock()  # MagicMock is definitely not in picklable_types
        pickled_msg = BlivetUtilsServer._pickle_answer(MagicMock(object_dict=test_dict), msg)
        unpickled_msg = pickle.loads(pickled_msg)
        # unpicklable objects are not pickled, instead a BlivetProxyObject is created
        # and its ProxyID is pickled; test we really have a ProxyID object and test
        # that original object was placed in the dict with proxied-object
        self.assertTrue(isinstance(unpickled_msg, ProxyID))
        self.assertEqual(test_dict[unpickled_msg.id].blivet_object, msg)

        # unpicklable objects in list
        test_dict = {}

        msg = [MagicMock(), "abcdef"]
        pickled_msg = BlivetUtilsServer._pickle_answer(MagicMock(object_dict=test_dict), msg)
        unpickled_msg = pickle.loads(pickled_msg)
        self.assertTrue(isinstance(unpickled_msg, list))
        self.assertTrue(isinstance(unpickled_msg[0], ProxyID))
        self.assertEqual(test_dict[unpickled_msg[0].id].blivet_object, msg[0])
        self.assertEqual(unpickled_msg[1], msg[1])

    def test_convert_args(self):
        # 'normal' arguments
        args = ["abcdef", 1, 1.01, True, None]
        converted_args = BlivetUtilsServer._args_convertTo_objects(MagicMock(), args)
        self.assertEqual(converted_args, args)

        # ProxyID arguments
        test_dict = {}

        arg1 = ProxyID()
        arg1_obj = MagicMock(blivet_object=MagicMock())
        test_dict[arg1.id] = arg1_obj
        arg2 = ProxyID()
        arg2_obj = MagicMock(blivet_object=MagicMock())
        test_dict[arg2.id] = arg2_obj

        converted_args = BlivetUtilsServer._args_convertTo_objects(MagicMock(object_dict=test_dict), [arg1, arg2])
        self.assertEqual(converted_args, [arg1_obj.blivet_object, arg2_obj.blivet_object])

        # ProxyDataContainer as an argument
        test_dict = {}

        arg3 = ProxyID()
        arg3_obj = MagicMock(blivet_object=MagicMock())
        test_dict[arg3.id] = arg3_obj

        args = [ProxyDataContainer(data1="abcdef", data2=1, data3=arg3)]
        converted_args = BlivetUtilsServer._args_convertTo_objects(MagicMock(object_dict=test_dict), args)
        self.assertEqual(converted_args[0]["data1"], "abcdef")
        self.assertEqual(converted_args[0]["data2"], 1)
        self.assertEqual(converted_args[0]["data3"], arg3_obj.blivet_object)

    def test_convert_kwargs(self):
        test_dict = {}

        arg1 = ProxyID()
        arg1_obj = MagicMock(blivet_object=MagicMock())
        test_dict[arg1.id] = arg1_obj
        arg2 = ProxyID()
        arg2_obj = MagicMock(blivet_object=MagicMock())
        test_dict[arg2.id] = arg2_obj

        kwargs = {"a": 1, "b": arg1, "c": arg2}
        server_mock = MagicMock(object_dict=test_dict,
                                _args_convertTo_objects=lambda args: BlivetUtilsServer._args_convertTo_objects(MagicMock(object_dict=test_dict), args))
        converted_kwargs = BlivetUtilsServer._kwargs_convertTo_objects(server_mock, kwargs)
        self.assertEqual(converted_kwargs, {"a": 1, "b": arg1_obj.blivet_object, "c": arg2_obj.blivet_object})


class BlivetProxyObjectTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.blivet_object = MagicMock(set_test=None)
        del cls.blivet_object.non_existing  # mock non-existing attribute
        cls.obj_id = ProxyID()
        cls.proxy_object = BlivetProxyObject(cls.blivet_object, cls.obj_id)

    def test_getattr(self):
        self.assertEqual(self.proxy_object.existing, self.blivet_object.existing)
        with self.assertRaises(AttributeError):
            self.proxy_object.non_existing  # pylint: disable=W0104

    def test_setattr(self):
        self.proxy_object.set_test = "test"
        self.assertEqual(self.blivet_object.set_test, "test")

    def test_getitem(self):
        self.assertEqual(self.proxy_object["key"], self.blivet_object["key"])  # pylint: disable=unsubscriptable-object

    def test_str(self):
        self.assertEqual(str(self.proxy_object), str(self.blivet_object))

    def test_len(self):
        self.assertEqual(len(self.proxy_object), len(self.blivet_object))


if __name__ == "__main__":
    unittest.main()
