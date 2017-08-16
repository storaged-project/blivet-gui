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

from blivet.devices.storage import StorageDevice

from .communication.proxy_utils import ProxyDataContainer
from .config import config

# ---------------------------------------------------------------------------- #


def set_logging(component, logging_level=logging.DEBUG):
    """ Configure logging

        :param component: name of a component
        :type component: str
        :param logging_level: loglevel
        :type logging_level: int

    """

    if not os.path.isdir(config.log_dir) or not os.access(config.log_dir, os.W_OK):
        log_handler = logging.NullHandler()
        log_file = ""
    else:
        log_file = os.path.join(config.log_dir, "%s.log" % component)

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


def _unpack_input(user_input, level, devices, message):
    # value is a list --> just unpack all its items
    if isinstance(user_input, (list, tuple)):
        for i in user_input:
            message, devices = _unpack_input(i, level, devices, message)

    # value is a dict or our "container" --> unpack to print key-value pairs
    elif isinstance(user_input, (dict, ProxyDataContainer)):
        message += "\n"
        for item in user_input:
            message += "\t" * level
            message += "%s:" % item

            # we don't want to save passphrase to the log
            if item == "passphrase" and user_input[item]:
                value = "*****"
            else:
                value = user_input[item]

            message, devices = _unpack_input(value, level + 1, devices, message)

    else:
        # and finally append value to the message
        message += " %s\n" % user_input

        # if value is actually a blivet device, save it for future use
        if isinstance(user_input, StorageDevice):
            devices.append(user_input)

    return (message, devices)


def log_utils_call(log, message, user_input):
    devices = []
    message += "=" * 80
    message += "\n"

    try:
        if user_input is not None:
            message += "**User input:**\n"
            message, devices = _unpack_input(user_input, 1, devices, message)
            message += "\n"

        if devices:
            message += "**Involved devices:**\n\n"
            for device in devices:
                message += repr(device)
                message += "\n"
    except Exception as e:  # pylint: disable=broad-except
        # really don't want to crash because of a logging issue
        log.debug("Logging failed: %s", str(e))
    else:
        log.debug(message)
