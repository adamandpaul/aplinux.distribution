# -*- coding:utf-8 -*-

from . import fabcloud
from unittest import TestCase


class TestTemporyNode(TestCase):

    def test_init(self):
        fabcloud.TemporyNode()
