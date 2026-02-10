# other_dialogs.py
# misc Gtk.Dialog classes
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
from blivetgui import __version__

from ..i18n import _

from blivet.formats.disklabel import DiskLabel

# ---------------------------------------------------------------------------- #


class AboutDialog:
    """ Standard 'about application' dialog
    """

    def __init__(self, parent_window, version):

        builder = Gtk.Builder()
        builder.set_translation_domain("blivet-gui")
        builder.add_from_file(locate_ui_file('about_dialog.ui'))
        dialog = builder.get_object("about_dialog")

        dialog.set_transient_for(parent_window)
        # TRANSLATORS: This will appear in the About dialog in the Credits section. You should enter
        # your name and email address (optional) here. Separate translator names with newlines.
        dialog.set_translator_credits(_("translator-credits"))
        dialog.set_version(version)

        dialog.show_all()
        dialog.run()
        dialog.destroy()


class SystemInformationDialog(Gtk.Dialog):
    """ Dialog showing system and application information
    """

    def __init__(self, parent_window, blivet_gui):
        """
            :param parent_window: parent window
            :type parent_window: Gtk.Window
            :param blivet_gui: BlivetGUI instance
            :type blivet_gui: BlivetGUI
        """

        self.blivet_gui = blivet_gui
        self.current_row = 0

        # Initialize dialog
        Gtk.Dialog.__init__(self)
        self.set_transient_for(parent_window)
        self.set_border_width(10)
        self.set_title(_("System Information"))
        self.add_buttons(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)

        # Create grid for information layout
        self.grid = Gtk.Grid(column_homogeneous=False, row_spacing=10, column_spacing=20)
        self.grid.set_margin_start(15)
        self.grid.set_margin_end(15)

        box = self.get_content_area()
        box.add(self.grid)

        # Add information sections
        self._add_version_info()
        self._add_startup_options()

        # Show dialog
        self.show_all()
        self.run()
        self.destroy()

    def _add_section_header(self, title):
        """ Add a section header to the grid
            :param title: section title
            :type title: str
        """
        header_label = Gtk.Label()
        header_label.set_markup("<b>%s</b>" % title)
        header_label.set_xalign(0)
        header_label.set_yalign(0)
        self.grid.attach(header_label, left=0, top=self.current_row, width=2, height=1)
        self.current_row += 1

    def _add_info_row(self, label_text, value_text, tooltip_text=None):
        """ Add a label-value row to the grid
            :param label_text: label for the information
            :type label_text: str
            :param value_text: value to display
            :type value_text: str
            :param tooltip_text: tooltip for the label
            :type tooltip_text: str
        """
        # Label
        label = Gtk.Label()
        label.set_markup("  <i>%s:</i>" % label_text)
        label.set_xalign(0)
        label.set_yalign(0)
        self.grid.attach(label, left=0, top=self.current_row, width=1, height=1)
        if tooltip_text:
            label.set_tooltip_markup(tooltip_text)

        # Value
        value_label = Gtk.Label(label=value_text)
        value_label.set_xalign(0)
        value_label.set_yalign(0)
        self.grid.attach(value_label, left=1, top=self.current_row, width=1, height=1)

        self.current_row += 1

    def _add_version_info(self):
        """ Add version information section
        """
        self._add_section_header(_("Version Information"))

        # blivet-gui version
        self._add_info_row(_("blivet-gui"), __version__)

        # blivet version
        try:
            blivet_version = self.blivet_gui.client.remote_call("get_blivet_version")
            self._add_info_row(_("blivet"), blivet_version)
        except Exception:  # pylint: disable=broad-except
            self._add_info_row(_("blivet"), _("Unknown"))

        self.current_row += 1

    def _add_startup_options(self):
        """ Add startup options section
        """
        self._add_section_header(_("Startup Options"))

        # Exclusive disks
        if self.blivet_gui.exclusive_disks:
            disks_value = ", ".join(self.blivet_gui.exclusive_disks)
        else:
            disks_value = _("None (all disks)")
        self._add_info_row(_("Exclusive disks"),
                           disks_value,
                           _("Selection of disks blivet-gui is allowed to operate with"))

        # Auto device updates
        auto_updates = self.blivet_gui.flags.get("auto_dev_updates", False)
        self._add_info_row(_("Advanced device information"),
                           _("Yes") if auto_updates else _("No"),
                           _("Whether gathering all information about devices is enabled, even if it requires potentially dangerous operations like mounting or a filesystem check"))

        self.current_row += 1


class AddLabelDialog:
    """ Dialog window allowing user to add disklabel to disk
    """

    def __init__(self, parent_window):
        """

            :param parent_window: parent window
            :type parent_window: Gtk.Window

        """

        builder = Gtk.Builder()
        builder.set_translation_domain("blivet-gui")
        builder.add_from_file(locate_ui_file('add_disklabel_dialog.ui'))
        self.dialog = builder.get_object("dialog")
        self.pttype_combo = builder.get_object("pttype_combo")

        self.dialog.set_transient_for(parent_window)

        for disklabel in DiskLabel.get_platform_label_types():
            self.pttype_combo.append_text(disklabel)

        self.pttype_combo.set_active(0)

        self.dialog.show_all()

    def set_decorated(self, decorated):
        self.dialog.set_decorated(decorated)

    def run(self):
        response = self.dialog.run()
        label = self.pttype_combo.get_active_text()

        self.dialog.destroy()

        if response == Gtk.ResponseType.OK:
            return label
        else:
            return None


class LuksPassphraseDialog:
    """ Dialog window allowing user to enter passphrase to decrypt
    """

    def __init__(self, parent_window):
        """

            :param parent_window: parent window
            :type parent_window: Gtk.Window

        """

        builder = Gtk.Builder()
        builder.set_translation_domain("blivet-gui")
        builder.add_from_file(locate_ui_file('luks_passphrase_dialog.ui'))
        self.dialog = builder.get_object("dialog")

        self.dialog.set_transient_for(parent_window)

        self.entry_passphrase = builder.get_object("entry_passphrase")
        self.dialog.show_all()

    def set_decorated(self, decorated):
        self.dialog.set_decorated(decorated)

    def run(self):

        response = self.dialog.run()
        passphrase = self.entry_passphrase.get_text()
        self.dialog.destroy()

        if response == Gtk.ResponseType.OK:
            return passphrase

        else:
            return None
