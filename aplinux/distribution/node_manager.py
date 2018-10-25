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
from libcloud.compute.types import NodeState

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

    def __init__(self, driver, user, key_pair, name_prefix=None, **kwargs):
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
        self.key_pair = key_pair
        self.name_prefix = name_prefix or self.name_prefix
        self.node_kwargs = kwargs
        self.node = None

    def create(self):
        """Starts the tempory node. Return once the node is considered running"""
        name_suffix = str(uuid.uuid4())
        self.name = f'{self.name_prefix}{name_suffix}'
        self.node = self.driver.create_node(name=self.name, **self.node_kwargs)
        self.driver.wait_until_running([self.node])

    def refresh_node(self):
        """Refresh the node from the node's driver"""
        node_id = self.node.id
        for node in self.node.driver.list_nodes():
            if node.id == node_id:
                self.node = node
                return

    def destroy(self):
        """Destroy the node, waiting for it to be terminated"""
        self.node.destroy()
        for i in range(60):
            time.sleep(5)
            self.refresh_node()
            if self.node.state == NodeState.TERMINATED:
                return
        raise Exception('Node failed to terminate')

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
                self.delete()
            except Exception as e:
                raise NodeManagerCleanupError('An exception was raied during node deletion. Node left in unkonwn state') from e