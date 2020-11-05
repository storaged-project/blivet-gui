# proxy_utils.py
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

import functools
import itertools


class ProxyDataContainer(object):
    """ A picklable container for multiple objects similar to namedtuple
    """

    kwargs = None

    def __init__(self, **kwargs):
        """
        Initialize the instance.

        Args:
            self: (todo): write your description
        """
        self.kwargs = kwargs

    def __iter__(self):
        """
        Return an iterator over the keys of the iterable.

        Args:
            self: (todo): write your description
        """
        return iter(self.kwargs.keys())

    def __getitem__(self, key):
        """
        Get an item from the cache.

        Args:
            self: (todo): write your description
            key: (str): write your description
        """
        return self.kwargs[key]

    def __setitem__(self, key, value):
        """
        Sets a value of the value.

        Args:
            self: (todo): write your description
            key: (str): write your description
            value: (str): write your description
        """
        self.kwargs[key] = value

    def __getattr__(self, name):
        """
        Returns the value from the kwargs.

        Args:
            self: (todo): write your description
            name: (str): write your description
        """
        if name not in self.kwargs.keys():
            raise AttributeError("%s has no attribute %s" % ("ProxyDataContainer", name))
        return self.kwargs.get(name, None)

    def __repr__(self):
        """
        Return a human - readable string.

        Args:
            self: (todo): write your description
        """
        return "ProxyDataContainer:\n%s" % str(self.kwargs)


class ProxyID(object):
    """ A simple picklable object with a unique ID
    """

    _newid_gen = functools.partial(next, itertools.count())

    def __init__(self):
        """
        Initialize the id.

        Args:
            self: (todo): write your description
        """
        self.id = self._newid_gen()

    def __repr__(self):
        """
        Return a human - readable representation of this object.

        Args:
            self: (todo): write your description
        """
        return "'Proxy ID, %s'" % self.id
