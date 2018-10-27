# -*- coding: utf-8 -*-
"""An integration  between libcloud and fabric 2 taking advantage of python context managers

Creating a tempory instance such as::

    >>> with TemporyNodeManager(driver,
                                key_pair,
                                image=image,
                                size=image) as node_manager:
    >>>     node_manager.fabric.run('echo hello')

"""

from io import StringIO
from libcloud.compute.base import KeyPair
from libcloud.compute.types import LibcloudError
from libcloud.compute.types import NodeState
from paramiko.rsakey import RSAKey

import fabric
import paramiko
import time
import uuid


class NodeManagerError(Exception):
    """A node manager generated error"""


class NodeManagerCleanupError(NodeManagerError):
    """A failure in the cleanup of a node occured"""


class TemporyNode(object):
    """A tempory node instance context object which is destroyed when the context exits

    Attributes:
        driver: A libcloud cloud driver
        user: The user to connect with
        key_pair: The libcloud key pair to use
        name_prefix: The node name prefix that is used for prefixing instance names
        node_kwargs: The kwargs passed to the create_node method
        node: The libcloud node or None if it hasn't been created
    """

    name_prefix = 'tempory-node-'

    def __init__(self, driver, user, key_pair=None, name_prefix=None, **kwargs):
        """Initialize the tempory node manager.

        Instances are later created with the create() method. They are given the name name_prefix
        plus a generated uuid.

        Args:
            driver: The libcloud driver to use
            user: The user used to create ssh connections with fabric
            key_pair: The libcloud key_pair used for fabric connections
            name_prefix: The desired name prefix for instances.
            **kwargs: The extra arguments passed to driver.create_node()
        """
        self.driver = driver
        self.user = user
        self._key_pair = key_pair
        self.name_prefix = name_prefix or self.name_prefix
        self.node_kwargs = kwargs
        self.node = None

    @property
    def key_pair(self):
        """key pair object used for authentication. If None, then a akey_pair can be generated"""
        if self._key_pair is None:

            # generate a key
            key = RSAKey.generate(2048)
            fingerprint = key.get_fingerprint()

            # construct the public key
            public_key_base64 = key.get_base64()
            public_key = f'ssh-rsa {public_key_base64} {self.user}'

            # construct the private key
            private_key_fout = StringIO()
            key.write_private_key(private_key_fout)
            private_key = private_key_fout.getvalue()

            self._key_pair = KeyPair('centos',
                                     public_key=public_key,
                                     fingerprint=fingerprint,
                                     driver=self.driver,
                                     private_key=private_key)

        return self._key_pair

    def create(self):
        """Starts the tempory node. Return once the node is considered running"""
        name_suffix = str(uuid.uuid4())
        self.name = f'{self.name_prefix}{name_suffix}'
        self.node = self.driver.create_node(name=self.name, **self.node_kwargs)
        self.driver.wait_until_running([self.node])

    def refresh_node(self):
        """Refresh the node from the node's driver"""
        if self.node is not None:
            node_id = self.node.id
            for node in self.node.driver.list_nodes():
                if node.id == node_id:
                    self.node = node
                    return
            self.node = None

    def destroy(self):
        """Destroy the node, waiting for it to be terminated"""

        # Atempt a destroy
        destroy_error = None
        try:
            self.node.destroy()
        except LibcloudError as err:
            destroy_error = err

        # Check that the node has gorne - sometimes the operation is successful with a timeout error
        for i in range(60):
            self.refresh_node()
            if self.node is None:
                return
            if self.node.state == NodeState.TERMINATED:
                return
            time.sleep(3)

        # if we have a destroy error then raise from that error
        if destroy_error is not None:
            raise NodeManagerError('Node failed to terminate') from destroy_error
        else:
            raise NodeManagerError('Node failed to terminate')

    _ip_address = None

    @property
    def ip_address(self):
        """Return a best guess ip_address"""
        if self._ip_address is None and self.node is not None:
            ip_addresses = self.node.public_ips + self.node.private_ips
            if len(ip_addresses) > 0:
                self._ip_address = ip_addresses[0]
        return self._ip_address

    @ip_address.setter
    def ip_address(self, value):
        """Allow for users to set the IP address specificly"""
        self._ip_address = value

    _fabric = None

    @property
    def fabric(self):
        """Return a fabric connection object"""
        if self._fabric is None and self.ip_address is not None:
            fin_private_key = StringIO(self.key_pair.private_key)
            pkey = paramiko.RSAKey.from_private_key(fin_private_key)
            self._fabric = fabric.Connection(self.ip_address,
                                             user=self.user,
                                             connect_kwargs={'pkey': pkey, 'look_for_keys': False})
        return self._fabric

    def __enter__(self):
        """Enter python context"""
        self.create()
        return self

    def __exit__(self, exc_type, ex_value, ex_tb):
        """Exit context manager"""
        if self.node is not None:
            try:
                self.destroy()
            except Exception as e:
                raise NodeManagerCleanupError('An exception was raied during node deletion. Node left in unkonwn state') from e


class TemporyGCENode(TemporyNode):
    """A Google Cloud Tempory Node"""

    def __init__(self, driver, user, image_name, node_size, **kwargs):
        """Create a tempory node manager for a gce node"""

        image = driver.ex_get_image('centos-7-')

        key = RSAKey.generate(2048)
        public_key = 'ssh-rsa {} centos'.format(key.get_base64())
        google_public_key = 'centos:ssh-rsa {} centos'.format(key.get_base64())
        private_key_fout = StringIO()
        key.write_private_key(private_key_fout)
        private_key = private_key_fout.getvalue()
        key_pair = KeyPair('centos',
                           public_key=public_key,
                           fingerprint=key.get_fingerprint(),
                           driver=driver,
                           private_key=private_key)
        node_size = driver.list_sizes()[0]
        ex_metadata = {
            'items': [{'key': 'ssh-keys',
                       'value': google_public_key }],
        }

        super().__init__(driver, user, key_pair, image=image, size=node_size, ex_metadata=ex_metadata)
