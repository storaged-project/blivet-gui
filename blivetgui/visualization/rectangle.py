# -*- coding: utf-8 -*-
# rectangle.py
# Gtk.Button modified for device visualization
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

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk

class Rectangle(Gtk.RadioButton):
    """ Rectangle object """

    __gtype_name__ = "Rectangle"

    def __init__(self, rtype, group, width, height, device):
        self.width = width
        self.height = height

        self.device = device

        Gtk.RadioButton.__init__(self, group=group, width_request=width, height_request=height)

        self.set_mode(False)
        self.set_name(rtype)

        label_name = Gtk.Label(label=self.device.name)
        self.add(label_name)
