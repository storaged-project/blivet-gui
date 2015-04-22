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
#------------------------------------------------------------------------------#

from __future__ import print_function

import os

import logging

import meh
import meh.handler
import meh.dump
import meh.ui.gui

import atexit

#------------------------------------------------------------------------------#

APP_NAME='blivet-gui'
APP_VERSION='0.2.4'

#------------------------------------------------------------------------------#

def set_logging(component, logging_level=logging.DEBUG, log_file=None):
    """ Configure logging

        :param component: name of a component
        :type component: str
        :param logging_level: loglevel
        :type logging_level: int
        :param log_file: name of log file
        :type log_file: str

    """

    if not log_file:
        log_file = "/tmp/" + component + ".log"

    while os.path.isfile(log_file):
        if not log_file[-1].isdigit():
            log_file += ".0"

        else:
            num = int(log_file.split(".")[-1])
            name = ".".join(log_file.split(".")[:-1])
            log_file = name + "." + str(num + 1)

    log_handler = logging.FileHandler(log_file)
    log_handler.setLevel(logging_level)
    formatter = logging.Formatter('%(levelname)s:%(name)s: %(message)s')
    log_handler.setFormatter(formatter)

    logger = logging.getLogger(component)
    logger.addHandler(log_handler)
    logger.setLevel(logging_level)

    return log_file, logger

def set_python_meh(log_files):
    """ Configure python-meh

        :param log_files: list of log files to send
        :type log_files: list of str

    """
    config = meh.Config(programName=APP_NAME, programVersion=APP_VERSION, programArch="noarch",
                        localSkipList=["passphrase"],
                        fileList=log_files)

    intf = meh.ui.gui.GraphicalIntf()

    handler = meh.handler.ExceptionHandler(config, intf, meh.dump.ExceptionDump)

    return handler

def remove_logs(log_files):
    """ Remove log files

        :param log_files: list of log files to delete
        :type log_files: list of str

    """

    try:
        for log_file in log_files:
            os.remove(log_file)

    except OSError as e:
        print("Failed to remove log file\n" + str(e))

def remove_atexit(log_files):
    """ Remove log files using atexit

        :param log_files: list of log files to delete
        :type log_files: list of str

    """

    atexit.register(remove_logs, log_files)
