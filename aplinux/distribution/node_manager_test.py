# -*- coding:utf-8 -*-

from . import node_manager
from libcloud.compute.base import KeyPair
from libcloud.compute.types import NodeState
from unittest import TestCase
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch


class TestTemporyNodeInit(TestCase):

    def test_init(self):
        driver = MagicMock()
        key_pair = MagicMock()
        create_kwargs = {'ex_colour': 'green', 'ex_shape': 'circle'}
        nm = node_manager.TemporyNode(driver,
                                      name_prefix='temp-foo-',
                                      size='big',
                                      image='linux-foo',
                                      user='boss',
                                      key_pair=key_pair,
                                      **create_kwargs)
        self.assertEqual(nm.driver, driver)
        self.assertEqual(nm.name_prefix, 'temp-foo-')
        self.assertEqual(nm.size, 'big')
        self.assertEqual(nm.image, 'linux-foo')
        self.assertEqual(nm.user, 'boss')
        self.assertEqual(nm.key_pair, key_pair)
        self.assertEqual(nm.create_kwargs, create_kwargs)
        self.assertIsNone(nm.node)
        self.assertIsNone(nm.fabric)
        self.assertIsNone(nm.ip_address)

    @patch('aplinux.distribution.node_manager.StringIO')
    @patch('aplinux.distribution.node_manager.RSAKey')
    def test_key_pair_generation(self, RSAKey, StringIO):  # noqa: N803 arg name should be lower case
        driver = MagicMock()
        nm = node_manager.TemporyNode(driver)
        nm.name = 'foo'
        key_pair = nm.key_pair
        self.assertIsInstance(key_pair, KeyPair)

        # assert we got a 2048 key
        RSAKey.generate.assert_called_with(2048)
        key = RSAKey.generate.return_value

        # key name and fingureprint
        self.assertEqual(key_pair.name, 'key-pair-foo')
        self.assertEqual(key_pair.fingerprint, key.get_fingerprint.return_value)

        # public key
        public_key_base64 = key.get_base64.return_value
        self.assertEqual(key_pair.public_key, f'ssh-rsa {public_key_base64} admin')

        # private key
        private_key_fout = StringIO.return_value
        key.write_private_key.assert_called_with(private_key_fout)
        self.assertEqual(key_pair.private_key, private_key_fout.getvalue.return_value)


class TestSimpleTemporyNodePreStart(TestCase):

    def setUp(self):
        self.driver = MagicMock()
        key_pair = MagicMock()
        self.create_kwargs = {'colour': 'red'}
        self.node_manager = node_manager.TemporyNode(self.driver,
                                                     user='centos',
                                                     size='small',
                                                     image='foo',
                                                     key_pair=key_pair,
                                                     **self.create_kwargs)

    @patch('uuid.uuid4')
    def test_name(self, uuid4):
        uuid4.return_value = '1234'
        self.assertEqual(self.node_manager.name, 'tempory-node-1234')

    def test_tempory_node_create(self):
        self.node_manager.name = 'node-123'
        self.node_manager.create()
        self.driver.create_node.assert_called_with(name='node-123',
                                                   size='small',
                                                   image='foo',
                                                   **self.create_kwargs)
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
        self.node_manager.destroy.assert_called()


class TestSimpleTemporyNodeRunning(TestCase):

    def setUp(self):
        self.driver = MagicMock()
        self.key_pair = MagicMock()
        self.node_kwargs = {'colour': 'blue'}
        self.node_manager = node_manager.TemporyNode(self.driver,
                                                     size='small',
                                                     image='foo',
                                                     user='centos',
                                                     key_pair=self.key_pair,
                                                     **self.node_kwargs)
        self.node = MagicMock()
        self.node.public_ips = ['111.222.333.444']
        self.node.private_ips = ['192.168.0.111']
        self.node_manager.node = self.node

    def test_get_node_by_name(self):
        expected_node = MagicMock()
        expected_node.name = 'foo-123'
        other_node = MagicMock()
        self.driver.list_nodes.return_value = [other_node, expected_node]
        return_node = self.node_manager._get_node_by_name('foo-123')
        self.assertEqual(return_node, expected_node)

    def test_refresh_node(self):
        self.node_manager._get_node_by_name = MagicMock(return_value='123')
        self.node_manager.refresh_node()
        self.assertEqual(self.node_manager.node, '123')

    @patch('time.sleep')
    def test_destroy(self, sleep):
        self.node.state = NodeState.RUNNING
        self.node_manager.refresh_node = Mock()

        def refresh2():
            self.node.state = NodeState.TERMINATED  # preset to terminated so that the destroy method returns

        def refresh1():
            self.node_manager.refresh_node.side_effect = refresh2

        self.node_manager.refresh_node.side_effect = refresh1
        self.node_manager.destroy()
        self.node.destroy.aseert_called_with()
        sleep.assert_called_with(3)
        self.node_manager.refresh_node.assert_called_with()

    @patch('time.sleep')
    def test_destroy_node_disapeared(self, sleep):
        self.node.state = NodeState.RUNNING
        self.node_manager.refresh_node = Mock()

        def refresh2():
            self.node_manager.node = None

        def refresh1():
            self.node_manager.refresh_node.side_effect = refresh2

        self.node_manager.refresh_node.side_effect = refresh1
        self.node_manager.destroy()
        self.node.destroy.aseert_called_with()
        sleep.assert_called_with(3)
        self.node_manager.refresh_node.assert_called_with()

    @patch('time.sleep')
    def test_destroy_node_filed(self, sleep):
        self.node.state = NodeState.RUNNING
        self.node_manager.refresh_node = Mock()
        with self.assertRaises(node_manager.NodeManagerError):
            self.node_manager.destroy()
        self.node.destroy.aseert_called_with()
        sleep.assert_called_with(3)
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


class TestTemporyGCENode(TestCase):

    def setUp(self):
        self.driver = MagicMock()
        self.key_pair = MagicMock()
        self.key_pair.public_key = 'ssh-rsa abcdefg centos'
        self.node_manager = node_manager.TemporyGCENode(self.driver,
                                                        image='foo-bar-7-',
                                                        key_pair=self.key_pair)

    def test_init(self):
        self.assertEqual(self.node_manager.create_kwargs['ex_metadata'],
                         {'items': [{'key': 'ssh-keys',
                                     'value': 'admin:ssh-rsa abcdefg centos'}]})

    def test_image(self):
        expected_image = self.driver.ex_get_image.return_value
        image = self.node_manager.image
        self.driver.ex_get_image.assert_called_with('foo-bar-7-')
        self.assertEqual(image, expected_image)


class TestTemporyEC2Node(TestCase):

    def setUp(self):
        self.driver = MagicMock()
        self.node_manager_kwargs = {
            'image': 'ami-9887c6e7',
            'size': 't3.micro',
        }
        self.node_manager = node_manager.TemporyEC2Node(
            self.driver,
            **self.node_manager_kwargs,
        )
        t2_node = MagicMock()
        self.t3_node = MagicMock()
        self.t3_node.id = 't3.micro'
        self.driver.list_sizes.return_value = [t2_node, self.t3_node]

    def test_init(self):
        self.assertEqual(
            self.node_manager.create_kwargs['ex_blockdevicemappings'],
            [
                {
                    'DeviceName': '/dev/sda1',
                    'Ebs': {'DeleteOnTermination': True},
                },
            ],
        )

    def test_init_security_group_names(self):
        kwargs = self.node_manager_kwargs.copy()
        kwargs['security_group_names'] = 'test group'
        new_node_manager = node_manager.TemporyEC2Node(self.driver, **kwargs)
        self.assertEqual(
            new_node_manager.create_kwargs['ex_security_groups'],
            ['test group'],
        )

    def test_init_security_group_names_list(self):
        kwargs = self.node_manager_kwargs.copy()
        kwargs['security_group_names'] = 'test group|test group2'
        new_node_manager = node_manager.TemporyEC2Node(self.driver, **kwargs)
        self.assertEqual(
            new_node_manager.create_kwargs['ex_security_groups'],
            ['test group', 'test group2'],
        )

    @patch('time.sleep', return_value=None)
    def test_create(self, patched_time_sleep):
        self.node_manager.create()
        self.driver.import_key_pair_from_string.assert_called()

    @patch('builtins.super')
    def test_destroy(self, super):
        self.node_manager.key_pair = MagicMock()
        self.node_manager.destroy()
        super().destroy.assert_called_with()
        self.driver.delete_key_pair.assert_called()

    def test_image(self):
        expected_image = self.driver.get_image.return_value
        image = self.node_manager.image
        self.driver.get_image.assert_called_with('ami-9887c6e7')
        self.assertEqual(image, expected_image)

    def test_size(self):
        expected_size = self.t3_node
        size = self.node_manager.size
        self.driver.list_sizes.assert_called()
        self.assertEqual(size, expected_size)
