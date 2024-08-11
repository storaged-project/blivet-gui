# -*- coding: utf-8 -*-
# message_dialogs.py
# misc Gtk.MessageDialogs
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

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk

from blivetgui.gui_utils import locate_ui_file
from .helpers import adjust_scrolled_size
from .constants import DialogResponseType
from ..communication.proxy_utils import ProxyDataContainer

from ..i18n import _

# ---------------------------------------------------------------------------- #


class WarningDialog(object):
    """ Basic warning dialog
    """

    def __init__(self, parent_window, msg, decorated=True):

        builder = Gtk.Builder()
        builder.set_translation_domain("blivet-gui")
        builder.add_from_file(locate_ui_file('warning_dialog.ui'))
        dialog = builder.get_object("warning_dialog")

        dialog.set_decorated(decorated)
        dialog.set_transient_for(parent_window)
        dialog.format_secondary_text(msg)

        dialog.show_all()
        dialog.run()
        dialog.destroy()


class ErrorDialog(object):
    """ Basic error dialog
    """

    def __init__(self, parent_window, msg, decorated=True):

        builder = Gtk.Builder()
        builder.set_translation_domain("blivet-gui")
        builder.add_from_file(locate_ui_file('error_dialog.ui'))
        dialog = builder.get_object("error_dialog")

        dialog.set_decorated(decorated)
        dialog.set_transient_for(parent_window)
        dialog.format_secondary_text(msg)

        dialog.show_all()
        dialog.run()
        dialog.destroy()


class InfoDialog(object):
    """ Basic error dialog
    """

    def __init__(self, parent_window, msg, decorated=True):

        builder = Gtk.Builder()
        builder.set_translation_domain("blivet-gui")
        builder.add_from_file(locate_ui_file('info_dialog.ui'))
        dialog = builder.get_object("info_dialog")

        dialog.set_decorated(decorated)
        dialog.set_transient_for(parent_window)
        dialog.format_secondary_text(msg)

        dialog.show_all()
        dialog.run()
        dialog.destroy()


class ExceptionDialog(object):
    """ Error dialog with traceback
    """

    def __init__(self, parent_window, allow_ignore, allow_report, msg, traceback, decorated=True):

        self.allow_ignore = allow_ignore
        self.allow_report = allow_report

        builder = Gtk.Builder()
        builder.set_translation_domain("blivet-gui")
        builder.add_from_file(locate_ui_file('exception_dialog.ui'))
        self.dialog = builder.get_object("exception_dialog")

        self.dialog.set_decorated(decorated)
        self.dialog.set_transient_for(parent_window)
        self.dialog.format_secondary_text(msg)

        exception_label = builder.get_object("exception_label")
        exception_label.set_text(traceback)

        self.button_back = builder.get_object("button_back")
        self.button_back.connect("clicked", self._on_back_button)

        self.button_report = builder.get_object("button_report")
        self.button_report.connect("clicked", self._on_report_button)

        button_quit = builder.get_object("button_quit")
        button_quit.connect("clicked", self._on_quit_button)

        report_label = builder.get_object("bugreport_label")
        if allow_report:
            msg = _("If you believe this is a bug, please use the 'Report a bug' button "
                    "below to report a bug using the\nAutomatic bug reporting tool (ABRT) "
                    "or open an issue on our "
                    "<a href=\"https://github.com/storaged-project/blivet-gui/issues\">GitHub</a>.")
        else:
            msg = _("If you believe this is a bug, please open an issue on our "
                    "<a href=\"https://github.com/storaged-project/blivet-gui/issues\">GitHub</a>.")

        report_label.set_markup("<i>%s</i>" % msg)

    def run(self):
        self.dialog.show_all()

        # hide buttons
        if not self.allow_ignore:
            self.button_back.hide()

        if not self.allow_report:
            self.button_report.hide()

        response = self.dialog.run()
        self.dialog.destroy()

        return response

    def _on_back_button(self, _button):
        self.dialog.response(DialogResponseType.BACK)

    def _on_report_button(self, _button):
        self.dialog.response(DialogResponseType.REPORT)

    def _on_quit_button(self, _button):
        self.dialog.response(DialogResponseType.QUIT)


class ConfirmDialog(object):
    """ General confirmation dialog
    """

    def __init__(self, parent_window, title, msg, decorated=True):

        builder = Gtk.Builder()
        builder.set_translation_domain("blivet-gui")
        builder.add_from_file(locate_ui_file('confirm_dialog.ui'))
        self.dialog = builder.get_object("confirm_dialog")

        self.dialog.set_decorated(decorated)
        self.dialog.set_transient_for(parent_window)
        self.dialog.set_markup("<b>" + title + "</b>")
        self.dialog.format_secondary_text(msg)

        self.dialog.show_all()

    def run(self):
        """ Run the dialog
        """

        response = self.dialog.run()

        self.dialog.destroy()

        return response == Gtk.ResponseType.OK


class ConfirmDeleteDialog(object):
    """ General confirmation dialog
    """

    def __init__(self, parent_window, device, parents=None, children=None):

        builder = Gtk.Builder()
        builder.set_translation_domain("blivet-gui")
        builder.add_from_file(locate_ui_file('confirm_delete_dialog.ui'))
        self.dialog = builder.get_object("confirm_delete_dialog")

        self.dialog.set_transient_for(parent_window)

        title = _("Confirm delete operation")
        msg = _("Are you sure you want delete device {name}?").format(name=device.name)

        self.dialog.set_markup("<b>" + title + "</b>")
        self.dialog.format_secondary_text(msg)

        self.children_label = builder.get_object("children_label")
        self.parent_check = builder.get_object("parent_check")
        self.parent_label = builder.get_object("parent_label")

        if children:
            children_text = _("Following children of {name} will be also removed by this action:\n").format(name=device.name)
            for child in children:
                children_text += " • {size} {type} {name}\n".format(size=child.size,
                                                                    type=child.type,
                                                                    name=child.name)
            self.children_label.set_label(children_text)

        if parents:
            check_text = _("Also delete following parent devices of {name}:").format(name=device.name)
            self.parent_check.set_label(check_text)
            self.parent_check.set_active(True)

            parent_text = ""
            for parent in parents:
                parent_text += " • {size} {type} {path}\n".format(size=parent.size,
                                                                  type=parent.type,
                                                                  path=parent.path)
            self.parent_label.set_label(parent_text)

        self.dialog.show_all()

        if not children:
            self.children_label.hide()

        if parents is None:
            self.parent_check.hide()
            self.parent_label.hide()

    def set_decorated(self, decorated):
        self.dialog.set_decorated(decorated)

    def run(self):
        """ Run the dialog
        """

        response = self.dialog.run()
        delete = response == Gtk.ResponseType.OK
        delete_parents = self.parent_check.get_active()

        self.dialog.destroy()
        return ProxyDataContainer(delete=delete,
                                  delete_parents=delete_parents)


def show_actions_list(treestore_actions):
    builder = Gtk.Builder()
    builder.set_translation_domain("blivet-gui")
    builder.add_from_file(locate_ui_file("blivet-gui.ui"))

    treeview_actions = builder.get_object("treeview_actions")
    treeview_actions.set_model(treestore_actions)
    treeview_actions.expand_all()

    return treeview_actions


class ConfirmActionsDialog(object):
    """ Confirm execute actions
    """

    def __init__(self, parent_window, title, msg, treestore_actions):
        builder = Gtk.Builder()
        builder.set_translation_domain("blivet-gui")
        builder.add_from_file(locate_ui_file("confirm_actions_dialog.ui"))
        self.dialog = builder.get_object("confirm_actions_dialog")

        self.dialog.set_transient_for(parent_window)
        self.dialog.set_markup("<b>" + title + "</b>")
        self.dialog.format_secondary_text(msg)

        scrolledwindow = builder.get_object("scrolledwindow")

        win_width = int(parent_window.get_allocated_width() * 0.60)
        win_height = int(parent_window.get_allocated_height() * 0.60)

        treeview_actions = show_actions_list(treestore_actions)
        scrolledwindow.add(treeview_actions)

        adjust_scrolled_size(scrolledwindow, win_width, win_height)

        self.dialog.show_all()

        # yes, it is necessary to call this twice, don't know why, just some Gtk magic
        adjust_scrolled_size(scrolledwindow, win_width, win_height)

    def run(self):
        """ Run the dialog
        """

        response = self.dialog.run()
        self.dialog.destroy()

        return response == Gtk.ResponseType.OK


class ShowActionsDialog(object):
    """ Show dialog with scheduled actions
    """

    def __init__(self, parent_window, treestore_actions):
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain("blivet-gui")
        self.builder.add_from_file(locate_ui_file("show_actions_dialog.ui"))
        self.dialog = self.builder.get_object("show_actions_dialog")

        self.dialog.set_transient_for(parent_window)

        if len(treestore_actions) == 0:
            self.dialog.format_secondary_text(_("There are no pending actions."))

        scrolledwindow = self.builder.get_object("scrolledwindow")

        win_width = int(parent_window.get_allocated_width() * 0.60)
        win_height = int(parent_window.get_allocated_height() * 0.60)

        treeview_actions = show_actions_list(treestore_actions)
        scrolledwindow.add(treeview_actions)

        adjust_scrolled_size(scrolledwindow, win_width, win_height)

        self.dialog.show_all()

        # yes, it is necessary to call this twice, don't know why, just some Gtk magic
        adjust_scrolled_size(scrolledwindow, win_width, win_height)

    def set_decorated(self, decorated):
        self.dialog.set_decorated(decorated)

    def run(self):
        """ Run the dialog
        """

        self.dialog.run()
        self.dialog.destroy()


class CustomDialog(object):
    """ Message dialog with custom buttons
    """

    def __init__(self, parent_window, buttons):
        builder = Gtk.Builder()
        builder.set_translation_domain("blivet-gui")
        builder.add_from_file(locate_ui_file("custom_dialog.ui"))
        self.dialog = builder.get_object("custom_dialog")

        self.details = builder.get_object("label_expanded")

        self.dialog.add_buttons(*buttons)

        self.dialog.set_transient_for(parent_window)

    def run(self):
        """ Run the dialog
        """

        response = self.dialog.run()
        self.dialog.destroy()

        return response
