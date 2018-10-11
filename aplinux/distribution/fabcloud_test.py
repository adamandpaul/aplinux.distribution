# -*- coding:utf-8 -*-

from . import fabcloud
from unittest import TestCase
from unittest.mock import MagicMock


class TestTemporyNode(TestCase):

    def test_init(self):
        driver = MagicMock()
        node = fabcloud.TemporyNode(driver)
        self.assertEqual(node.driver, driver)
