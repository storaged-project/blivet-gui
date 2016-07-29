# -*- coding: utf-8 -*-
# logs.py
# Logging for blivet-gui
#
# Copyright (C) 2014  Red Hat, Inc.
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

import os
import logging
from logging.handlers import RotatingFileHandler

from . import __app_name__

# ---------------------------------------------------------------------------- #

LOG_DIR = "/var/log/%s" % __app_name__


def set_logging(component, logging_level=logging.DEBUG):
    """ Configure logging

        :param component: name of a component
        :type component: str
        :param logging_level: loglevel
        :type logging_level: int

    """

    if not os.path.isdir(LOG_DIR) or not os.access(LOG_DIR, os.W_OK):
        log_handler = logging.NullHandler()
        log_file = ""
    else:
        log_file = "/var/log/blivet-gui/%s.log" % component

        rotate = os.path.isfile(log_file)

        log_handler = RotatingFileHandler(log_file, backupCount=5)
        log_handler.setLevel(logging_level)
        formatter = logging.Formatter('%(levelname)s:%(name)s: %(message)s')
        log_handler.setFormatter(formatter)

        if rotate:
            log_handler.doRollover()

    logger = logging.getLogger(component)
    logger.addHandler(log_handler)
    logger.setLevel(logging_level)

    return log_file, logger
