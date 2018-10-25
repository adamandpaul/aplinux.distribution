# -*- coding: utf-8 -*-
"""Test Suite for this package

Auto discover tests in this package
"""

import doctest
import fnmatch
import os.path
import pkg_resources
import unittest


def test_suite(package_name='aplinux.distribution', pattern='*_test.py'):
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


def integration_test_suite(package='aplinux.distribution', doctests_path='integration_test', doctest_pattern='*_inttest.rst'):
    """Create an test suite for integration

    These are heavier weight tests designed  to make sure all the components a re  working togeths

    Args:
        package_name (str): The package we are interested in loading a test suite for
        pattern (str): The glob patten used for test discovery

    Returns:
        TestSuite: The test suite to be used for the test runner
    """
    doctest_files = []
    base_dir = pkg_resources.resource_filename(package, doctests_path)
    for item_name in pkg_resources.resource_listdir(package, doctests_path):
        if fnmatch.fnmatch(item_name, doctest_pattern):
            doctest_file = os.path.join(base_dir, item_name)
            doctest_files.append(doctest_file)
    suite = doctest.DocFileSuite(*doctest_files, module_relative=False)
    return suite
