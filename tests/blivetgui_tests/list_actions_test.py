# -*- coding: utf-8 -*-

import unittest
from unittest.mock import MagicMock

import os

from blivetgui.i18n import _, P_
from blivetgui.list_actions import ListActions


@unittest.skipUnless("DISPLAY" in os.environ.keys(), "requires X server")
class ListActionsTest(unittest.TestCase):

    buttons_state = None
    actions_label = None

    def _set_buttons_state(self, state):
        """
        Sets the buttons state.

        Args:
            self: (todo): write your description
            state: (str): write your description
        """
        self.buttons_state = state

    def _set_actions_label(self, label):
        """
        Set the actions label.

        Args:
            self: (todo): write your description
            label: (str): write your description
        """
        self.actions_label = label

    def setUp(self):
        """
        Sets the gui actions.

        Args:
            self: (todo): write your description
        """
        self.blivet_gui = MagicMock()
        self.blivet_gui.configure_mock(activate_action_buttons=self._set_buttons_state)
        self.blivet_gui.configure_mock(label_actions=MagicMock(set_markup=self._set_actions_label))

        self.actions_list = ListActions(self.blivet_gui)
        self.actions_list.initialize()

    def test_initial_state(self):
        """
        Initializes the initial state.

        Args:
            self: (todo): write your description
        """
        self.assertFalse(self.buttons_state)
        self.assertIn(_("No pending actions"), self.actions_label)
        self.assertEqual(self.actions_list.actions, 0)
        self.assertEqual(len(self.actions_list.history), 0)

    def test_append(self):
        """
        Append a new test to be run of actions

        Args:
            self: (todo): write your description
        """
        action1 = MagicMock()
        action2 = MagicMock()
        self.actions_list.append(action_type="add", action_desc="add", blivet_actions=[action1, action2])

        self.assertEqual(self.actions_list.actions, 1)
        self.assertEqual(len(self.actions_list.history), 1)
        self.assertTrue([action1, action2] in self.actions_list.history)
        self.assertTrue(self.buttons_state)
        self.assertIn(P_("%s pending action", "%s pending actions", 1) % 1, self.actions_label)

    def test_pop(self):
        """
        Perform actions from the list.

        Args:
            self: (todo): write your description
        """
        action1 = MagicMock()
        self.actions_list.append(action_type="add", action_desc="add", blivet_actions=[action1])
        action2 = MagicMock()
        self.actions_list.append(action_type="add", action_desc="add", blivet_actions=[action2])

        # pop action2 from the list
        pop = self.actions_list.pop()
        self.assertEqual(pop, [action2])
        self.assertEqual(self.actions_list.actions, 1)
        self.assertEqual(len(self.actions_list.history), 1)
        self.assertTrue([action1] in self.actions_list.history)  # action1 should stay there
        self.assertFalse([action2] in self.actions_list.history)  # action2 shouldn't
        self.assertTrue(self.buttons_state)
        self.assertIn(P_("%s pending action", "%s pending actions", 1) % 1, self.actions_label)

        # pop action1 from the list
        pop = self.actions_list.pop()
        self.assertEqual(pop, [action1])
        self.assertEqual(self.actions_list.actions, 0)
        self.assertEqual(len(self.actions_list.history), 0)
        self.assertFalse(self.buttons_state)
        self.assertIn(_("No pending actions"), self.actions_label)

    def test_clear(self):
        """
        Clears the actions.

        Args:
            self: (todo): write your description
        """
        action1 = MagicMock()
        self.actions_list.append(action_type="add", action_desc="add", blivet_actions=[action1])

        self.actions_list.clear()
        self.assertEqual(self.actions_list.actions, 0)
        self.assertEqual(len(self.actions_list.history), 0)
        self.assertFalse(self.buttons_state)
        self.assertIn(_("No pending actions"), self.actions_label)


if __name__ == "__main__":
    unittest.main()
