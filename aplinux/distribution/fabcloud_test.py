# -*- coding:utf-8 -*-

from . import fabcloud
from unittest import TestCase
from unittest.mock import MagicMock


class TestTemporyNodeInit(TestCase):

    def test_init(self):
        driver = MagicMock()
        node_kwargs = {'image': 'foo', 'size': 'blah'}
        node_manager = fabcloud.TemporyNodeManager(driver, **node_kwargs)
        self.assertEqual(node_manager.driver, driver)
        self.assertEqual(node_manager.node_kwargs, node_kwargs)
        self.assertIsNone(node_manager.node)


class TestSimpleTemporyNodePreStart(TestCase):

    def setUp(self):
        self.driver = MagicMock()
        self.node_kwargs = {'image': 'foo'}
        self.node_manager = fabcloud.TemporyNodeManager(self.driver, **self.node_kwargs)

    def test_tempory_node_start(self):
        self.node_manager.start()
        self.driver.create_node.assert_called_with(**self.node_kwargs)
        expected_node = self.driver.create_node.return_value
        self.assertEqual(self.node_manager.node, expected_node)
