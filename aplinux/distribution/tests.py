# -*- coding: utf-8 -*-
"""Test Suite for this package

Auto discover tests in this package
"""

import doctest
import fnmatch
import os.path
import pkg_resources
import unittest


PACKAGE_NAME = 'aplinux.distribution'


def test_suite_test_cases(package_name=PACKAGE_NAME, pattern='*_test.py'):
    """Create the test suite used for the test runer

    Discover tests and load them into a test suite.

    Args:
        package_name (str): The package we are interested in loading a test suite for
        pattern (str): The glob patten used for test discovery

    Returns:
        TestSuite: The test suite to be used for the test runner
    """

    # The egg info object is needed to get the top_level_dir value
    environment = pkg_resources.Environment()
    assert len(environment[package_name]), 'we should only have a single environment to deal with'
    this_egg_info = environment[package_name][0]

    # Find the top_level_dir, because namespaces don't work too good with unittest
    top_level_dir = this_egg_info.location

    test_loader = unittest.TestLoader()
    suite = test_loader.discover(package_name,
                                 pattern=pattern,
                                 top_level_dir=top_level_dir)

    return suite


def test_suite_doctest_folder(package_name=PACKAGE_NAME, path='doctests', pattern='*_test.rst'):
    """Create an test suite from a doctest folder

    These are heavier weight tests designed  to make sure all the components a re  working togeths

    Args:
        package_name (str): The package we are interested in loading a test suite for
        pattern (str): The glob patten used for test discovery

    Returns:
        TestSuite: The test suite to be used for the test runner
    """
    doctest_files = []
    base_dir = pkg_resources.resource_filename(package_name, path)
    for item_name in pkg_resources.resource_listdir(package_name, path):
        if fnmatch.fnmatch(item_name, pattern):
            doctest_file = os.path.join(base_dir, item_name)
            doctest_files.append(doctest_file)
    option_flags = doctest.NORMALIZE_WHITESPACE | doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS
    suite = doctest.DocFileSuite(*doctest_files,
                                 module_relative=False,
                                 optionflags=option_flags)
    return suite


def test_suite(package_name=PACKAGE_NAME):
    """The default test suite. Do unittesting"""
    return test_suite_test_cases(package_name,
                                 pattern='*_test.py')


def integration_test_suite(package_name=PACKAGE_NAME):
    """Do integration testing"""
    return unittest.TestSuite([
        test_suite_test_cases(package_name,
                              pattern='*_inttest.py'),
        test_suite_doctest_folder(package_name,
                                  path='integration_test',
                                  pattern='*_inttest.rst'),
    ])
