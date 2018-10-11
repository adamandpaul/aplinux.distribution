# -*- coding: utf-8 -*-
"""An integration  between libcloud and fabric 2 taking advantage of python context managers

Creating a tempory instance such as::

    >>> with TemporyNodeManager(driver,
                         image=image,
                         size=image) as node:
    >>>     node.fabric.run('echo hello')

"""


class TemporyNodeManager(object):
    """A tempory instance context object which is destroyed when the context exits

    Attributes:
        driver: A libcloud cloud driver
        node_kwargs: The kwargs passed to the create_node method
        node: The libcloud node or None if it hasn't been created
    """

    def __init__(self, driver, **kwargs):
        """Initialize the tempory node"""
        self.driver = driver
        self.node_kwargs = kwargs
        self.node = None
