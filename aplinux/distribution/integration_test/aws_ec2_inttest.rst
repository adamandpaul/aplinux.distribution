=======================================
Using aplinux.distribution with AWS EC2
=======================================

Get our cloud driver::

    >>> from libcloud.compute.providers import get_driver
    >>> from libcloud.compute.types import Provider
    >>> import os
    >>> cls = get_driver(Provider.EC2)
    >>> driver = cls(os.environ['APLINUX_INTEGRATION_TEST_AWS_ACCESS_ID'],
    ...              os.environ['APLINUX_INTEGRATION_TEST_AWS_SECRET_KEY'],
    ...              region='us-east-1')

Set up the security group names, e.g. to allow SSH access on port 22::

    # Pipe a.k.a. '|' separated list of security group names, remember
    # to use bash "" which will allow spaces and other valid characters,
    # e.g. export APLINUX_INTEGRATION_TEST_AWS_SECURITY_GROUP_NAMES="test group|test group2"
    >>> security_group_names = os.environ['APLINUX_INTEGRATION_TEST_AWS_SECURITY_GROUP_NAMES']

Fetch latest CentOS 7 by product code as per `CentOS AWS wiki <https://wiki.centos.org/Cloud/AWS>`_:

    >>> images = driver.list_images(ex_filters={'product-code': 'aw0evgkw8e5c1q413zgy5pjce'})
    >>> images_by_description_release = sorted(images, key=lambda _: _.extra['description'].split(' ')[-1])
    >>> image = images_by_description_release[-1]

Run temporary instance::

    >>> from aplinux.distribution.node_manager import TemporyEC2Node
    >>> size = 't3.micro'
    >>> user = 'centos'

    >>> with TemporyEC2Node(driver, image=image, size=size, security_group_names=security_group_names, user=user) as nm:
    ...     print(nm.fabric.run('echo hello', hide=True).stdout)
    hello
