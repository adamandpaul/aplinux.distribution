# -*- coding: utf-8 -*-
"""An integration  between libcloud and fabric 2 taking advantage of python context managers

Creating a tempory instance such as::

    >>> with TemporyNodeManager(driver,
                         image=image,
                         size=image) as node_manager:
    >>>     node_manager.fabric.run('echo hello')

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

    def start(self):
        """Starts the tempory node. Return once the node is considered running"""
        self.node = self.driver.create_node(**self.node_kwargs)
        self.driver.wait_until_running(self.node)
