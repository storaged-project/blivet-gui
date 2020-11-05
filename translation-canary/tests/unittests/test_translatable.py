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
# Red Hat Author(s): David Shea <dshea@redhat.com>

import unittest
import unittest.mock
from polib import POEntry, POFile
import tempfile

from translation_canary.translatable.test_markup import test_markup
from translation_canary.translatable.test_comment import test_comment

from translation_canary.translatable import testString, testPOT

class TestMarkup(unittest.TestCase):
    def test_ok(self):
        """
        Makes a ok ok ok message.

        Args:
            self: (todo): write your description
        """
        # no markup
        test_markup(POEntry(msgid="test string"))

        # internal markup
        test_markup(POEntry(msgid="<b>test</b> string"))

    def test_unnecessary_markup(self):
        """
        Marks a test as read.

        Args:
            self: (todo): write your description
        """
        self.assertRaises(AssertionError, test_markup, POEntry(msgid="<b>test string</b>"))

class TestComment(unittest.TestCase):
    def test_ok(self):
        """
        The test token.

        Args:
            self: (todo): write your description
        """
        # Perfectly fine string
        test_comment(POEntry(msgid="Hello, I am a test string"))

        # single-character string with a comment
        test_comment(POEntry(msgid="c", comment="TRANSLATORS: 'c' to continue"))

    def test_no_comment(self):
        """
        Ens if a test.

        Args:
            self: (todo): write your description
        """
        self.assertRaises(AssertionError, test_comment, POEntry(msgid="c"))

# Test the top-level functions
# fake tests for testing with
def _true_test(_s):
    """
    True if the given string is a test.

    Args:
        _s: (todo): write your description
    """
    pass

def _false_test(_s):
    """
    Evaluate a test.

    Args:
        _s: (todo): write your description
    """
    raise AssertionError("no good")

def _picky_test(s):
    """
    Raise a test.

    Args:
        s: (array): write your description
    """
    if s.msgstr.startswith("p"):
        raise AssertionError("I don't like this one")

class TestTestString(unittest.TestCase):
    @unittest.mock.patch("translation_canary.translatable._tests", [_true_test])
    def test_success(self):
        """
        Synchronously run a success.

        Args:
            self: (todo): write your description
        """
        self.assertTrue(testString(POEntry()))

    @unittest.mock.patch("translation_canary.translatable._tests", [_false_test])
    def test_failure(self):
        """
        Asserts that the failure.

        Args:
            self: (todo): write your description
        """
        self.assertFalse(testString(POEntry()))

@unittest.mock.patch("translation_canary.translatable._tests", [_picky_test])
class TestTestPOT(unittest.TestCase):
    def test_success(self):
        """
        Test for test test.

        Args:
            self: (todo): write your description
        """
        with tempfile.NamedTemporaryFile(suffix=".pot") as potfile:
            poobj = POFile()
            poobj.append(POEntry(msgstr="test string"))
            poobj.save(potfile.name)

            self.assertTrue(testPOT(potfile.name))

    def test_some_failure(self):
        """
        Create a failure in testfile

        Args:
            self: (todo): write your description
        """
        with tempfile.NamedTemporaryFile(suffix=".pot") as potfile:
            poobj = POFile()
            poobj.append(POEntry(msgstr="test string"))
            poobj.append(POEntry(msgstr="pest string"))
            poobj.save(potfile.name)

            self.assertFalse(testPOT(potfile.name))

    def test_all_failure(self):
        """
        Test for all test files to testfile

        Args:
            self: (todo): write your description
        """
        with tempfile.NamedTemporaryFile(suffix=".pot") as potfile:
            poobj = POFile()
            poobj.append(POEntry(msgstr="pest string"))
            poobj.append(POEntry(msgstr="past string"))
            poobj.save(potfile.name)

            self.assertFalse(testPOT(potfile.name))
