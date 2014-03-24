#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
# devel-assistant.py - this program calls mainWindow to start the GUI
# Copyright 2001 - 2013 Red Hat, Inc.
# Copyright 2013 Petr Hracek <phracek@redhat.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
#
# Authors:
# Petr Hracek <phracek@redhat.com>

import logging
import sys
import firstWindow

try:
    from gi.repository import Gtk
except RuntimeError, e:
    print _("devel-assistant requires a currently running X server.")
    print "%s: %r" % (e.__class__.__name__, str(e))
    sys.exit(1)

firstWindow.firstWindow()
