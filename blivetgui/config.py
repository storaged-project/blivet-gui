# -*- coding: utf-8 -*-
# config.py
# Config for blivet-gui
#
# Copyright (C) 2017  Red Hat, Inc.
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


class BlivetGUIConfig(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

        self["default_fstype"] = "ext4"
        self["log_dir"] = "/var/log/blivet-gui"

    def __getattr__(self, name):
        if name not in self.keys() and not hasattr(self, name):
            raise AttributeError("BlivetGUIConfig has no attribute %s" % name)
        return self[name]

    def __setattr__(self, name, value):
        if name not in self.keys() and not hasattr(self, name):
            raise AttributeError("BlivetGUIConfig has no attribute %s" % name)
        self[name] = value

    def __repr__(self):
        return "BlivetGUIConfig:\n%s" % str(self)


config = BlivetGUIConfig()
