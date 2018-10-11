# -*- coding:utf-8 -*-

from . import fabcloud
from unittest import TestCase
from unittest.mock import MagicMock


class TestTemporyNodeInit(TestCase):

    def test_init(self):
        driver = MagicMock()
        key_pair = MagicMock()
        node_kwargs = {'image': 'foo', 'size': 'blah'}
        node_manager = fabcloud.TemporyNodeManager(driver, key_pair, **node_kwargs)
        self.assertEqual(node_manager.driver, driver)
        self.assertEqual(node_manager.key_pair, key_pair)
        self.assertEqual(node_manager.node_kwargs, node_kwargs)
        self.assertIsNone(node_manager.node)
        self.assertIsNone(node_manager.fabric)


class TestSimpleTemporyNodePreStart(TestCase):

    def setUp(self):
        self.driver = MagicMock()
        key_pair = MagicMock()
        self.node_kwargs = {'image': 'foo'}
        self.node_manager = fabcloud.TemporyNodeManager(self.driver, key_pair, **self.node_kwargs)

    def test_tempory_node_start(self):
        self.node_manager.start()
        self.driver.create_node.assert_called_with(**self.node_kwargs)
        expected_node = self.driver.create_node.return_value
        self.assertEqual(self.node_manager.node, expected_node)
        self.driver.wait_until_running.assert_called_with(expected_node)


class TestSimpleTemporyNodeRunning(TestCase):

    def setUp(self):
        self.driver = MagicMock()
        key_pair = MagicMock()
        self.node_kwargs = {'image': 'foo'}
        self.node_manager = fabcloud.TemporyNodeManager(self.driver, key_pair, **self.node_kwargs)
        self.node = MagicMock()
        self.node_manager.node = self.node

    def test_ip_address(self):
        self.node.public_ips = ['111.222.333.444']
        self.node.private_ips = ['192.168.0.111']
        self.assertEqual(self.node_manager.ip_address, '111.222.333.444')
