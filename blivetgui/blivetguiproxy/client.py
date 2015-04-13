# client.py
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

from six.moves import cPickle

import six

from .proxy_utils import ProxyID, ProxyDataContainer

import socket

import struct

#------------------------------------------------------------------------------#

class ClientProxyObject(object):

    def __init__(self, client, proxy_id):
        self.client = client
        self.proxy_id = proxy_id

    def __len__(self):
        remote_ret = self.client.remote_method(self.proxy_id, "__len__", ())
        return remote_ret

    def __iter__(self):
        remote_iter = self.client.remote_method(self.proxy_id, "__iter__", ())
        return remote_iter

    def __next__(self):
        remote_ret = self.client.remote_next(self.proxy_id)

        if isinstance(remote_ret, BaseException):
            raise remote_ret
        else:
            return remote_ret

        return remote_ret

    def __getitem__(self, key):
        remote_key = self.client.remote_key(self.proxy_id, key)

        if isinstance(remote_key, BaseException):
            raise remote_key
        else:
            return remote_key

    def __str__(self):
        remote_str = self.client.remote_method(self.proxy_id, "__str__", ())
        return remote_str

    def __getattr__(self, attr_name):
        remote_attr = self.client.remote_param(self.proxy_id, attr_name)

        if isinstance(remote_attr, BaseException) and attr_name not in ("exception",):
            raise remote_attr

        else:
            return remote_attr

#------------------------------------------------------------------------------#

SOCK_FILE = "/tmp/blivet-gui.sock" #FIXME

from threading import Lock

class BlivetGUIClient(object):

    id_dict = {}

    def __init__(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(SOCK_FILE)
        self.mutex = Lock()

    def _answer_convertTo_object(self, answer):
        # all data sent from server to BlivetGUI must be either built-in types (int, str...) or
        # ClientProxyObject, never ProxyID

        if isinstance(answer, ProxyID):
            if answer.id in self.id_dict.keys(): # we already recieved this id before and have our proxy object for it
                return self.id_dict[answer]
            else:
                self.id_dict[answer] = ClientProxyObject(client=self, proxy_id=answer) # new id, create new proxy object
                return self.id_dict[answer] # and return iz
        elif isinstance(answer, (list, tuple)):
            new_answer = []
            for item in answer:
                new_answer.append(self._answer_convertTo_object(item))
            return new_answer
        else:
            return answer

    def _args_convertTo_id(self, args):
        # all args sent from client to server must be either built-in types (int, str...) or
        # ProxyID (or ProxyDataContainer), never ClientProxyObject

        args_id = []

        for arg in args:
            if isinstance(arg, ProxyDataContainer):
                for item in arg:
                    if isinstance(arg[item], ClientProxyObject):
                        arg[item] = arg[item].id
                    elif isinstance(arg[item], (list, tuple)):
                        arg[item] = self._args_convertTo_id(arg[item])
                args_id.append(arg)
            elif isinstance(arg, ClientProxyObject):
                args_id.append(arg.proxy_id)
            elif isinstance(arg, (list, tuple)):
                args_id.append(self._args_convertTo_id(arg))
            else:
                args_id.append(arg)

        return args_id

    def remote_call(self, method, *args): # call method on server with args
        pickled_data = cPickle.dumps(("call", method, self._args_convertTo_id(args)))

        with self.mutex:
            self._send(pickled_data)
            answer = cPickle.loads(self._recv_msg())

        ret = self._answer_convertTo_object(answer)

        if not ret.success:
            raise type(ret.exception)(str(ret.exception) + "\n" + ret.traceback)

        else:
            return ret.answer

    def remote_param(self, proxy_id, param_name): # get param from object represented by proxy_id
        pickled_data = cPickle.dumps(("param", proxy_id, param_name))

        with self.mutex:
            self._send(pickled_data)
            answer = cPickle.loads(self._recv_msg())

        return self._answer_convertTo_object(answer)

    def remote_method(self, proxy_id, method_name, args):
        pickled_data = cPickle.dumps(("method", proxy_id, method_name, args))

        with self.mutex:
            self._send(pickled_data)
            answer = cPickle.loads(self._recv_msg())

        return self._answer_convertTo_object(answer)

    def remote_next(self, proxy_id):
        pickled_data = cPickle.dumps(("next", proxy_id))

        with self.mutex:
            self._send(pickled_data)
            answer = cPickle.loads(self._recv_msg())

        return self._answer_convertTo_object(answer)

    def remote_key(self, proxy_id, key):
        pickled_data = cPickle.dumps(("key", proxy_id, key))

        with self.mutex:
            self._send(pickled_data)
            answer = cPickle.loads(self._recv_msg())

        return self._answer_convertTo_object(answer)

    def quit(self):
        pickled_data = cPickle.dumps(("quit",))

        with self.mutex:
            self._send(pickled_data)
            self.sock.close()

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
            packet = self.sock.recv(length - len(data))

            if not packet:
                return None

            data += packet

        return data

    def _send(self, data):
        data = struct.pack(">I", len(data)) + data
        self.sock.sendall(data)
