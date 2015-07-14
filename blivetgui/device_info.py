# -*- coding: utf-8 -*-
# actions_toolbar.py
# Gtk.Label displaying information about selected device
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

import gettext

#------------------------------------------------------------------------------#

_ = lambda x: gettext.translation("blivet-gui", fallback=True).gettext(x) if x != "" else ""

#------------------------------------------------------------------------------#

class DeviceInfo(object):
    """ Create label with information about selected device
    """

    def __init__(self, blivet_gui):

        self.blivet_gui = blivet_gui

        self.info_label = Gtk.Label()
        self.info_label.set_margin_start(5)
        self.info_label.set_margin_end(5)

    def update_device_info(self, device):
        """ Basic information for selected device
        """

        if device.type == "lvmvg":
            info_str = _("<b>LVM2 Volume group <i>{0}</i> occupying {1} " \
                         "physical volume(s):</b>\n\n").format(device.name, len(device.parents))

            for parent in device.parents:
                info_str += _("\t• PV <i>{0}</i>, size: {1} on <i>{2}</i> " \
                              "disk.\n").format(parent.name, str(parent.size), parent.disks[0].name)

        elif device.type == "disk":
            info_str = _("<b>Hard disk</b> <i>{0}</i>\n\n\t• Size: <i>{1}</i>\n\t" \
                         "• Model: <i>{2}</i>\n").format(device.path,
                                                         str(device.size), device.model)

        else:
            info_str = ""

        self.info_label.set_markup(info_str)

        return
