# server.py
#
#
# Copyright (C) 2015  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#
# Red Hat Author(s): Vojtech Trefny <vtrefny@redhat.com>
#
#------------------------------------------------------------------------------#

from blivet import size

import sys

import six
import traceback

import struct

from six.moves import socketserver
from six.moves import cPickle

from .proxy_utils import ProxyID, ProxyDataContainer

from ..utils import BlivetUtils

#------------------------------------------------------------------------------#

picklable_types = six.integer_types + six.string_types + (six.text_type, float, bool, size.Size, BaseException)

#------------------------------------------------------------------------------#

import inspect

class BlivetProxyObject(object):

    def __init__(self, blivet_object):
        self.blivet_object = blivet_object

    def __getattr__(self, name):
        if not hasattr(self.blivet_object, name):
            raise AttributeError

        subobject = getattr(self.blivet_object, name)

        return subobject

    def is_method(self, param_name):
        subobject = getattr(self.blivet_object, param_name)

        return inspect.ismethod(subobject)

    def __getitem__(self, key):
        try:
            if isinstance(self.blivet_object[key], picklable_types):
                return self.blivet_object[key]

            else:
                return BlivetProxyObject(self.blivet_object[key])

        except IndexError as e:
            return e

    def __str__(self):
        return str(self.blivet_object)

    def __len__(self):
        if hasattr(self.blivet_object, "__len__"):
            return len(self.blivet_object)

        # testing "if object:" uses len() to determine whether object is not None
        else:
            return 1


class BlivetUtilsServer(socketserver.BaseRequestHandler): #FIXME: possibly change the server to multiprocess manager?
    blivet_utils = None
    proxy_objects = []
    object_dict = {}

    def handle(self):
        # self.request is the TCP socket connected to the client

        while True:
            msg = self._recv_msg()

            unpickled_msg = cPickle.loads(msg)

            if unpickled_msg[0] == "quit":
                self.server.quit = True
                break

            elif unpickled_msg[0] == "init":
                # print("RECV: init", unpickled_msg)
                self._blivet_utils_init(unpickled_msg)

            elif unpickled_msg[0] == "call":
                # print("RECV: call", unpickled_msg)
                self._call_utils_method(unpickled_msg)

            elif unpickled_msg[0] == "param":
                # print("RECV: param", unpickled_msg)
                self._get_param(unpickled_msg)

            elif unpickled_msg[0] == "method":
                # print("RECV: method", unpickled_msg)
                self._call_method(unpickled_msg)

            elif unpickled_msg[0] == "next":
                # print("RECV: next", unpickled_msg)
                self._get_next(unpickled_msg)

            elif unpickled_msg[0] == "key":
                # print("RECV: key", unpickled_msg)
                self._get_key(unpickled_msg)

    def _recv_msg(self):
        raw_msglen = self._recv_data(4)

        if not raw_msglen:
            return None

        msglen = struct.unpack(">I", raw_msglen)[0]

        return self._recv_data(msglen)

    def _recv_data(self, length):

        if six.PY2:
            data = ""
        else:
            data = b""

        while len(data) < length:
            packet = self.request.recv(length - len(data))

            if not packet:
                return None

            data += packet

        return data

    def _pickle_answer(self, answer):
        if answer is None:
            picklable_answer = answer

        elif isinstance(answer, (list, tuple)):
            picklable_answer = []

            for item in answer:
                if not isinstance(item, picklable_types):
                    proxy_object = BlivetProxyObject(item)
                    new_id = ProxyID()
                    self.object_dict[new_id.id] = proxy_object
                    picklable_answer.append(new_id)
                else:
                    picklable_answer.append(item)

        elif not isinstance(answer, picklable_types):
            proxy_object = BlivetProxyObject(answer)
            new_id = ProxyID()
            self.object_dict[new_id.id] = proxy_object
            picklable_answer = new_id

        else:
            picklable_answer = answer

        pickled_answer = cPickle.dumps(picklable_answer)

        return pickled_answer

    def _get_param(self, data):
        proxy_object = self.object_dict[data[1].id]
        param_name = data[2]

        if not hasattr(proxy_object.blivet_object, param_name):
            if six.PY2:
                answer = ValueError("%s has no attribute %s" % (proxy_object.blivet_object.name, param_name))
            else:
                answer = AttributeError("%s has no attribute %s" % (proxy_object.blivet_object.name, param_name))

        elif proxy_object.is_method(param_name):
            raise ValueError("Calling method, not attribute")

        else:
            answer = getattr(proxy_object, param_name)

        pickled_answer = self._pickle_answer(answer)

        self._send(pickled_answer)

    def _get_next(self, data):
        proxy_object = self.object_dict[data[1].id]

        try:
            answer = proxy_object.__next__()

        except StopIteration as stop:
            answer = stop

        pickled_answer = self._pickle_answer(answer)

        self._send(pickled_answer)

    def _get_key(self, data):
        proxy_object = self.object_dict[data[1].id]
        key = data[2]

        answer = proxy_object[key]
        pickled_answer = self._pickle_answer(answer)

        self._send(pickled_answer)

    def _blivet_utils_init(self, data):
        if self.blivet_utils:
            raise RuntimeError("Server already received request for initialization.")

        if self.server.other_running:
            exc = RuntimeError("Another instance of blivet-gui-daemon is already running.")
            answer = ProxyDataContainer(success=False, exception=exc)

        else:
            args = self._args_convertTo_objects(data[1])

            self.blivet_utils = BlivetUtils(*args)

            answer = ProxyDataContainer(success=True)

        pickled_answer = self._pickle_answer(answer)

        self._send(pickled_answer)

    def _call_method(self, data):
        proxy_object = self.object_dict[data[1].id]
        param_name = data[2]
        args = data[3]

        method = getattr(proxy_object, param_name)
        answer = method(*args)
        pickled_answer = self._pickle_answer(answer)

        self._send(pickled_answer)

    def _call_utils_method(self, data):
        utils_method = getattr(self.blivet_utils, data[1])
        args = self._args_convertTo_objects(data[2])

        try:
            ret = utils_method(*args)
            answer = ProxyDataContainer(success=True, answer=ret)
        except Exception as e: # pylint: disable=broad-except
            answer = ProxyDataContainer(success=False, exception=e, traceback=traceback.format_exc())

        pickled_answer = self._pickle_answer(answer)

        self._send(pickled_answer)

    def _args_convertTo_objects(self, args):
        # all args sent from client to server are be either built-in types (int, str...) or
        # ProxyID (or ProxyDataContainer), we need to "convert" them to blivet Objects
        args_id = []

        for arg in args:
            if isinstance(arg, ProxyDataContainer):
                for item in arg:
                    if isinstance(arg[item], ProxyID):
                        arg[item] = self.object_dict[arg[item].id].blivet_object
                    elif isinstance(arg[item], (list, tuple)):
                        arg[item] = self._args_convertTo_objects(arg[item])
                args_id.append(arg)
            elif isinstance(arg, ProxyID):
                args_id.append(self.object_dict[arg.id].blivet_object)

            elif isinstance(arg, (list, tuple)):
                args_id.append(self._args_convertTo_objects(arg))

            else:
                args_id.append(arg)

        return args_id

    def _send(self, data):
        data = struct.pack(">I", len(data)) + data
        self.request.sendall(data)
