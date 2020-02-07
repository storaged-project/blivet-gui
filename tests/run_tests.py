#!/usr/bin/python3

from __future__ import print_function

import os
import six
import sys
import argparse
import unittest


def _get_tests_from_suite(suite, tests):
    """ Extract tests from the test suite """
    # 'tests' we get from 'unittest.defaultTestLoader.discover' are "wrapped"
    # in multiple 'unittest.suite.TestSuite' classes/lists so we need to "unpack"
    # the indivudual test cases
    for test in suite:
        if isinstance(test, unittest.suite.TestSuite):
            _get_tests_from_suite(test, tests)

        if isinstance(test, unittest.TestCase):
            tests.append(test)

    return tests


def parse_args():
    argparser = argparse.ArgumentParser(description="Blivet-GUI test suite")
    argparser.add_argument("testname", nargs="?",
                           help="name of test class or method (e. g. 'blivetutils_tests.edit_dialog_test')")
    argparser.add_argument("-i", "--installed", dest="installed",
                           help="run tests against installed version of libblockdev",
                           action="store_true")
    return argparser.parse_args()


def main():
    testdir = os.path.abspath(os.path.dirname(__file__))
    projdir = os.path.abspath(os.path.normpath(os.path.join(testdir, "..")))

    suite = unittest.TestSuite()
    args = parse_args()

    if not args.installed and "PYTHONPATH" not in os.environ:
        os.environ["PYTHONPATH"] = projdir  # pylint: disable=environment-modify

        try:
            pyver = "python3" if six.PY3 else "python"
            os.execv(sys.executable, [pyver] + sys.argv)
        except OSError as e:
            print("Failed re-exec with a new PYTHONPATH: %s" % str(e))
            sys.exit(1)

    testdir = os.path.abspath(os.path.dirname(__file__))

    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    test_cases = loader.discover(start_dir=testdir, pattern='*test*.py')

    tests = []
    tests = _get_tests_from_suite(test_cases, tests)

    for test in tests:
        if args.testname and not test.id().startswith(args.testname):
            continue

        suite.addTest(test)

    result = unittest.TextTestRunner(verbosity=2).run(suite)

    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
