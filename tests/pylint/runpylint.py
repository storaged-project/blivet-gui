#!/usr/bin/python3

import sys

from pocketlint import PocketLintConfig, PocketLinter, FalsePositive


class BlivetGUILintConfig(PocketLintConfig):
    def __init__(self):
        PocketLintConfig.__init__(self)

        self.falsePositives = [FalsePositive(r"Value '.*\.parents_store' is unsubscriptable"),
                               FalsePositive(r"Non-iterable value .*\.parents_store is used in an iterating context"),
                               FalsePositive(r".*Test\..*: Too many positional arguments for method call")]

    @property
    def pylintPlugins(self):
        retval = super(BlivetGUILintConfig, self).pylintPlugins
        retval.remove("pocketlint.checkers.markup")
        return retval

    @property
    def disabledOptions(self):
        return ["W0142",           # Used * or ** magic
                "W0212",           # Access to a protected member of a client class
                "W0511",           # Used when a warning note as FIXME or XXX is detected.
                "I0011",           # Locally disabling %s
                ]

    @property
    def ignoreNames(self):
        return {"translation-canary"}

    @property
    def extraArgs(self):
        return ["--unsafe-load-any-extension=yes"]


if __name__ == "__main__":
    conf = BlivetGUILintConfig()
    linter = PocketLinter(conf)
    rc = linter.run()
    sys.exit(rc)
