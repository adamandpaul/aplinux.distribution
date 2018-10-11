# -*- coding:utf-8 -*-

from . import fabcloud
from unittest import TestCase
from unittest.mock import MagicMock


class TestTemporyNode(TestCase):

    def test_init(self):
        driver = MagicMock()
        node_kwargs = {'image': 'foo', 'size': 'blah'}
        node_manager = fabcloud.TemporyNodeManager(driver, **node_kwargs)
        self.assertEqual(node_manager.driver, driver)
        self.assertEqual(node_manager.node_kwargs, node_kwargs)
