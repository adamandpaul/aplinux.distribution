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
from retry import retry

import fabric
import logging
import paramiko
import time
import uuid


logger = logging.getLogger('aplinux.distribution')


class NodeManagerError(Exception):
    """A node manager generated error"""


class NodeManagerErrorNoNode(NodeManagerError):
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

    def _get_node_by_name(self, name):
        """Utility method used for testing if a node already exists or for refreshing the current node"""
        for node in self.driver.list_nodes():
            if node.name == name:
                return node
        return None

    def create(self):
        """Starts the tempory node. Return once the node is considered running"""
        assert self.name is not None and self.name.strip() != '', 'name must not be None or blank string'
        assert self._get_node_by_name(self.name) is None, f'Node with the name {self.name} already exists'
        logger.info(f'Creating tempory {self.size} node from {self.image}: {self.name}')
        self.node = self.driver.create_node(name=self.name,
                                            size=self.size,
                                            image=self.image,
                                            **self.create_kwargs)
        self.driver.wait_until_running([self.node])

    def refresh_node(self):
        """Refresh the node from the node's driver"""
        self.node = self._get_node_by_name(self.name)

    def destroy(self):
        """Destroy the node, waiting for it to be terminated"""
        logger.info(f'Destroying tempory node: {self.name}')

        if self.node is None:
            self.refresh_node()

        if self.node is None:
            raise NodeManagerErrorNoNode('No node to destroy')

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
        try:
            self.create()
        except Exception as e:
            # sleep for a bit incase the destroy api is eventually consistant
            time.sleep(3)
            try:
                self.destroy()
            except NodeManagerErrorNoNode:
                pass
            raise e
        return self

    def __exit__(self, exc_type, ex_value, ex_tb):
        """Exit context manager"""
        try:
            self.destroy()
        except Exception as e:
            raise NodeManagerCleanupError('An exception was raied during node deletion. Node left in unkonwn state') from e

    def wait_untill_ready(self, tries=10, delay=0.5, backoff=1.5):
        """Wait untill the node is able to accept fabric run commands

        Args:
            timeout (int): The number of seconds to wait until raising an exception
            interval (int): The number of seconds between retry
        """
        @retry(tries=tries, delay=delay, backoff=backoff)
        def test_connect():
            self.fabric.run('echo "hello"')
        test_connect()


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


class TemporyEC2Node(TemporyNode):
    """An Amazon Web Services Elastic Compute Cloud (EC2) temporary node"""

    # Use pipe delimiter ASCII code 124,
    # as it's not a valid security group character
    # https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html
    EX_SECURITY_GROUP_DELIMITER = '|'

    def __init__(self, *args, **kwargs):
        """Create a temporary node manager for an AWS EC2 node"""
        kwargs.setdefault('ex_blockdevicemappings', [
            {
                'DeviceName': '/dev/sda1',
                'Ebs': {'DeleteOnTermination': True},
            },
        ])
        security_group_names = kwargs.get('security_group_names', '')
        if security_group_names:
            kwargs['ex_security_groups'] = security_group_names.split(
                self.EX_SECURITY_GROUP_DELIMITER)
        super().__init__(*args, **kwargs)
        self.create_kwargs.setdefault('ex_keyname', self.key_pair.name)

    def create(self):
        """Also add a key pair to access the EC2 instance"""
        logger.info(f'Importing temporary key pair: {self.key_pair.name}')
        self.driver.import_key_pair_from_string(
            self.key_pair.name,
            self.key_pair.public_key,
        )
        super().create()

        # About 50% of the time, got a paramiko.ssh_exception.NoValidConnectionsError:
        # [Errno None] Unable to connect to port 22 on 3.80.6.237
        time.sleep(3)

        # The public IP address does not show up when the node is first fetched
        logger.info('Refreshing node')
        self.refresh_node()

    def destroy(self):
        """Also clean up the key pair if it has been created"""
        super().destroy()
        if self._key_pair:
            logger.info(f'Deleting temporary key pair: {self.key_pair.name}')
            self.driver.delete_key_pair(self.key_pair)

    @TemporyNode.image.getter
    def image(self):
        """if image is a string then fetch the image from get_image"""
        super_image = super().image
        if isinstance(super_image, str):
            driver_image = self.driver.get_image(super_image)
            self.image = driver_image
        return super().image

    @TemporyNode.size.getter
    def size(self):
        """If size is a string then fetch the size from the
        driver-provided list of sizes"""
        super_size = super().size
        if isinstance(super_size, str):
            driver_sizes = self.driver.list_sizes()
            filtered_sizes = [_ for _ in driver_sizes if _.id == super_size]
            if filtered_sizes:
                self.size = filtered_sizes[0]
        return super().size
