# -*- coding:utf-8 -*-

from . import fabcloud
from unittest import TestCase
from unittest.mock import MagicMock


class TestTemporyNode(TestCase):

    def test_init(self):
        driver = MagicMock()
        node_kwargs = {'image': 'foo', 'size': 'blah'}
        node = fabcloud.TemporyNode(driver, **node_kwargs)
        self.assertEqual(node.driver, driver)
        self.assertEqual(node.node_kwargs, node_kwargs)
