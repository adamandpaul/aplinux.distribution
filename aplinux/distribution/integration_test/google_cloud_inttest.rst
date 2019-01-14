============================================
Using aplinux.distribution with Google Cloud
============================================

Get our cloud driver::

    >>> from libcloud.compute.providers import get_driver
    >>> from libcloud.compute.types import Provider
    >>> import os
    >>> ComputeEngine = get_driver(Provider.GCE)
    >>> driver = ComputeEngine(os.environ['APLINUX_INTEGRATION_TEST_GCE_SERCIE_ACCOUNT_EMAIL'],
    ...                        os.environ['APLINUX_INTEGRATION_TEST_GCE_SERCIE_ACCOUNT_KEY_FILE'],
    ...                        datacenter='us-central1-a',
    ...                        project=os.environ['APLINUX_INTEGRATION_TEST_GCE_PROJECT_ID'])

Run tempory instance::

    >>> from aplinux.distribution.node_manager import TemporyGCENode
    >>> with TemporyGCENode(driver, image='centos-7-') as nm:
    ...     print(nm.fabric.run('echo hello', hide=True).stdout)
    hello
