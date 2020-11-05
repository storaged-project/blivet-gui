#!/usr/bin/python3

import sys
from pocketlint import PocketLintConfig, PocketLinter

class TranslationCanaryLintConfig(PocketLintConfig):
    @property
    def disabledOptions(self):
        """
        Return the list of disabled options.

        Args:
            self: (todo): write your description
        """
        return [ "I0011",           # Locally disabling %s
               ]

    @property
    def extraArgs(self):
        """
        Returns extra extra arguments.

        Args:
            self: (todo): write your description
        """
        return ["--init-import", "y"]

if __name__ == "__main__":
    conf = TranslationCanaryLintConfig()
    linter = PocketLinter(conf)
    rc = linter.run()
    sys.exit(rc)
