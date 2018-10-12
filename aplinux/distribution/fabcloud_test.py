# -*- coding:utf-8 -*-

from . import fabcloud
from unittest import TestCase
from unittest.mock import MagicMock
from unittest.mock import patch


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
        self.assertIsNone(node_manager.ip_address)


class TestSimpleTemporyNodePreStart(TestCase):

    def setUp(self):
        self.driver = MagicMock()
        key_pair = MagicMock()
        self.node_kwargs = {'image': 'foo'}
        self.node_manager = fabcloud.TemporyNodeManager(self.driver, key_pair, **self.node_kwargs)

    def test_tempory_node_create(self):
        self.node_manager.create()
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
        self.node.public_ips = ['111.222.333.444']
        self.node.private_ips = ['192.168.0.111']
        self.node_manager.node = self.node

    def test_ip_address(self):
        self.assertEqual(self.node_manager.ip_address, '111.222.333.444')

    @patch('fabric.Connection')
    def test_fabric(self, Connection):  # noqa: N803 arg name should be lower case
        connection = self.node_manager.fabric
        self.assertEqual(connection, Connection.return_value)
