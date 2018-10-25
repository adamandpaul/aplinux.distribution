# -*- coding:utf-8 -*-

from . import node_manager
from libcloud.compute.types import NodeState
from unittest import TestCase
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch


class TestTemporyNodeInit(TestCase):

    def test_init(self):
        driver = MagicMock()
        key_pair = MagicMock()
        node_kwargs = {'image': 'foo', 'size': 'blah'}
        nm = node_manager.TemporyNode(driver, 'centos', key_pair, **node_kwargs)
        self.assertEqual(nm.driver, driver)
        self.assertEqual(nm.user, 'centos')
        self.assertEqual(nm.key_pair, key_pair)
        self.assertEqual(nm.node_kwargs, node_kwargs)
        self.assertIsNone(nm.node)
        self.assertIsNone(nm.fabric)
        self.assertIsNone(nm.ip_address)


class TestSimpleTemporyNodePreStart(TestCase):

    def setUp(self):
        self.driver = MagicMock()
        key_pair = MagicMock()
        self.node_kwargs = {'image': 'foo'}
        self.node_manager = node_manager.TemporyNode(self.driver, 'centos', key_pair, **self.node_kwargs)

    @patch('uuid.uuid4')
    def test_tempory_node_create(self, uuid4):
        uuid4.return_value = '1234'
        self.node_manager.create()
        self.driver.create_node.assert_called_with(name='tempory-node-1234', **self.node_kwargs)
        expected_node = self.driver.create_node.return_value
        self.assertEqual(self.node_manager.node, expected_node)
        self.driver.wait_until_running.assert_called_with([expected_node])

    def test_context_enter(self):
        self.node_manager.create = MagicMock()
        result = self.node_manager.__enter__()
        self.node_manager.create.assert_called_with()
        self.assertEqual(result, self.node_manager)

    def test_context_exit(self):
        self.node_manager.destroy = MagicMock()
        self.node_manager.__exit__(None, None, None)
        self.node_manager.destroy.assert_not_called()


class TestSimpleTemporyNodeRunning(TestCase):

    def setUp(self):
        self.driver = MagicMock()
        self.key_pair = MagicMock()
        self.node_kwargs = {'image': 'foo'}
        self.node_manager = node_manager.TemporyNode(self.driver, 'centos', self.key_pair, **self.node_kwargs)
        self.node = MagicMock()
        self.node.public_ips = ['111.222.333.444']
        self.node.private_ips = ['192.168.0.111']
        self.node_manager.node = self.node

    def test_refresh_node(self):
        other_node = MagicMock()
        fresh_node = MagicMock()
        fresh_node.id = self.node.id
        self.node.driver.list_nodes.return_value = [other_node, fresh_node]
        self.node_manager.refresh_node()
        self.assertEqual(self.node_manager.node, fresh_node)

    @patch('time.sleep')
    def test_destroy(self, sleep):
        self.node.state = NodeState.TERMINATED  # preset to terminated so that the destroy method returns
        self.node_manager.refresh_node = Mock()
        self.node_manager.destroy()
        self.node.destroy.aseert_called_with()
        sleep.assert_called_with(5)
        self.node_manager.refresh_node.assert_called_with()

    def test_context_exit(self):
        self.node_manager.destroy = MagicMock()
        self.node_manager.__exit__(None, None, None)
        self.node_manager.destroy.assert_called_with()

    def test_context_exit_with_error(self):
        self.node_manager.destroy = MagicMock()
        expected_exception = Exception()
        self.node_manager.destroy.side_effect = [expected_exception]
        with self.assertRaises(node_manager.NodeManagerCleanupError):
            self.node_manager.__exit__(None, None, None)

    def test_ip_address(self):
        self.assertEqual(self.node_manager.ip_address, '111.222.333.444')

    def test_set_ipaddress(self):
        self.node_manager.ip_address = 'foo'
        self.assertEqual(self.node_manager.ip_address, 'foo')

        # a ip_address of None should cause a recalculation
        self.node_manager.ip_address = None
        self.assertEqual(self.node_manager.ip_address, '111.222.333.444')

    @patch('fabric.Connection')
    @patch('paramiko.RSAKey')
    def test_fabric(self, RSAKey, Connection):  # noqa: N803 arg name should be lower case
        self.key_pair.private_key = 'abc'
        pkey = RSAKey.from_private_key.return_value
        connection = self.node_manager.fabric
        Connection.assert_called_with(self.node_manager.ip_address,
                                      user='centos',
                                      connect_kwargs={'pkey': pkey,
                                                      'look_for_keys': False})
        self.assertEqual(connection, Connection.return_value)
