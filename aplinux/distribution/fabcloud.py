# -*- coding: utf-8 -*-
"""An integration  between libcloud and fabric 2 taking advantage of python context managers

Creating a tempory instance such as::

    >>> with TemporyNode(driver,
                         image=image,
                         size=image) as node:
    >>>     node.fabric.run('echo hello')

"""


class TemporyNode(object):
    """A tempory instance context object which is destroyed when the context exits
    """
