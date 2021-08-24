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
        self.kwargs = kwargs

    def __iter__(self):
        return iter(self.kwargs.keys())

    def __getitem__(self, key):
        return self.kwargs[key]

    def __setitem__(self, key, value):
        self.kwargs[key] = value

    def __getattr__(self, name):
        if name not in self.kwargs.keys():
            raise AttributeError("%s has no attribute %s" % ("ProxyDataContainer", name))
        return self.kwargs.get(name, None)

    def __repr__(self):
        return "ProxyDataContainer:\n%s" % str(self.kwargs)


class ProxyID(object):
    """ A simple picklable object with a unique ID
    """

    _newid_gen = functools.partial(next, itertools.count())

    def __init__(self):
        self.id = self._newid_gen()  # pylint: disable=assignment-from-no-return

    def __repr__(self):
        return "'Proxy ID, %s'" % self.id
