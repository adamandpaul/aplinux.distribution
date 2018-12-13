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
import logging
import paramiko
import time
import uuid


logger = logging.getLogger('aplinux.distribution')


class NodeManagerError(Exception):
    """A node manager generated error"""


class NodeManagerCleanupError(NodeManagerError):
    """A failure in the cleanup of a node occured"""


class TemporyNode(object):
    """A tempory node instance context object which is destroyed when the context exits

    Attributes:
        driver: A libcloud cloud driver
        name_prefix: The node name prefix that is used for prefixing instance names
        user: The user to connect with
        create_kwargs: The kwargs passed to the create_node method
        node: The libcloud node or None if it hasn't been created
    """

    _name = None

    @property
    def name(self):
        """Create a name for the node"""
        if self._name is None:
            name_suffix = str(uuid.uuid4())
            self._name = f'{self.name_prefix}{name_suffix}'
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    _size = None

    @property
    def size(self):
        """the libcloud size value"""
        if self._size is None:
            sizes = self.driver.list_sizes()
            if len(sizes) > 0:
                self._size = sizes[0]
        return self._size

    @size.setter
    def size(self, value):
        self._size = value

    _image = None

    @property
    def image(self):
        """the libcloud image value"""
        return self._image

    @image.setter
    def image(self, value):
        self._image = value

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

            self._key_pair = KeyPair(f'key-pair-{self.name}',
                                     public_key=public_key,
                                     fingerprint=fingerprint,
                                     driver=self.driver,
                                     private_key=private_key)

        return self._key_pair

    @key_pair.setter
    def key_pair(self, value):
        self._key_pair = value

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

    def __init__(self, driver, name_prefix=None, size=None, image=None, user='admin', key_pair=None, **kwargs):
        """Initialize the tempory node manager.

        Instances are later created with the create() method. They are given the name name_prefix
        plus a generated uuid.

        Args:
            driver: The libcloud driver to use
            name_prefix: The desired name prefix for instances.
            size: The desired size. If None then the first from list_sizes is uesed
            user: The user used to create ssh connections with fabric
            key_pair: The libcloud key_pair used for fabric connections. Auto generated if None
            **kwargs: The extra arguments passed to driver.create_node()
        """
        # set attributes
        self.driver = driver
        self.name_prefix = name_prefix or 'tempory-node-'
        self.user = user
        self.create_kwargs = kwargs
        self.node = None

        # set properties
        self.size = size
        self.image = image
        self.key_pair = key_pair

    def create(self):
        """Starts the tempory node. Return once the node is considered running"""
        logger.info(f'Creating tempory {self.size} node from {self.image}: {self.name}')
        self.node = self.driver.create_node(name=self.name,
                                            size=self.size,
                                            image=self.image,
                                            **self.create_kwargs)
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
        if self.node is None:
            logger.info(f'No tempory node to destroy')
            return

        logger.info(f'Destroying tempory node: {self.name}')

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

    def __enter__(self):
        """Enter python context"""
        self.create()
        return self

    def __exit__(self, exc_type, ex_value, ex_tb):
        """Exit context manager"""
        try:
            self.destroy()
        except Exception as e:
            raise NodeManagerCleanupError('An exception was raied during node deletion. Node left in unkonwn state') from e


class TemporyGCENode(TemporyNode):
    """A Google Cloud Tempory Node"""

    @TemporyNode.image.getter
    def image(self):
        """if image has been a string then fetch the image from ex_get_image"""
        super_image = super().image
        if isinstance(super_image, str):
            driver_image = self.driver.ex_get_image(super_image)
            self.image = driver_image
        return super().image

    def __init__(self, *args, **kwargs):
        """Create a tempory node manager for a gce node"""
        super().__init__(*args, **kwargs)
        meta = self.create_kwargs.setdefault('ex_metadata', {})
        items = meta.setdefault('items', [])
        items.append({'key': 'ssh-keys',
                      'value': f'{self.user}:{self.key_pair.public_key}'})
