============================================
Using aplinux.distribution with Google Cloud
============================================

Setup imports::

    >>> import os
    >>> from libcloud.compute.types import Provider
    >>> from libcloud.compute.providers import get_driver
    >>> from libcloud.compute.base import KeyPair
    >>> from paramiko.rsakey import RSAKey
    >>> from io import StringIO
    >>> from aplinux.distribution.fabcloud import TemporyNodeManager

Get our cloud driver::

    >>> ComputeEngine = get_driver(Provider.GCE)
    >>> driver = ComputeEngine(os.environ['APLINUX_INTEGRATION_TEST_GCE_SERCIE_ACCOUNT_EMAIL'],
    ...                        os.environ['APLINUX_INTEGRATION_TEST_GCE_SERCIE_ACCOUNT_KEY_FILE'],
    ...                        datacenter='us-central1-a',
    ...                        project=os.environ['APLINUX_INTEGRATION_TEST_GCE_PROJECT_ID'])

Get the image::

    >>> image = driver.ex_get_image('centos-7-')

Generate the ssh key::

    >>> key = RSAKey.generate(2048)
    >>> public_key = 'ssh-rsa {} centos'.format(key.get_base64())
    >>> google_public_key = 'centos:ssh-rsa {} centos'.format(key.get_base64())
    >>> private_key_fout = StringIO()
    >>> key.write_private_key(private_key_fout)
    >>> private_key = private_key_fout.getvalue()
    >>> key_pair = KeyPair('centos',
    ...                    public_key=public_key,
    ...                    fingerprint=key.get_fingerprint(),
    ...                    driver=driver,
    ...                    private_key=private_key)

Get the node size::

    >>> node_size = driver.list_sizes()[0]

Define the node meta data (in GCE the ssh-key goes here)::

    >>> ex_metadata = {
    ...     'items': [{'key': 'ssh-keys',
    ...                'value': google_public_key }],
    ... }

Run tempory instance::

    >>> with TemporyNodeManager(driver, 'centos', key_pair, image=image, size=node_size, ex_metadata=ex_metadata) as nm:
    ...     nm.fabric.run('echo hello')
    hello
