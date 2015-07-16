#!/usr/bin/python3

import sys

from pocketlint import FalsePositive, PocketLintConfig, PocketLinter

class BlivetLintConfig(PocketLintConfig):
    def __init__(self):
        PocketLintConfig.__init__(self)

        self.falsePositives = [ FalsePositive(r"Catching an exception which doesn't inherit from BaseException: (BlockDev|DM|Crypto|Swap|LVM|Btrfs|MDRaid|)Error$"),
                                FalsePositive(r"Instance of 'int' has no .* member$"),
                                FalsePositive(r"No value for argument 'member_count' in unbound method call$"),
                                FalsePositive(r"No value for argument 'smallest_member_size' in unbound method call$"),
                              ]

    @property
    def disabledOptions(self):
        return [ "W0105",           # String statement has no effect
                 "W0110",           # map/filter on lambda could be replaced by comprehension
                 "W0141",           # Used builtin function %r
                 "W0142",           # Used * or ** magic
                 "W0212",           # Access to a protected member of a client class
                 "W0511",           # Used when a warning note as FIXME or XXX is detected.
                 "W0603",           # Using the global statement
                 "W0614",           # Unused import %s from wildcard import
                 "I0011",           # Locally disabling %s
               ]

if __name__ == "__main__":
    conf = BlivetLintConfig()
    linter = PocketLinter(conf)
    rc = linter.run()
    sys.exit(rc)
