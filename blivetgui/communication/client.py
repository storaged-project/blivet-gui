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
# ---------------------------------------------------------------------------- #

import pickle

import socket
import struct

from threading import Lock

from .proxy_utils import ProxyID, ProxyDataContainer
from .errors import ServerConnectionError

from ..i18n import _

# ---------------------------------------------------------------------------- #


class ClientProxyObject(object):

    attrs = ("client", "proxy_id")

    def __init__(self, client, proxy_id):
        """
        Initialize a proxy.

        Args:
            self: (todo): write your description
            client: (todo): write your description
            proxy_id: (str): write your description
        """
        self.client = client
        self.proxy_id = proxy_id

    def __len__(self):
        """
        Return the remote remote proxy

        Args:
            self: (todo): write your description
        """
        remote_ret = self.client.remote_method(self.proxy_id, "__len__", (), {})
        return remote_ret

    def __iter__(self):
        """
        Return an iterator of remote proxy.

        Args:
            self: (todo): write your description
        """
        remote_iter = self.client.remote_method(self.proxy_id, "__iter__", (), {})
        return remote_iter

    def __call__(self, *args, **kwargs):
        """
        Calls the remote method.

        Args:
            self: (todo): write your description
        """
        remote_res = self.client.remote_method(self.proxy_id, "__call__", args, kwargs)

        if isinstance(remote_res, BaseException):
            raise remote_res
        else:
            return remote_res

    def __next__(self):
        """
        Returns the next remote proxy.

        Args:
            self: (todo): write your description
        """
        remote_ret = self.client.remote_next(self.proxy_id)

        if isinstance(remote_ret, BaseException):
            raise remote_ret
        else:
            return remote_ret

        return remote_ret

    def __getitem__(self, key):
        """
        Retrieves the key from the cache.

        Args:
            self: (todo): write your description
            key: (str): write your description
        """
        remote_key = self.client.remote_key(self.proxy_id, key)

        if isinstance(remote_key, BaseException):
            raise remote_key
        else:
            return remote_key

    def __str__(self):
        """
        Returns a string representation of this proxy.

        Args:
            self: (todo): write your description
        """
        remote_str = self.client.remote_method(self.proxy_id, "__str__", (), {})
        return remote_str

    def __getattr__(self, attr_name):
        """
        Get attribute from the attribute.

        Args:
            self: (todo): write your description
            attr_name: (str): write your description
        """
        remote_attr = self.client.remote_param(self.proxy_id, attr_name)

        if isinstance(remote_attr, BaseException) and attr_name not in ("exception",):
            raise remote_attr

        else:
            return remote_attr

    def __setattr__(self, attr_name, value):
        """
        Set an attribute on an object.

        Args:
            self: (todo): write your description
            attr_name: (str): write your description
            value: (todo): write your description
        """
        if attr_name in self.attrs + tuple(object.__dict__.keys()):
            super().__setattr__(attr_name, value)
        else:
            remote_res = self.client.remote_method(self.proxy_id, "__setattr__", (attr_name, value), {})

            if isinstance(remote_res, BaseException):
                raise remote_res
            else:
                return remote_res


class BlivetGUIClient(object):

    id_dict = {}

    def __init__(self, server_socket):
        """
        Create a socket.

        Args:
            self: (todo): write your description
            server_socket: (todo): write your description
        """
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(server_socket)
        self.mutex = Lock()

    def _answer_convertTo_object(self, answer):
        """ All data sent from server to BlivetGUI must be either built-in types (int, str...) or
            ClientProxyObject, never ProxyID
        """

        if isinstance(answer, ProxyID):
            if answer.id in self.id_dict.keys():  # we already recieved this id before and have our proxy object for it
                return self.id_dict[answer]
            else:
                self.id_dict[answer] = ClientProxyObject(client=self, proxy_id=answer)  # new id, create new proxy object
                return self.id_dict[answer]  # and return it
        elif isinstance(answer, (list, tuple)):
            new_answer = []
            for item in answer:
                new_answer.append(self._answer_convertTo_object(item))
            return new_answer
        else:
            return answer

    def _args_convertTo_id(self, args):
        """ All args sent from client to server must be either built-in types (int, str...) or
            ProxyID (or ProxyDataContainer), never ClientProxyObject
        """

        args_id = []

        for arg in args:
            if isinstance(arg, ProxyDataContainer):
                arg_id = ProxyDataContainer()
                for item in arg:
                    if isinstance(arg[item], ProxyDataContainer):
                        arg_id[item] = self._args_convertTo_id([arg[item]])[0]
                    elif isinstance(arg[item], ClientProxyObject):
                        arg_id[item] = arg[item].proxy_id
                    elif isinstance(arg[item], (list, tuple)):
                        arg_id[item] = self._args_convertTo_id(arg[item])
                    else:
                        arg_id[item] = arg[item]
                args_id.append(arg_id)
            elif isinstance(arg, ClientProxyObject):
                args_id.append(arg.proxy_id)
            elif isinstance(arg, (list, tuple)):
                args_id.append(self._args_convertTo_id(arg))
            else:
                args_id.append(arg)

        return args_id

    def remote_call(self, method, *args):
        """ Call a method on server
        """

        pickled_data = pickle.dumps(("call", method, self._args_convertTo_id(args)))

        with self.mutex:
            self._send(pickled_data)
            answer = pickle.loads(self._recv_msg())

        ret = self._answer_convertTo_object(answer)

        if not ret.success:  # pylint: disable=maybe-no-member
            raise type(ret.exception)(str(ret.exception) + "\n" + ret.traceback)  # pylint: disable=maybe-no-member

        else:
            return ret.answer  # pylint: disable=maybe-no-member

    def remote_param(self, proxy_id, param_name):
        """ Get a param of proxy_id object
        """

        pickled_data = pickle.dumps(("param", proxy_id, param_name))

        with self.mutex:
            self._send(pickled_data)
            answer = pickle.loads(self._recv_msg())

        return self._answer_convertTo_object(answer)

    def remote_method(self, proxy_id, method_name, args, kwargs):
        """ Call remotely a method on proxy_id object
        """

        pickled_data = pickle.dumps(("method", proxy_id, method_name, args, kwargs))

        with self.mutex:
            self._send(pickled_data)
            answer = pickle.loads(self._recv_msg())

        return self._answer_convertTo_object(answer)

    def remote_next(self, proxy_id):
        """ Ask for a next member of iterable proxy_id object
        """

        pickled_data = pickle.dumps(("next", proxy_id))

        with self.mutex:
            self._send(pickled_data)
            answer = pickle.loads(self._recv_msg())

        return self._answer_convertTo_object(answer)

    def remote_key(self, proxy_id, key):
        """ Ask for a member of iterable proxy_id object
        """

        pickled_data = pickle.dumps(("key", proxy_id, key))

        with self.mutex:
            self._send(pickled_data)
            answer = pickle.loads(self._recv_msg())

        return self._answer_convertTo_object(answer)

    def remote_control(self, command, *args):
        """ Send a control command to server
        """

        pickled_data = pickle.dumps((command, args))

        with self.mutex:
            self._send(pickled_data)
            answer = pickle.loads(self._recv_msg())

        return self._answer_convertTo_object(answer)

    def remote_do_it(self, show_progress_clbk):
        """
        Perform remote pickle on remote

        Args:
            self: (todo): write your description
            show_progress_clbk: (bool): write your description
        """

        pickled_data = pickle.dumps(("call", "blivet_do_it", ()))

        with self.mutex:
            self._send(pickled_data)
            answer = pickle.loads(self._recv_msg())

            ret = self._answer_convertTo_object(answer)

            while True:
                if ret[0]:  # pylint: disable=maybe-no-member
                    break

                show_progress_clbk(ret[1])

                answer = pickle.loads(self._recv_msg())
                ret = self._answer_convertTo_object(answer)

        return ret[1]

    def quit(self):
        """ Quit the client
        """

        pickled_data = pickle.dumps(("quit",))

        with self.mutex:
            self._send(pickled_data)
            self.sock.close()

    def _recv_msg(self):
        """ Recieve a message from server

            ..note.: first for bites represents message length
        """
        raw_msglen = self._recv_data(4)

        if not raw_msglen:
            return None

        msglen = struct.unpack(">I", raw_msglen)[0]

        return self._recv_data(msglen)

    def _recv_data(self, length):
        """ Recieve 'length' of data from client

            :param length: length of data to receive
            :type length: int

        """

        data = b""

        while len(data) < length:

            try:
                packet = self.sock.recv(length - len(data))

            except (OSError, BrokenPipeError) as e:
                msg = _("Failed to connect to blivet-gui-daemon")
                raise ServerConnectionError(msg) from e

            if not packet:
                return None

            data += packet

        return data

    def _send(self, data):
        """
        Send data to the socket.

        Args:
            self: (str): write your description
            data: (todo): write your description
        """
        data = struct.pack(">I", len(data)) + data

        try:
            self.sock.sendall(data)

        except (OSError, BrokenPipeError) as e:
            msg = _("Failed to connect to blivet-gui-daemon")
            raise ServerConnectionError(msg) from e
